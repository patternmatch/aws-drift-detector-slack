import unittest
import sys

sys.path.insert(0, './drift_detector')

from drift_detector.drift_detector import get_stack_url


class TestGetStackUrl(unittest.TestCase):
    def test_getting_valid_stack_url(self):
        """
        Test that stack url is correctly returned
        """
        self.assertEqual(
            get_stack_url('42'),
            'https://console.aws.amazon.com/cloudformation/home#/stacks/drifts?stackId=42'
        )


if __name__ == '__main__':
    unittest.main()
