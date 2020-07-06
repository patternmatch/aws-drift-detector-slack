import unittest

from unittest.mock import MagicMock
from src.drift_detector import detect_drift

class MockCFClient: pass

mock_cfclient = MockCFClient()


class TestDetectDrift(unittest.TestCase):
    def setUp(self):
        mock_cfclient.detect_stack_drift = MagicMock(return_value={
            'StackDriftDetectionId': 42
        })
        mock_cfclient.describe_stack_drift_detection_status = MagicMock(return_value={
            'DetectionStatus': 'DETECTION_COMPLETE'
        })
        mock_cfclient.describe_stack_resource_drifts = MagicMock(return_value={
            'StackResourceDrifts': [
                {
                    'StackResourceDriftStatus': 'MODIFIED',
                    'PhysicalResourceId': 'physical_resource_id',
                    'ResourceType': 'resource_type',
                },
            ],
        })


    def test_detect_drift(self):
        """
        Test that drift is correctly detected
        """
        mock_stacks = [
            {
                'StackName': 'stack_name'
            }
        ]

        self.assertEqual(detect_drift(mock_cfclient, mock_stacks), [
            {
                'StackName': 'stack_name',
                'drift': [
                    {
                        'PhysicalResourceId': 'physical_resource_id',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'MODIFIED',
                    },
                ],
                'no_of_drifted_resources': 1,
                'no_of_resources': 1,
            },
        ])


    def test_detect_drift_with_no_drift(self):
        """
        Test that no drift is correctly detected
        """
        mock_stacks = [
            {
                'StackName': 'stack_name'
            },
        ]

        mock_cfclient.describe_stack_resource_drifts = MagicMock(return_value={
            'StackResourceDrifts': [
                {
                    'StackResourceDriftStatus': 'IN_SYNC',
                    'PhysicalResourceId': 'physical_resource_id_one',
                    'ResourceType': 'resource_type',
                },
                {
                    'StackResourceDriftStatus': 'IN_SYNC',
                    'PhysicalResourceId': 'physical_resource_id_two',
                    'ResourceType': 'resource_type',
                },
            ],
        })

        self.assertEqual(detect_drift(mock_cfclient, mock_stacks), [
            {
                'StackName': 'stack_name',
                'drift': [
                    {
                        'PhysicalResourceId': 'physical_resource_id_one',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'IN_SYNC',
                    },
                    {
                        'PhysicalResourceId': 'physical_resource_id_two',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'IN_SYNC',
                    },
                ],
                'no_of_drifted_resources': 0,
                'no_of_resources': 2,
            },
        ])


    def test_detect_drift_sorting(self):
        """
        Test that drift is correctly detected and sorted
        """
        mock_stacks = [
            {
                'StackName': 'stack_name'
            },
        ]

        mock_cfclient.describe_stack_resource_drifts = MagicMock(return_value={
            'StackResourceDrifts': [
                {
                    'StackResourceDriftStatus': 'IN_SYNC',
                    'PhysicalResourceId': 'aaaaaaaa',
                    'ResourceType': 'resource_type',
                },
                {
                    'StackResourceDriftStatus': 'IN_SYNC',
                    'PhysicalResourceId': 'cccccccc',
                    'ResourceType': 'resource_type',
                },
                {
                    'StackResourceDriftStatus': 'IN_SYNC',
                    'PhysicalResourceId': 'bbbbbbbb',
                    'ResourceType': 'resource_type',
                },
            ],
        })

        self.assertEqual(detect_drift(mock_cfclient, mock_stacks), [
            {
                'StackName': 'stack_name',
                'drift': [
                    {
                        'PhysicalResourceId': 'aaaaaaaa',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'IN_SYNC',
                    },
                    {
                        'PhysicalResourceId': 'bbbbbbbb',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'IN_SYNC',
                    },
                    {
                        'PhysicalResourceId': 'cccccccc',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'IN_SYNC',
                    },
                ],
                'no_of_drifted_resources': 0,
                'no_of_resources': 3,
            },
        ])


if __name__ == '__main__':
    unittest.main()
