import unittest
import sys

sys.path.insert(0, './drift_detector')

from unittest.mock import MagicMock
from drift_detector.drift_detector import append_drift_info


class MockCFClient: pass


mock_cf_client = MockCFClient()


class TestAppendDriftInfo(unittest.TestCase):
    def test_append_drift_info_with_detected_drift(self):
        """
        Test that drift info is correctly appended for detected drift
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
                    'PhysicalResourceId': 'physical_resource_id',
                    'ResourceType': 'resource_type'
                }
            ]
        })

        result = append_drift_info(mock_cf_client, mock_stacks)

        self.assertEqual([
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id',
                'drift': [
                    {
                        'PhysicalResourceId': 'physical_resource_id',
                        'StackResourceDriftStatus': 'MODIFIED',
                        'ResourceType': 'resource_type'
                    }
                ],
                'no_of_drifted_resources': 1,
                'no_of_resources': 1,
            }
        ], result)

    def test_append_drift_info_with_no_detected_drift(self):
        """
        Test that no drift is correctly appended
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
                    'StackResourceDriftStatus': 'IN_SYNC',
                    'PhysicalResourceId': 'physical_resource_id_one',
                    'ResourceType': 'resource_type'
                },
                {
                    'StackResourceDriftStatus': 'IN_SYNC',
                    'PhysicalResourceId': 'physical_resource_id_two',
                    'ResourceType': 'resource_type'
                }
            ]
        })

        stacks = append_drift_info(mock_cf_client, mock_stacks)

        self.assertEqual([
            {
                'StackName': 'stack_name',
                'StackId': 'stack_id',
                'drift': [
                    {
                        'PhysicalResourceId': 'physical_resource_id_one',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'IN_SYNC'
                    },
                    {
                        'PhysicalResourceId': 'physical_resource_id_two',
                        'ResourceType': 'resource_type',
                        'StackResourceDriftStatus': 'IN_SYNC'
                    }
                ],
                'no_of_drifted_resources': 0,
                'no_of_resources': 2
            }
        ], stacks)


if __name__ == '__main__':
    unittest.main()
