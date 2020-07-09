import json
import boto3
import requests
import urllib.parse
import sys
import time
import os

MAX_ATTEMPTS = 100
ATTEMPT_WAIT_TIME = 6


def is_arn(physical_resource_id):
    return physical_resource_id.startswith('arn:aws:')


def parse_arn(arn):
    # Function borrowed from: https://gist.github.com/gene1wood/5299969edc4ef21d8efcfea52158dd40

    # If given string is not an arn, simply return it.
    if is_arn(arn) is False:
        return arn

    # http://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    elements = arn.split(':', 5)
    result = {
        'arn': elements[0],
        'partition': elements[1],
        'service': elements[2],
        'region': elements[3],
        'account': elements[4],
        'resource': elements[5],
        'resource_type': None
    }
    if '/' in result['resource']:
        result['resource_type'], result['resource'] = result['resource'].split('/', 1)
    elif ':' in result['resource']:
        result['resource_type'], result['resource'] = result['resource'].split(':', 1)

    return result['resource']


def get_emoji_for_status(status):
    if(status == 'DELETED'):
        return ':x:'
    elif(status == 'MODIFIED'):
        return ':warning:'
    elif(status == 'IN_SYNC'):
        return ':heavy_check_mark:'

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
                'PhysicalResourceId': parse_arn(drift['PhysicalResourceId']),
                'StackResourceDriftStatus': drift['StackResourceDriftStatus'],
                'ResourceType': drift['ResourceType']
            })

        stack['drift'].sort(key=lambda x: x['PhysicalResourceId'])

        stacks_with_drift.append(stack)

    return stacks_with_drift


def build_slack_message(stack):
    blocks = []

    stack_url = get_stack_url(stack['StackId'])
    stack_name = stack['StackName']

    show_in_sync_resources = os.environ.get('SHOW_IN_SYNC', 'false')

    if stack['no_of_drifted_resources'] > 0:
        blocks.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':warning: Drift detected at *<' \
                        + stack_url + '|' + stack_name \
                        + '>*'
            }
        })

        blocks.append({
            'type': 'divider',
        })

        for drift in stack['drift']:
            if show_in_sync_resources == "false" and drift['StackResourceDriftStatus'] == 'IN_SYNC':
                continue

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ">" + get_emoji_for_status(drift['StackResourceDriftStatus'])\
                        + " *" + drift['PhysicalResourceId'] + "*\n>:small_orange_diamond: _"\
                        + drift['ResourceType'] + "_"
                },
            })

        blocks.append({
            'type': 'divider',
        })

    else:
        blocks.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': ':heavy_check_mark: No drift detected at *<' \
                        + stack_url + '|' + stack_name \
                        + '>*'
            }
        })

    return {
        'blocks': blocks
    }


def post_to_slack(stacks):
    url = os.environ['SLACK_WEBHOOK']

    headers = {
        "Content-Type": "application/json"
    }

    for stack in stacks:
        message = build_slack_message(stack)

        print(json.dumps(message))

        response = requests.post(url, headers=headers, data=json.dumps(message))

        print(response)
        print(response.content)


def lambda_handler(event, context):
    cfclient = boto3.client('cloudformation')

    stacks = detect_drift(cfclient, find_stacks(cfclient))
    post_to_slack(stacks)

    return {
        "statusCode": 200,
        "body": '',
    }
