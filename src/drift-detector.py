import json
import boto3
import requests
import urllib.parse
import sys
import time
import os

MAX_ATTEMPTS = 100
ATTEMPT_WAIT_TIME = 6


def get_emoji_for_status(status):
    if(status == 'DELETED'):
        return ':x:'
    elif(status == 'MODIFIED'):
        return ':pencil:'
    elif(status == 'IN_SYNC'):
        return ':check:'

    return ''


def get_stack_url(stack_id):
    return 'https://console.aws.amazon.com/'\
           +'cloudformation/home#/stacks/drifts?stackId='\
           +urllib.parse.quote(stack_id)


def is_status_proper_to_check_drift(status):
    return status in (
        'CREATE_COMPLETE',
        'UPDATE_COMPLETE',
        'UPDATE_ROLLBACK_COMPLETE'
    )


def find_stacks(cfclient):
    stacks = []

    paginator = cfclient.get_paginator('describe_stacks')

    response_iterator = paginator.paginate()
    for page in response_iterator:
        for stack in page['Stacks']:
            if is_status_proper_to_check_drift(stack['StackStatus']):
                stacks.append(stack)

    return stacks


def detect_drift(cfclient, stacks):
    stacks_with_drift = []
    stacks_checking_ids = []

    for stack in stacks:
        stacks_checking_ids.append(cfclient.detect_stack_drift(
            StackName=stack['StackName']
        )['StackDriftDetectionId'])

    attempts = 0

    for stack_id in stacks_checking_ids:
        while True:
            response = cfclient.describe_stack_drift_detection_status(
                StackDriftDetectionId=stack_id
            )

            if response['DetectionStatus'] == 'DETECTION_COMPLETE':
                break
            elif response['DetectionStatus'] == 'DETECTION_FAILED':
                print('Detection failed')
                print(response)
                break

            if attempts < MAX_ATTEMPTS:
                attempts += 1
                sleep = ATTEMPT_WAIT_TIME
                time.sleep(sleep)
            else:
                print('Max attempts exceeded')
                sys.exit(1)

    for stack in stacks:
        response = cfclient.describe_stack_resource_drifts(
            StackName=stack['StackName']
        )
        stack['drift'] = []
        stack['no_of_drifted_resources'] = 0
        stack['no_of_resources'] = len(response['StackResourceDrifts'])

        for drift in response['StackResourceDrifts']:
            if drift['StackResourceDriftStatus'] in ('DELETED', 'MODIFIED'):
                stack['no_of_drifted_resources'] += 1

            stack['drift'].append({
                'PhysicalResourceId': drift['PhysicalResourceId'],
                'StackResourceDriftStatus': drift['StackResourceDriftStatus'],
                'ResourceType': drift['ResourceType']
            })

        print(stack['drift'])

        stacks_with_drift.append(stack)

    return stacks_with_drift


def post_to_slack(stacks):
    url = os.environ['SLACK_WEBHOOK']

    headers = {
        "Content-Type": "application/json"
    }

    blocks = []

    for stack in stacks:
        if stack['no_of_drifted_resources'] == 0:
            continue

        stack_url = get_stack_url(stack['StackId'])
        stack_name = stack['StackName']
        if stack['no_of_resources'] == 0:
            percentage = "0"
        else:
            percentage = str(round(
                stack['no_of_drifted_resources']/stack['no_of_resources']*100, 0
            ))

        blocks.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':warning: *<' \
                        + stack_url + '|' + stack_name \
                        + '>* DRIFTED '
                        + str(stack['no_of_drifted_resources']) \
                        + '/' + str(stack['no_of_resources']) + ' resources'
            }
        })

        for drift in stack['drift']:
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': "\t"+drift['PhysicalResourceId']\
                            +"\t"+drift['ResourceType']\
                            +"\t"+drift['StackResourceDriftStatus']\
                            +"\t"+get_emoji_for_status(drift['StackResourceDriftStatus'])
                }
            })

    message = {
        'blocks': blocks
    }

    return requests.post(url, headers=headers, data=json.dumps(message))


def lambda_handler(event, context):
    cfclient = boto3.client('cloudformation')

    stacks = detect_drift(cfclient, find_stacks(cfclient))
    response = post_to_slack(stacks)

    return {
        "statusCode": 200,
        "body": '',
    }
