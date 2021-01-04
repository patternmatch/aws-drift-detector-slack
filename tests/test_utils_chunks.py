import unittest
from drift_detector.utils import chunks

chunk_test_params = [
    ([1, 2, 3, 4], 2, [[1, 2], [3, 4]]),
    ([1, 2, 3, 4], 1, [[1], [2], [3], [4]]),
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5, [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]),
    ([1, 2, 3], 2, [[1, 2], [3]]),
]


stacks = [
    {
        'StackName': 'aws-sam-cli-managed-default',
        'StackStatus': 'CREATE_COMPLETE',
    },
    {
        'StackName': 'hello-world-stack',
        'StackStatus': 'CREATE_COMPLETE',
    },
    {
        'StackName': 'hello-world-stack2',
        'StackStatus': 'CREATE_COMPLETE',
    },
    {
        'StackName': 'hello-world-stack3',
        'StackStatus': 'CREATE_COMPLETE',
    },
    {
        'StackName': 'hello-world-stack4',
        'StackStatus': 'CREATE_COMPLETE',
    },
    {
        'StackName': 'hello-world-stack5',
        'StackStatus': 'CREATE_COMPLETE',
    }
]

expected_stacks = [
    [
        {
            'StackName': 'aws-sam-cli-managed-default',
            'StackStatus': 'CREATE_COMPLETE',
        },
        {
            'StackName': 'hello-world-stack',
            'StackStatus': 'CREATE_COMPLETE',
        }
    ],
    [
        {
            'StackName': 'hello-world-stack2',
            'StackStatus': 'CREATE_COMPLETE',
        },
        {
            'StackName': 'hello-world-stack3',
            'StackStatus': 'CREATE_COMPLETE',
        }
    ],
    [
        {
            'StackName': 'hello-world-stack4',
            'StackStatus': 'CREATE_COMPLETE',
        },
        {
            'StackName': 'hello-world-stack5',
            'StackStatus': 'CREATE_COMPLETE',
        }
    ]
]


class TestChunks(unittest.TestCase):
    def test_chunks_split_into_chunks_correctly(self):
        for input_collection, single_chunk_size, expected_result in chunk_test_params:
            with self.subTest():
                result = list(chunks(input_collection, single_chunk_size))
                self.assertEqual(result, expected_result)

    def test_chunks_split_into_stacks(self):
        self.assertEqual(list(chunks(stacks, 2)), expected_stacks)


if __name__ == '__main__':
    unittest.main()
