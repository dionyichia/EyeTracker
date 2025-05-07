"""
Video widget for displaying camera feed in the EyeTracker application
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap
import cv2

class VideoWidget(QWidget):
    """Widget for displaying video feed from camera"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        
        layout.addWidget(self.video_label)
    
    def update_frame(self, frame):
        """Update the displayed frame
        
        Args:
            frame: OpenCV frame (numpy array)
        """
        if frame is None:
            return
        
        # Convert OpenCV BGR format to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        height, width, channels = rgb_frame.shape
        bytes_per_line = channels * width
        
        # Create QImage from the frame
        qt_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Convert to QPixmap and set to label
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale pixmap to fit widget while maintaining aspect ratio
        self.video_label.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio))  
    
    def sizeHint(self):
        """Return a suitable size for the widget"""
        return QSize(640, 480)
    
    def minimumSizeHint(self):
        """Return the minimum size for the widget"""
        return QSize(320, 240)