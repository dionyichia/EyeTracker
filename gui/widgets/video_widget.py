"""
Video widget for displaying camera feed in the EyeTracker application
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter
import cv2

class VideoWidget(QWidget):
    """Widget for displaying video feed from camera"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # We no longer need the video_label since we'll paint directly on the widget
        self.setStyleSheet("background-color: black;")
        
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
        
        # Convert to QPixmap and store it
        self.pixmap = QPixmap.fromImage(qt_image)
        
        # Trigger a repaint
        self.update()

        return qt_image
    
    def paintEvent(self, event):
        """Paint the video frame on the widget"""
        super().paintEvent(event)
        
        if self.pixmap is not None:
            painter = QPainter(self)
            # Scale pixmap to fit widget while maintaining aspect ratio
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            
            # Calculate position to center the pixmap in the widget
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            # Draw the pixmap
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # Allow for external paint operations (like overlays)
            if hasattr(self, 'external_paint') and callable(self.external_paint):
                self.external_paint(painter)
                
            painter.end()
    
    def sizeHint(self):
        """Return a suitable size for the widget"""
        return QSize(640, 480)
    
    def minimumSizeHint(self):
        """Return the minimum size for the widget"""
        return QSize(320, 240)