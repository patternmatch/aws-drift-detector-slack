import unittest
import os
import sys

sys.path.insert(0, './drift_detector')

from drift_detector.discover_stacks import send_stacks_to_sqs
from unittest.mock import MagicMock


class MockSQSClient: pass


class MockCFClient: pass


class MockPaginator: pass


mock_sqs_client = MockSQSClient()
mock_cf_client = MockCFClient()
mock_paginator = MockPaginator()

stacks_in_batches = [
  {
    'StackName': 'aws-sam-cli-managed-default',
    'StackStatus': 'CREATE_COMPLETE',
  },
  {
    'StackName': 'hello-world-stack',
    'StackStatus': 'CREATE_COMPLETE',
  },
  {
    'StackName': 'hello-world-stack2',
    'StackStatus': 'CREATE_COMPLETE',
  },
  {
    'StackName': 'hello-world-stack3',
    'StackStatus': 'CREATE_COMPLETE',
  },
  {
    'StackName': 'hello-world-stack4',
    'StackStatus': 'CREATE_COMPLETE',
  },
  {
    'StackName': 'hello-world-stack5',
    'StackStatus': 'CREATE_COMPLETE',
  }
]


class TestSendStacks(unittest.TestCase):
    def setUp(self):
        mock_cf_client.detect_stack_drift = MagicMock(return_value={
          'StackDriftDetectionId': 42
        })
        mock_cf_client.describe_stack_drift_detection_status = MagicMock(return_value={
          'StackId': 'stack_id',
          'DetectionStatus': 'DETECTION_COMPLETE'
        })
        mock_cf_client.describe_stack_resource_drifts = MagicMock(return_value={
          'StackResourceDrifts': [
            {
              'StackResourceDriftStatus': 'MODIFIED',
              'PhysicalResourceId': 'physical_resource_id',
              'ResourceType': 'resource_type'
            }
          ]
        })
        mock_paginator.paginate = MagicMock(return_value=[
          {
            'Stacks': [
              {
                'StackName': 'aws-sam-cli-managed-default',
                'StackStatus': 'CREATE_COMPLETE',
              },
              {
                'StackName': 'hello-world-stack',
                'StackStatus': 'CREATE_COMPLETE',
              }
            ]
          }
        ])
        mock_cf_client.get_paginator = MagicMock(return_value=mock_paginator)
        mock_sqs_client.send_message = MagicMock()

    def test_send_stacks(self):
        """
        Test that sends stacks to sqs
        """
        sqs_url = 'www.sqs-test.com'

        send_stacks_to_sqs(stacks_in_batches, mock_sqs_client, sqs_url)

        self.assertTrue(mock_sqs_client.send_message.called)


if __name__ == '__main__':
  unittest.main()