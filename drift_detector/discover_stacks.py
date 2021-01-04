import boto3
import os
import re
import json
from utils import chunks


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


def send_stacks_to_sqs(stacks_in_batches, sqs_client, sqs_url):
    for stacks in stacks_in_batches:
        json_stacks = json.dumps(stacks, indent=4, default=str, sort_keys=True)
        sqs_client.send_message(
            QueueUrl=sqs_url,
            MessageBody=json_stacks,
            MessageGroupId='drift_detector'
        )


def lambda_handler(event, context):
    try:
        cf_client = boto3.client('cloudformation')
        sqs_client = boto3.client('sqs')

        sqs_url = os.environ['DRIFT_DETECTION_QUEUE']
        batches = int(os.environ['STACK_BATCHES'])

        stacks_in_batches = chunks(find_stacks(cf_client), batches)
        send_stacks_to_sqs(stacks_in_batches, sqs_client, sqs_url)
    except Exception as e:
        print("Unexpected error: %s" % e)
        raise

    return {
            "statusCode": 200,
            "body": '',
        }