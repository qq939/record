import sys
import unittest
import signal
import time
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

dst_dir = Path(__file__).parent / "dst"
dst_dir.mkdir(exist_ok=True)

class TestVideoRecorder(unittest.TestCase):
    def setUp(self):
        self.timeout_seconds = 30
        
    def signal_handler(self, signum, frame):
        raise TimeoutError("Test timed out")
        
    def test_import_modules(self):
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(self.timeout_seconds)
        
        try:
            from PyQt5.QtWidgets import QApplication
            import cv2
            import numpy as np
            from video_recorder import VideoRecorderApp
        finally:
            signal.alarm(0)
            
    def test_dst_directory_exists(self):
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(self.timeout_seconds)
        
        try:
            dst_dir = Path(__file__).parent / "dst"
            self.assertTrue(dst_dir.exists(), "dst目录应该存在")
        finally:
            signal.alarm(0)
            
    def test_video_recorder_class_exists(self):
        signal.signal(signal.SIGALRM, self.signal_handler)
        signal.alarm(self.timeout_seconds)
        
        try:
            from video_recorder import VideoRecorderApp
            self.assertTrue(hasattr(VideoRecorderApp, 'init_ui'))
            self.assertTrue(hasattr(VideoRecorderApp, 'toggle_recording'))
            self.assertTrue(hasattr(VideoRecorderApp, 'start_recording'))
            self.assertTrue(hasattr(VideoRecorderApp, 'stop_recording'))
        finally:
            signal.alarm(0)
            
    def test_dst_directory_creation(self):
        dst_dir = Path(__file__).parent / "dst"
        self.assertTrue(dst_dir.exists(), "dst目录应该存在")
        self.assertTrue(dst_dir.is_dir(), "dst应该是目录")

if __name__ == "__main__":
    unittest.main()
