import unittest
from youtube_api import extract_video_id
from src.pipeline import duration_seconds, tag_count

class CoreTests(unittest.TestCase):
    def test_video_urls(self):
        vid='dQw4w9WgXcQ'
        for url in [vid,'https://www.youtube.com/watch?v='+vid,'https://youtu.be/'+vid,'https://www.youtube.com/shorts/'+vid,'https://www.youtube.com/live/'+vid]:
            self.assertEqual(extract_video_id(url),vid)
    def test_reject_other_hosts(self):
        for url in ['https://youtube.com.evil.com/watch?v=dQw4w9WgXcQ','https://example.com/watch?v=dQw4w9WgXcQ','invalid']:
            with self.assertRaises(ValueError): extract_video_id(url)
    def test_durations(self):
        self.assertEqual(duration_seconds('PT2M15S'),135)
        self.assertEqual(duration_seconds('01:02:03'),3723)
    def test_tags(self):
        self.assertEqual(tag_count('cat|dog'),2)

if __name__=='__main__': unittest.main()
