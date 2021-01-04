import unittest
import os
import sys

sys.path.insert(0, './drift_detector')

from drift_detector.drift_detector import invoke_slack_notification_lambda
from unittest.mock import MagicMock
from unittest.mock import patch


class MockLambdaClient: pass


class MockCFClient: pass


mock_lambda_client = MockLambdaClient()
mock_cf_client = MockCFClient()


class TestInvokeLambda(unittest.TestCase):
    def setUp(self):
        os.environ['SLACK_NOTIFICATION_FUNCTION'] = 'slack-notification-function'
        mock_lambda_client.invoke = MagicMock()

    @patch('drift_detector.drift_detector.detect_drift')
    def test_invoke_lambda(self, mock_detect_drift):
        """
        Test that invoke lambda
        """
        mock_stacks = [
          {
            'StackName': 'stack_name',
            'StackId': 'stack_id'
          }
        ]

        detection_failed_stacks = [
          {
            'StackName': 'stack_name1',
            'StackId': 'stack_id1'
          }
        ]

        payload = {
          "first": mock_stacks,
          "detection_failed_stacks": detection_failed_stacks
        }
        function = 'test_function'
        mock_detect_drift.return_value = payload

        invoke_slack_notification_lambda(mock_stacks, detection_failed_stacks, mock_lambda_client, function)

        self.assertTrue(mock_lambda_client.invoke.called)


if __name__ == '__main__':
  unittest.main()