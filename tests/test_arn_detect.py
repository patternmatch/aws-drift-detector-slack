import unittest

from src.drift_detector import is_arn

class TestArnDetect(unittest.TestCase):
    def test_with_arn(self):
        """
        Test that arn is correctly detected
        """
        self.assertTrue(is_arn("arn:aws:lambda:us-east-1:450349639042:function:serverless-housekeeping-gdrive-prod-finance:4"))


    def test_with_non_arn(self):
        """
        Test that non arn is correctly detected
        """
        self.assertFalse(is_arn("/aws/lambda/serverless-housekeeping-gdrive-prod-finance"))


    def test_with_resource_name(self):
        """
        Test that non arn is correctly detected
        """
        self.assertFalse(is_arn("serverless-housekeeping-gdrive-prod-finance"))


if __name__ == '__main__':
    unittest.main()
