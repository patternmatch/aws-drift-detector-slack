import unittest
import os

from unittest.mock import MagicMock
from src.drift_detector import find_stacks

class MockCFClient: pass
class MockPaginator: pass

mock_cfclient = MockCFClient()
mock_paginator = MockPaginator()


class TestFindStacks(unittest.TestCase):
    def setUp(self):
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

        mock_cfclient.get_paginator = MagicMock(return_value=mock_paginator)


    def tearDown(self):
        # Reset 'STACK_REGEX' back to default, after each test.
        os.environ['STACK_REGEX'] = '.*'


    def test_find_stacks(self):
        """
        Test that stacks are found and returned
        """
        self.assertEqual(find_stacks(mock_cfclient), [
            {
                'StackName': 'aws-sam-cli-managed-default',
                'StackStatus': 'CREATE_COMPLETE',
            },
            {
                'StackName': 'hello-world-stack',
                'StackStatus': 'CREATE_COMPLETE',
            }
        ])


    def test_find_stacks_with_valid_regex(self):
        """
        Test that stacks matching regex are found and returned
        """
        os.environ['STACK_REGEX'] = '.*world.*'

        self.assertEqual(find_stacks(mock_cfclient), [
            {
                'StackName': 'hello-world-stack',
                'StackStatus': 'CREATE_COMPLETE',
            },
        ])


    def test_find_stacks_with_valid_regex_and_no_matches(self):
        """
        Test that stacks matching regex are found and returned
        """
        os.environ['STACK_REGEX'] = '.*test.*'

        self.assertEqual(find_stacks(mock_cfclient), [])


if __name__ == '__main__':
    unittest.main()
