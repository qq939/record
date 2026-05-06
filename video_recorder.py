import sys
import os
import time
from pathlib import Path

dst_dir = Path(__file__).parent / "dst"
dst_dir.mkdir(exist_ok=True)

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QComboBox, QLineEdit, QTabWidget,
                              QFrame, QSizePolicy, QScrollArea)
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QImage, QPixmap, QFont, QPalette, QColor, QIcon
import cv2
import numpy as np


class VideoRecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.video_writer = None
        self.output_dir = Path(__file__).parent / "dst"
        self.current_camera = 0
        self.cap = None
        self.current_source_type = None
        self.frame_count = 0
        self.fps = 0
        self.last_frame_time = time.time()
        self.init_ui()
        self.detect_cameras()
        
    def init_ui(self):
        self.setWindowTitle("视频录制面板")
        self.setGeometry(100, 100, 1024, 768)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                background-color: #252526;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbf;
            }
            QPushButton#recordBtn {
                background-color: #e74c3c;
                min-width: 120px;
            }
            QPushButton#recordBtn:hover {
                background-color: #c0392b;
            }
            QPushButton#recordBtn.recording {
                background-color: #27ae60;
            }
            QPushButton#refreshBtn {
                background-color: #6c757d;
                min-width: 80px;
            }
            QPushButton#refreshBtn:hover {
                background-color: #5a6268;
            }
            QPushButton#addCameraBtn {
                background-color: #17a2b8;
            }
            QPushButton#addCameraBtn:hover {
                background-color: #138496;
            }
            QPushButton#connectBtn {
                background-color: #28a745;
            }
            QPushButton#connectBtn:hover {
                background-color: #218838;
            }
            QPushButton#disconnectBtn {
                background-color: #dc3545;
            }
            QPushButton#disconnectBtn:hover {
                background-color: #c82333;
            }
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #5d5d5d;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #5d5d5d;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox::dropDown {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #888;
                margin-right: 10px;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QLabel#videoLabel {
                background-color: #000000;
                border-radius: 8px;
                min-height: 480px;
            }
            QLabel#statusLabel {
                font-size: 14px;
                font-weight: bold;
                color: #cccccc;
            }
            QLabel#titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #0078d4;
            }
        """)
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        title = QLabel("📹 视频录制面板")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        self.tabs = QTabWidget()
        
        local_tab = QWidget()
        local_layout = QVBoxLayout(local_tab)
        local_layout.setContentsMargins(15, 15, 15, 15)
        local_layout.setSpacing(10)
        
        local_title = QLabel("📷 本地相机")
        local_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078d4;")
        local_layout.addWidget(local_title)
        
        camera_row = QHBoxLayout()
        camera_row.addWidget(QLabel("选择相机:"))
        
        self.camera_combo = QComboBox()
        self.camera_combo.currentIndexChanged.connect(self.on_camera_changed)
        camera_row.addWidget(self.camera_combo)
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setObjectName("refreshBtn")
        self.refresh_btn.clicked.connect(self.detect_cameras)
        camera_row.addWidget(self.refresh_btn)
        
        camera_row.addStretch()
        local_layout.addLayout(camera_row)
        
        manual_row = QHBoxLayout()
        manual_row.addWidget(QLabel("手动输入索引:"))
        self.manual_index = QLineEdit()
        self.manual_index.setPlaceholderText("输入相机索引 (如 2, 3...)")
        self.manual_index.setMaximumWidth(300)
        manual_row.addWidget(self.manual_index)
        
        self.add_camera_btn = QPushButton("➕ 添加相机")
        self.add_camera_btn.setObjectName("addCameraBtn")
        self.add_camera_btn.clicked.connect(self.add_manual_camera)
        manual_row.addWidget(self.add_camera_btn)
        
        manual_row.addStretch()
        local_layout.addLayout(manual_row)
        self.tabs.addTab(local_tab, "本地相机")
        
        rtsp_tab = QWidget()
        rtsp_layout = QVBoxLayout(rtsp_tab)
        rtsp_layout.setContentsMargins(15, 15, 15, 15)
        rtsp_layout.setSpacing(10)
        
        rtsp_title = QLabel("🌐 网络摄像头 (RTSP)")
        rtsp_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078d4;")
        rtsp_layout.addWidget(rtsp_title)
        
        rtsp_info = QLabel("💡 海康/网络摄像头RTSP地址格式:")
        rtsp_layout.addWidget(rtsp_info)
        
        rtsp_format = QLabel("rtsp://用户名:密码@IP地址:554/Streaming/Channels/101")
        rtsp_format.setStyleSheet("color: #6c757d; font-size: 12px; background-color: #2d2d2d; padding: 8px; border-radius: 4px;")
        rtsp_layout.addWidget(rtsp_format)
        
        rtsp_layout.addWidget(QLabel("📍 RTSP地址:"))
        self.rtsp_input = QLineEdit()
        self.rtsp_input.setPlaceholderText("rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101")
        rtsp_layout.addWidget(self.rtsp_input)
        
        rtsp_btn_layout = QHBoxLayout()
        self.connect_rtsp_btn = QPushButton("🔗 连接RTSP")
        self.connect_rtsp_btn.setObjectName("connectBtn")
        self.connect_rtsp_btn.clicked.connect(self.connect_rtsp)
        rtsp_btn_layout.addWidget(self.connect_rtsp_btn)
        
        self.disconnect_rtsp_btn = QPushButton("❌ 断开连接")
        self.disconnect_rtsp_btn.setObjectName("disconnectBtn")
        self.disconnect_rtsp_btn.clicked.connect(self.disconnect_rtsp)
        rtsp_btn_layout.addWidget(self.disconnect_rtsp_btn)
        
        rtsp_btn_layout.addStretch()
        rtsp_layout.addLayout(rtsp_btn_layout)
        
        self.rtsp_status = QLabel("状态: 未连接")
        self.rtsp_status.setStyleSheet("color: #6c757d;")
        rtsp_layout.addWidget(self.rtsp_status)
        
        rtsp_layout.addStretch()
        self.tabs.addTab(rtsp_tab, "网络摄像头(RTSP)")
        
        main_layout.addWidget(self.tabs)
        
        self.video_label = QLabel()
        self.video_label.setObjectName("videoLabel")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.video_label)
        
        info_row = QHBoxLayout()
        self.fps_label = QLabel("FPS: 0")
        info_row.addWidget(self.fps_label)
        
        self.resolution_label = QLabel("分辨率: --")
        info_row.addWidget(self.resolution_label)
        
        info_row.addStretch()
        
        self.status_label = QLabel("状态: 未录制")
        self.status_label.setObjectName("statusLabel")
        info_row.addWidget(self.status_label)
        
        main_layout.addLayout(info_row)
        
        control_layout = QHBoxLayout()
        control_layout.addStretch()
        
        self.record_btn = QPushButton("⏺ 开始录制")
        self.record_btn.setObjectName("recordBtn")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setMinimumSize(150, 45)
        control_layout.addWidget(self.record_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        self.setLayout(main_layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
    def detect_cameras(self):
        self.camera_combo.clear()
        available_cameras = []
        
        for i in range(10):
            test_cap = cv2.VideoCapture(i)
            if test_cap.isOpened():
                available_cameras.append(i)
                test_cap.release()
            time.sleep(0.1)
                
        for cam_idx in available_cameras:
            self.camera_combo.addItem(f"📷 相机 {cam_idx}", cam_idx)
            
        if not available_cameras:
            self.status_label.setText("⚠️ 警告: 未检测到本地摄像头")
        else:
            self.init_camera(available_cameras[0])
            self.status_label.setText(f"✅ 检测到 {len(available_cameras)} 个本地相机")
            
    def add_manual_camera(self):
        try:
            manual_idx = int(self.manual_index.text())
            test_cap = cv2.VideoCapture(manual_idx)
            if test_cap.isOpened():
                if self.camera_combo.findData(manual_idx) == -1:
                    self.camera_combo.addItem(f"📷 相机 {manual_idx} (手动)", manual_idx)
                    self.camera_combo.setCurrentIndex(self.camera_combo.count() - 1)
                test_cap.release()
                self.status_label.setText(f"✅ 已添加相机 {manual_idx}")
            else:
                self.status_label.setText(f"❌ 错误: 相机 {manual_idx} 不可用")
                test_cap.release()
        except ValueError:
            self.status_label.setText("❌ 错误: 请输入有效的数字")
            
    def connect_rtsp(self):
        rtsp_url = self.rtsp_input.text().strip()
        if not rtsp_url:
            self.rtsp_status.setText("❌ 错误: 请输入RTSP地址")
            return
            
        if self.cap is not None:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(rtsp_url)
        time.sleep(1)
        
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_source_type = 'rtsp'
                self.rtsp_status.setText(f"✅ 已连接")
                self.status_label.setText("🌐 状态: 网络摄像头已连接")
            else:
                self.rtsp_status.setText("❌ 错误: 无法读取视频流")
                self.cap.release()
                self.cap = None
        else:
            self.rtsp_status.setText("❌ 错误: 无法连接到RTSP流")
            self.cap = None
            
    def disconnect_rtsp(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.current_source_type = None
        self.rtsp_status.setText("状态: 已断开")
        self.status_label.setText("状态: 未连接")
        
    def init_camera(self, camera_index):
        if self.cap is not None:
            self.cap.release()
            
        self.current_camera = camera_index
        self.current_source_type = 'local'
        self.cap = cv2.VideoCapture(camera_index)
        time.sleep(0.5)
        
        if not self.cap.isOpened():
            self.status_label.setText(f"❌ 错误: 无法打开相机 {camera_index}")
            
    def on_camera_changed(self, index):
        if self.is_recording:
            self.stop_recording()
            
        camera_index = self.camera_combo.itemData(index)
        if camera_index is not None:
            self.init_camera(camera_index)
            self.tabs.setCurrentIndex(0)
            
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        if self.cap is None or not self.cap.isOpened():
            self.status_label.setText("❌ 错误: 摄像头未打开")
            return
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.avi"
        filepath = self.output_dir / filename
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = 20.0
        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if frame_width == 0 or frame_height == 0:
            frame_width = 1280
            frame_height = 720
            
        self.video_writer = cv2.VideoWriter(
            str(filepath), fourcc, fps, (frame_width, frame_height)
        )
        
        self.is_recording = True
        self.frame_count = 0
        self.record_btn.setText("⏹ 停止录制")
        self.record_btn.setObjectName("recordBtn recording")
        self.record_btn.setStyleSheet(self.styleSheet())
        self.status_label.setText(f"🔴 录制中 - {filename}")
        
    def stop_recording(self):
        self.is_recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            
        self.record_btn.setText("⏺ 开始录制")
        self.record_btn.setObjectName("recordBtn")
        self.record_btn.setStyleSheet(self.styleSheet())
        self.status_label.setText("✅ 录制已保存到 dst 目录")
        
    def update_frame(self):
        if self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if ret:
            current_time = time.time()
            self.frame_count += 1
            
            if current_time - self.last_frame_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_frame_time = current_time
                self.fps_label.setText(f"📊 FPS: {self.fps}")
                self.resolution_label.setText(f"📐 分辨率: {frame.shape[1]}x{frame.shape[0]}")
            
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
        else:
            if self.current_source_type == 'rtsp':
                self.rtsp_status.setText("⚠️ 视频流断开，正在重连...")
                self.connect_rtsp()
            
    def closeEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        if self.cap is not None:
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoRecorderApp()
    window.show()
    sys.exit(app.exec_())
