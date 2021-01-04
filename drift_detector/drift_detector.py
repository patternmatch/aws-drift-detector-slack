import boto3
import json
import urllib.parse
import sys
import time
import os
from utils import chunks

CHECK_STATUS_MAX_ATTEMPTS = 100
CHECK_STATUS_ATTEMPT_WAIT_TIME = 6
CF_CALLS_CHUNK_SIZE = 3
DRIFT_DETECTION_MAX_RETRIES = 5


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


def detect_drift(cf_client, stacks):
    stacks_to_check = json.loads(stacks)
    attempts = 0

    while stacks_to_check and attempts < DRIFT_DETECTION_MAX_RETRIES:
        attempts += 1
        split_into_chunks_stacks = chunks(stacks_to_check, CF_CALLS_CHUNK_SIZE)

        for chunk in split_into_chunks_stacks:
            stacks_checking_ids = []
            for stack in chunk:
                stacks_checking_ids.append(cf_client.detect_stack_drift(
                    StackName=stack['StackName']
                )['StackDriftDetectionId'])

            completed_stacks_ids = check_drifts_detection_status(cf_client, stacks_checking_ids)
            stacks_to_check = list(filter(lambda s: s['StackId'] not in completed_stacks_ids, stacks_to_check))

    detection_complete_stacks = list(filter(lambda s: s not in stacks_to_check, json.loads(stacks)))
    detection_failed_stacks = list(filter(lambda s: s in stacks_to_check, json.loads(stacks)))

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
    detection_complete_stack_ids = []
    attempts = 0

    for detection_id in stacks_checking_ids:
        while True:
            response = cf_client.describe_stack_drift_detection_status(
                StackDriftDetectionId=detection_id
            )

            if response['DetectionStatus'] == 'DETECTION_COMPLETE':
                detection_complete_stack_ids.append(response['StackId'])
                break
            elif response['DetectionStatus'] == 'DETECTION_FAILED':
                stack_id = response['StackId']
                fail_reason = response['DetectionStatusReason']
                print(f'Drift detection has failed for the Stack with ID: {stack_id} with reason: {fail_reason}')
                break

            if attempts < CHECK_STATUS_MAX_ATTEMPTS:
                attempts += 1
                sleep = CHECK_STATUS_ATTEMPT_WAIT_TIME
                time.sleep(sleep)
            else:
                print('Max attempts exceeded')
                sys.exit(1)

    return detection_complete_stack_ids


def invoke_slack_notification_lambda(stacks, detection_failed_stacks, lambda_client, function):
    lambda_payload = json.dumps({
      "stacks": stacks,
      "detection_failed_stacks": detection_failed_stacks
    })
    lambda_client.invoke(FunctionName=function,
                         InvocationType='Event',
                         Payload=lambda_payload)


def lambda_handler(event, context):
    try:
        cf_client = boto3.client('cloudformation')
        lambda_client = boto3.client('lambda')

        function = os.environ['SLACK_NOTIFICATION_FUNCTION']

        print("Drift detector lambda")

        for record in event['Records']:
            payload = record["body"]
            stacks, detection_failed_stacks = detect_drift(cf_client, payload)
            invoke_slack_notification_lambda(stacks, detection_failed_stacks, lambda_client, function)
    except Exception as e:
        print("Unexpected error: %s" % e)
        raise

    return {
        "statusCode": 200,
        "body": '',
    }