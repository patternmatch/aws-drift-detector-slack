import unittest

from unittest.mock import Mock
from src.drift_detector import check_drifts_detection_status


class MockCFClient: pass


mock_cf_client = MockCFClient()


class TestCheckDriftsDetectionStatus(unittest.TestCase):
    def test_test_check_drifts_detection_status_with_failed_detection(self):
        """
        Test that drift detection status with failed detection returns failed detections
        """

        complete_detection_id = 1
        failed_detection_id = 2

        stacks_checking_ids = [complete_detection_id, failed_detection_id]

        status_per_id = {
            complete_detection_id: {
                'DetectionStatus': 'DETECTION_COMPLETE'
            },
            failed_detection_id: {
                'StackId': 'failed_stack_id',
                'DetectionStatus': 'DETECTION_FAILED',
                'DetectionStatusReason': "Fail reason"
            }}

        def mock_describe_stack_drift_detection_status(**kwargs):
            return status_per_id[kwargs['StackDriftDetectionId']]

        mock_cf_client.describe_stack_drift_detection_status = Mock(
            side_effect=mock_describe_stack_drift_detection_status)

        detection_failed_stack_ids = check_drifts_detection_status(mock_cf_client, stacks_checking_ids)

        self.assertEqual(['failed_stack_id'], detection_failed_stack_ids)


if __name__ == '__main__':
    unittest.main()
