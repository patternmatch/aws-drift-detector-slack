import unittest
import sys

sys.path.insert(0, './drift_detector')

from drift_detector.drift_detector import is_status_proper_to_check_drift


class TestIsStatusProperToCheckDrift(unittest.TestCase):
    def test_valid_status(self):
        """
        Test that valid status is correctly detected
        """
        self.assertEqual(is_status_proper_to_check_drift('UPDATE_COMPLETE'), True)

    def test_invalid_status(self):
        """
        Test that invalid status is correctly detected
        """
        self.assertEqual(is_status_proper_to_check_drift('INVALID_STATUS'), False)


if __name__ == '__main__':
    unittest.main()
