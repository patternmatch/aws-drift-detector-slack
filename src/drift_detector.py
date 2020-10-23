import json
import boto3
import requests
import urllib.parse
import sys
import time
import os
import re

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
    if status == 'DELETED':
        return ':x:'
    elif status == 'MODIFIED':
        return ':warning:'
    elif status == 'IN_SYNC':
        return ':heavy_check_mark:'

    return ''


def get_stack_url(stack_id):
    return f'https://console.aws.amazon.com/cloudformation/home#/stacks/drifts?stackId={urllib.parse.quote(stack_id)}'


def is_status_proper_to_check_drift(status):
    return status in (
        'CREATE_COMPLETE',
        'UPDATE_COMPLETE',
        'UPDATE_ROLLBACK_COMPLETE'
    )


def find_stacks(cf_client):
    stacks = []

    stack_regex = re.compile(os.environ.get('STACK_REGEX', '.*'))

    paginator = cf_client.get_paginator('describe_stacks')

    response_iterator = paginator.paginate()
    for page in response_iterator:
        for stack in page['Stacks']:
            if is_status_proper_to_check_drift(stack['StackStatus']) \
                    and stack_regex.match(stack['StackName']):
                stacks.append(stack)

    return stacks


def detect_drift(cf_client, stacks):
    stacks_checking_ids = []

    for stack in stacks:
        stacks_checking_ids.append(cf_client.detect_stack_drift(
            StackName=stack['StackName']
        )['StackDriftDetectionId'])

    detection_failed_stacks_ids = check_drifts_detection_status(cf_client, stacks_checking_ids)
    detection_complete_stacks = list(filter(lambda s: s['StackId'] not in detection_failed_stacks_ids, stacks))
    detection_failed_stacks = list(filter(lambda s: s['StackId'] in detection_failed_stacks_ids, stacks))

    return append_drift_info(cf_client, detection_complete_stacks), detection_failed_stacks


def append_drift_info(cf_client, detection_complete_stacks):
    stacks_with_drift_info = []

    for stack in detection_complete_stacks:
        response = cf_client.describe_stack_resource_drifts(
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

        stacks_with_drift_info.append(stack)

    return stacks_with_drift_info


def check_drifts_detection_status(cf_client, stacks_checking_ids):
    detection_failed_stack_ids = []
    attempts = 0

    for detection_id in stacks_checking_ids:
        while True:
            response = cf_client.describe_stack_drift_detection_status(
                StackDriftDetectionId=detection_id
            )

            if response['DetectionStatus'] == 'DETECTION_COMPLETE':
                break
            elif response['DetectionStatus'] == 'DETECTION_FAILED':
                stack_id = response['StackId']
                fail_reason = response['DetectionStatusReason']
                print(f'Drift detection has failed for the Stack with ID: {stack_id} with reason: {fail_reason}')
                detection_failed_stack_ids.append(stack_id)
                break

            if attempts < MAX_ATTEMPTS:
                attempts += 1
                sleep = ATTEMPT_WAIT_TIME
                time.sleep(sleep)
            else:
                print('Max attempts exceeded')
                sys.exit(1)

    return detection_failed_stack_ids


def build_slack_message(stack):
    stack_url = get_stack_url(stack['StackId'])
    stack_name = stack['StackName']

    show_in_sync_resources = os.environ.get('SHOW_IN_SYNC', 'false')

    if stack['no_of_drifted_resources'] > 0:
        blocks = create_drifted_stack_message_blocks(show_in_sync_resources, stack, stack_name, stack_url)

    else:
        blocks = create_not_drifted_stack_message_blocks(stack_name, stack_url)

    return {
        'blocks': blocks
    }


def create_not_drifted_stack_message_blocks(stack_name, stack_url):
    return [{
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': ':heavy_check_mark: No drift detected at *<'
                    + stack_url + '|' + stack_name
                    + '>*'
        }
    }]


def create_drifted_stack_message_blocks(show_in_sync_resources, stack, stack_name, stack_url):
    blocks = [{
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': ':warning: Drift detected at *<'
                    + stack_url + '|' + stack_name
                    + '>*'
        }
    }, {
        'type': 'divider',
    }]

    for drift in stack['drift']:
        if show_in_sync_resources == "false" and drift['StackResourceDriftStatus'] == 'IN_SYNC':
            continue

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ">" + get_emoji_for_status(drift['StackResourceDriftStatus'])
                        + " *" + drift['PhysicalResourceId'] + "*\n>:small_orange_diamond: _"
                        + drift['ResourceType'] + "_"
            },
        })
    blocks.append({
        'type': 'divider',
    })

    return blocks


def build_detection_failed_slack_message(detection_failed_stack):
    stack_url = get_stack_url(detection_failed_stack['StackId'])
    stack_name = detection_failed_stack['StackName']

    return {'blocks': [{
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': ':question: Detection failed at *<'
                    + stack_url + '|' + stack_name
                    + '>*'
        }
    }]}


def post_to_slack(stacks, detection_failed_stacks):
    url = os.environ['SLACK_WEBHOOK']

    headers = {
        "Content-Type": "application/json"
    }

    for detection_failed_stack in detection_failed_stacks:
        message = build_detection_failed_slack_message(detection_failed_stack)
        requests.post(url, headers=headers, data=json.dumps(message))

    for stack in stacks:
        message = build_slack_message(stack)
        requests.post(url, headers=headers, data=json.dumps(message))


def lambda_handler(event, context):
    cf_client = boto3.client('cloudformation')

    stacks, detection_failed_stacks = detect_drift(cf_client, find_stacks(cf_client))
    post_to_slack(stacks, detection_failed_stacks)

    return {
        "statusCode": 200,
        "body": '',
    }
