import unittest

from src.drift_detector import get_emoji_for_status


class TestEmoji(unittest.TestCase):
    def test_deleted_status_emoji(self):
        """
        Test that correct emoji is returned for deleted status
        """
        self.assertEqual(get_emoji_for_status('DELETED'), ":x:")


    def test_modified_status_emoji(self):
        """
        Test that correct emoji is returned for modified status
        """
        self.assertEqual(get_emoji_for_status('MODIFIED'), ":warning:")


    def test_in_sync_status_emoji(self):
        """
        Test that correct emoji is returned for in sync status
        """
        self.assertEqual(get_emoji_for_status('IN_SYNC'), ":heavy_check_mark:")


    def test_fallback_status_emoji(self):
        """
        Test that no emoji is returned when status is empty
        """
        self.assertEqual(get_emoji_for_status(None), "")


if __name__ == '__main__':
    unittest.main()
