import unittest
import sys

sys.path.insert(0, './drift_detector')

from drift_detector.drift_detector import detect_drift
from unittest.mock import MagicMock


class MockCFClient: pass


mock_cf_client = MockCFClient()


class TestDetectDrift(unittest.TestCase):
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

    def test_detect_drift(self):
        """
        Test that drift is correctly detected
        """
        mock_stacks = [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id'
            }
        ]

        stacks, _ = detect_drift(mock_cf_client, mock_stacks)

        self.assertEqual(stacks, [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id',
                'drift': [
                    {
                        'PhysicalResourceId': 'physical_resource_id',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'MODIFIED',
                    },
                ],
                'no_of_drifted_resources': 1,
                'no_of_resources': 1,
            }
        ])

    def test_detect_drift_with_no_drift(self):
        """
        Test that no drift is correctly detected
        """
        mock_stacks = [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id'
            },
        ]

        mock_cf_client.describe_stack_resource_drifts = MagicMock(return_value={
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

        stacks, _ = detect_drift(mock_cf_client, mock_stacks)

        self.assertEqual(stacks, [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id',
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
                'StackName': 'stack_name',
                'StackId': 'stack_id'
            },
        ]

        mock_cf_client.describe_stack_resource_drifts = MagicMock(return_value={
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

        stacks, _ = detect_drift(mock_cf_client, mock_stacks)

        self.assertEqual(stacks, [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id',
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

    def test_detect_drift_for_resource_with_arn_as_id(self):
        """
        Test that drift is correctly detected for resources with arn id
        """
        mock_stacks = [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id'
            }
        ]

        mock_cf_client.describe_stack_resource_drifts = MagicMock(return_value={
            'StackResourceDrifts': [
                {
                    'StackResourceDriftStatus': 'MODIFIED',
                    'PhysicalResourceId': 'arn:aws:lambda:us-east-1:450349639042:function:serverless-housekeeping-gdrive-prod-stuff:4',
                    'ResourceType': 'resource_type',
                },
            ],
        })

        stacks, _ = detect_drift(mock_cf_client, mock_stacks)

        self.assertEqual(stacks, [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id',
                'drift': [
                    {
                        'PhysicalResourceId': 'serverless-housekeeping-gdrive-prod-stuff:4',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'MODIFIED',
                    },
                ],
                'no_of_drifted_resources': 1,
                'no_of_resources': 1,
            },
        ])

    def test_detect_drift_with_failed_detection(self):
        """
        Test that failed detection are correctly handled
        """
        mock_stacks = [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id'
            },
        ]

        mock_cf_client.describe_stack_resource_drifts = MagicMock(return_value={
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

        stacks, _ = detect_drift(mock_cf_client, mock_stacks)

        self.assertEqual(stacks, [
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id',
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


if __name__ == '__main__':
    unittest.main()
