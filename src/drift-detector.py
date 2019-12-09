import json
import boto3
import sys
import time

MAX_ATTEMPTS=10
ATTEMPT_WAIT_TIME=1

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
            stacks.append(stack)

    return stacks


def detect_drift(cfclient, stacks):
    stacks_with_drift = []
    stacks_checking_ids = []

    for stack in stacks:
        if not is_status_proper_to_check_drift(stack['StackStatus']):
            continue

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
                stacks_with_drift.append(response)
                break
            elif response['DetectionStatus'] == 'DETECTION_FAILED':
                print('Detection failed')
                break

            if attempts < MAX_ATTEMPTS:
                attempts += 1
                sleep = min(int((2^attempts)*0.1)+1, 15)
                print(sleep)
                time.sleep(sleep)
            else:
                print('Max attempts exceeded')
                sys.exit(1)

    return stacks_with_drift


def lambda_handler(event, context):
    cfclient = boto3.client('cloudformation')

    print(detect_drift(cfclient, find_stacks(cfclient)))

    return {
        "statusCode": 200,
        "body": '',
    }
