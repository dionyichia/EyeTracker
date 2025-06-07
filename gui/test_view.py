"""
Test view for the EyeTracker application
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from gui.widgets.video_widget import VideoWidget
from gui.widgets.help_popup import HelpPopup
import json


class TestView(QWidget):
    """View for running the visual field test"""
    
    # Signals
    test_completed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
        # Timer for updating video feed
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_feed)
        
        # Timer for checking test status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_test_status)
        
        # Test state
        self.test_points_total = 0
        self.test_points_completed = 0
        self.test_results = {
            'points_shown': 0,
            'points_clicked': 0,
            'points_missed': 0,
            'false_positives': 0
        }
        self.points_shown = 0
        self.num_points = 1
        self.click_counter = 0
        self.click_tracker = None
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)

        # Title and Help Button Row
        title_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("Visual Field Test in Progress")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # main_layout.addWidget(title_label)

        # Help button
        help_button = QPushButton("Help")
        help_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                max-width: 60px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        help_button.clicked.connect(self.show_help)
        
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(help_button)
        
        main_layout.addLayout(title_layout)
        
        # Main content area with video feed and status
        content_layout = QHBoxLayout()
        
        # Video feed
        self.video_widget = VideoWidget()
        self.video_widget.setMinimumSize(640, 480)
        content_layout.addWidget(self.video_widget, 3)
        
        # Test status and controls
        status_layout = QVBoxLayout()
        
        # Test progress
        progress_group = QGroupBox("Test Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)  # Will be updated when test starts
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Points: 0 / 0")
        progress_layout.addWidget(self.progress_label)

        self.clicks_label = QLabel("Clicks Made: 0")
        progress_layout.addWidget(self.clicks_label)

        self.successful_detections_label = QLabel("Successful Detections: 0")
        progress_layout.addWidget(self.successful_detections_label)
        
        status_layout.addWidget(progress_group)
        
        # Live status
        status_group = QGroupBox("Live Status")
        status_group_layout = QVBoxLayout(status_group)
        
        # Eye position status
        self.eye_position_label = QLabel("Eye Position: OK")
        self.eye_position_label.setStyleSheet("font-weight: bold; color: green;")
        status_group_layout.addWidget(self.eye_position_label)
        
        # Last action status
        self.last_action_label = QLabel("Waiting for test to start...")
        status_group_layout.addWidget(self.last_action_label)
        
        status_layout.addWidget(status_group)
        
        # Add spacer
        status_layout.addStretch()
        
        # Stop test button
        self.stop_test_btn = QPushButton("Stop Test")
        self.stop_test_btn.setMinimumHeight(50)
        self.stop_test_btn.clicked.connect(self.stop_test)
        status_layout.addWidget(self.stop_test_btn)
        
        # Add status layout to content layout
        content_layout.addLayout(status_layout, 1)
        
        # Add content to main layout
        main_layout.addLayout(content_layout)

    def show_help(self):
        """Show the help popup for calibration"""
        self.help_popup = HelpPopup(self, phase="test")
        self.help_popup.show()
    
    def update_video_feed(self):
        """Update the video feed with the current frame"""
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            frame = self.parent.eye_tracker.get_processed_frame()
            if frame is not None:
                self.video_widget.update_frame(frame)
                
                # Update eye position status
                if self.parent.eye_tracker.is_eye_in_position():
                    self.eye_position_label.setText("Eye Position: OK")
                    self.eye_position_label.setStyleSheet("font-weight: bold; color: green;")
                else:
                    self.eye_position_label.setText("Eye Position: OFF CENTER")
                    self.eye_position_label.setStyleSheet("font-weight: bold; color: red;")
    
    def check_test_status(self):
        """Check the status of the test from the Arduino"""
        if self.parent and hasattr(self.parent, 'arduino_tracker') and self.parent.arduino_tracker:
            # Check if test is still running
            if not self.parent.arduino_tracker.is_test_running:
                self.finish_test()
                return
            
            # Get current test status, Track test progress in real time, currenly add too much lag
            status = self.parent.arduino_tracker.get_test_status()
            
            if 'Running' in status['test_status'] and len(status.keys()) > 1:
                print("here 1")
                
                # Update progress
                self.points_shown = status.get('points_shown', 0)
                self.num_points = status.get('total_points', 1)  # avoid divide by zero
                self.click_counter = status.get('clicks', 0)
                self.click_tracker = status.get('click_pattern', '')

            elif status['test_status'] in ('Finished', 'Ready'):
                self.status_timer.stop()
                self.progress_bar.setValue(100)
                self.progress_label.setText("Test Completed")
                self.clicks_label.setText("")
                self.successful_detections_label.setText("")
                self.finish_test()
                return
            
            if self.click_tracker:
                successful_detections = self.click_tracker.count('1')
                progress = int((self.points_shown / self.num_points) * 100)
            else:
                successful_detections = 0
                progress = 0

            self.progress_bar.setValue(progress)
            self.progress_label.setText(f"Points: {self.points_shown} / {self.num_points}")

            self.clicks_label.setText(f"Clicks Made: {self.click_counter}")
            self.successful_detections_label.setText(f"Successful Detections: {successful_detections}")

            return
        
    
    def start_test(self):
        """Initialize and start the test"""
        # Reset test state
        self.points_shown = 0
        self.num_points = 1
        self.click_counter = 0
        self.click_tracker = None
    
        self.test_points_total = 0
        self.test_points_completed = 0
        self.progress_bar.setValue(0)
        self.progress_label.setText("Points: 0 / 0")
        
        # Start timers
        self.video_timer.start(8)  # ~30 fps
        self.status_timer.start(500)  # Check test status every 500ms

        # Send arduino command to start test
        self.parent.arduino_tracker.start_test()
    
    def stop_test(self):
        """Stop the test before completion"""
        if self.parent and hasattr(self.parent, 'arduino_tracker') and self.parent.arduino_tracker:
            self.parent.arduino_tracker.stop_test()
            self.finish_test()
    
    def finish_test(self):
        """Finish the test and show results"""
        # Stop timers
        self.video_timer.stop()
        self.status_timer.stop()
        
        # Get final results from Arduino
        if self.parent and hasattr(self.parent, 'arduino_tracker') and self.parent.arduino_tracker:
            results = self.parent.arduino_tracker.get_test_results()
            if results:
                self.test_results = results
        
        # Signal test completion
        if self.parent:
            self.parent.end_test(self.test_results)
    
    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        self.start_test()
    
    def hideEvent(self, event):
        """Called when the widget is hidden"""
        super().hideEvent(event)
        
        # Stop timers when the view is hidden
        self.video_timer.stop()
        self.status_timer.stop()