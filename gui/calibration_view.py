"""
Calibration view for the EyeTracker application
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

from gui.widgets.video_widget import VideoWidget


class CalibrationView(QWidget):
    """View for calibrating and positioning the eye tracker"""
    
    # Signals
    calibration_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Timer for updating video feed
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_feed)
        
        # Track calibration state
        self.is_calibrated = False
        self.threshold_value = 128  # Default threshold

        self.setup_ui()
        
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Eye Position Calibration")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Instructions
        instructions = (
            "1. Position the subject so their eye is in the center of the frame\n"
            "2. Adjust the threshold slider if needed\n"
            "3. Press 'L' or click 'Set Position' to lock the eye position\n"
            "4. Click 'Start Test' when ready"
        )
        instr_label = QLabel(instructions)
        instr_label.setStyleSheet("margin: 10px;")
        instr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(instr_label)
        
        # Main content area with video feed and controls
        content_layout = QHBoxLayout()
        
        # Video feed
        self.video_widget = VideoWidget()
        self.video_widget.setMinimumSize(640, 480)
        content_layout.addWidget(self.video_widget, 3)
        
        # Controls
        controls_layout = QVBoxLayout()
        
        # Threshold control
        threshold_group = QGroupBox("Threshold Adjustment")
        threshold_layout = QVBoxLayout(threshold_group)
        
        threshold_label = QLabel("Adjust pupil detection threshold:")
        threshold_layout.addWidget(threshold_label)
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(255)
        self.threshold_slider.setValue(self.threshold_value)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_value_label = QLabel(f"Current: {self.threshold_value}")
        threshold_layout.addWidget(self.threshold_value_label)
        
        controls_layout.addWidget(threshold_group)
        
        # Calibration control
        calibration_group = QGroupBox("Calibration")
        calibration_layout = QVBoxLayout(calibration_group)
        
        self.set_position_btn = QPushButton("Set Position (L)")
        self.set_position_btn.clicked.connect(self.set_position)
        calibration_layout.addWidget(self.set_position_btn)
        
        self.calibration_status = QLabel("Status: Not calibrated")
        calibration_layout.addWidget(self.calibration_status)
        
        controls_layout.addWidget(calibration_group)
        
        # Add spacer
        controls_layout.addStretch()
        
        # Start test button
        self.start_test_btn = QPushButton("Start Test")
        self.start_test_btn.setMinimumHeight(50)
        self.start_test_btn.setEnabled(False)  # Disabled until calibrated
        self.start_test_btn.clicked.connect(self.on_start_test)
        controls_layout.addWidget(self.start_test_btn)
        
        # Add controls to content layout
        content_layout.addLayout(controls_layout, 1)
        
        # Add content to main layout
        main_layout.addLayout(content_layout)
    
    def on_threshold_changed(self, value):
        """Handle threshold slider value change"""
        self.threshold_value = value
        self.threshold_value_label.setText(f"Current: {value}")
        
        # Update eye tracker threshold if available
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            self.parent.eye_tracker.set_threshold(value)
    
    def set_position(self):
        """Set the eye position"""
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            self.parent.eye_tracker.lock_position()
            self.is_calibrated = True
            self.calibration_status.setText("Status: Calibrated")
            self.start_test_btn.setEnabled(True)
    
    def on_start_test(self):
        """Start the test"""
        if self.parent:
            self.parent.start_test()
    
    def update_video_feed(self):
        """Update the video feed with the current frame"""
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            frame = self.parent.eye_tracker.get_processed_frame()
            if frame is not None:
                self.video_widget.update_frame(frame)
            else:
                print("No frame detected")
    
    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        
        # Start video timer when the view is shown
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            self.video_timer.start(33)  # ~30 fps
    
    def hideEvent(self, event):
        """Called when the widget is hidden"""
        super().hideEvent(event)
        
        # Stop video timer when the view is hidden
        self.video_timer.stop()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_L:
            self.set_position()
        else:
            super().keyPressEvent(event)