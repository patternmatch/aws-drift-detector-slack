import unittest

from src.drift_detector import parse_arn

class TestArnParse(unittest.TestCase):
    def test_with_arn(self):
        """
        Test that arn is correctly detected and parsed
        """
        self.assertEqual(parse_arn("arn:aws:lambda:us-east-1:450349639042:function:serverless-housekeeping-gdrive-prod-finance:4"), "serverless-housekeeping-gdrive-prod-finance:4")


    def test_with_non_arn(self):
        """
        Test that non arn is not parsed and returned
        """
        self.assertEqual(parse_arn("/aws/lambda/serverless-housekeeping-gdrive-prod-finance"), "/aws/lambda/serverless-housekeeping-gdrive-prod-finance")


    def test_with_resource_name(self):
        """
        Test that non arn is not parsed and returned
        """
        self.assertEqual(parse_arn("serverless-housekeeping-gdrive-prod-finance"), "serverless-housekeeping-gdrive-prod-finance")


if __name__ == '__main__':
    unittest.main()
