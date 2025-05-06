"""
Video widget for displaying camera feed in the EyeTracker application
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap


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
        frame_rgb = frame
        if len(frame.shape) == 3:  # Color image (has 3 dimensions)
            if frame.shape[2] == 3:  # 3 channels
                # Convert BGR to RGB
                frame_rgb = frame[..., ::-1].copy()
        
        height, width = frame_rgb.shape[:2]
        bytes_per_line = 3 * width
        
        # Create QImage from the frame
        q_image = QImage(
            frame_rgb.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        
        # Scale the image to fit the widget while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        
        # Get the size of the label
        label_size = self.video_label.size()
        
        # Scale the pixmap to fit the label while preserving aspect ratio
        scaled_pixmap = pixmap.scaled(
            label_size, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Set the pixmap to the label
        self.video_label.setPixmap(scaled_pixmap)
    
    def sizeHint(self):
        """Return a suitable size for the widget"""
        return QSize(640, 480)
    
    def minimumSizeHint(self):
        """Return the minimum size for the widget"""
        return QSize(320, 240)