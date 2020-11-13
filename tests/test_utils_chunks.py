import unittest
from drift_detector.utils import chunks

chunk_test_params = [
    ([1, 2, 3, 4], 2, [[1, 2], [3, 4]]),
    ([1, 2, 3, 4], 1, [[1], [2], [3], [4]]),
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5, [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]),
    ([1, 2, 3], 2, [[1, 2], [3]]),
]


class TestChunks(unittest.TestCase):
    def test_chunks_split_into_chunks_correctly(self):
        for input_collection, single_chunk_size, expected_result in chunk_test_params:
            with self.subTest():
                result = list(chunks(input_collection, single_chunk_size))
                self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
