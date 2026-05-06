import sys
import os
from pathlib import Path

dst_dir = Path(__file__).parent / "dst"
dst_dir.mkdir(exist_ok=True)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np


class VideoRecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.video_writer = None
        self.output_dir = Path(__file__).parent / "dst"
        self.init_ui()
        self.init_camera()
        
    def init_ui(self):
        self.setWindowTitle("视频录制面板")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_label)
        
        control_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("开始录制")
        self.record_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px; font-size: 16px;")
        self.record_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_btn)
        
        self.status_label = QLabel("状态: 未录制")
        self.status_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
    def init_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_label.setText("警告: 无法打开摄像头")
            
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        if not self.cap.isOpened():
            self.status_label.setText("错误: 摄像头未打开")
            return
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.avi"
        filepath = self.output_dir / filename
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = 20.0
        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.video_writer = cv2.VideoWriter(
            str(filepath), fourcc, fps, (frame_width, frame_height)
        )
        
        self.is_recording = True
        self.record_btn.setText("停止录制")
        self.record_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-size: 16px;")
        self.status_label.setText(f"状态: 录制中 - {filename}")
        
    def stop_recording(self):
        self.is_recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            
        self.record_btn.setText("开始录制")
        self.record_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px; font-size: 16px;")
        self.status_label.setText("状态: 录制已保存")
        
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            if self.is_recording and self.video_writer is not None:
                self.video_writer.write(frame)
                cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
                
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            q_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            scaled_pixmap = pixmap.scaled(
                self.video_label.width(), self.video_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)
            
    def closeEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        if self.cap is not None:
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    import time
    app = QApplication(sys.argv)
    window = VideoRecorderApp()
    window.show()
    sys.exit(app.exec_())
