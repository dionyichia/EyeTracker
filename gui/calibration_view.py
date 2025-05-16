"""
Calibration view for the EyeTracker application
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen

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
        self.threshold_value = 48  # Default threshold
        
        # Zoom region selection
        self.zoom_factor = 1  # Target zoom factor
        self.previous_zoom_factor = 1 # The zoom factor of the currently displayed frame 
        self.zoom_center = None # Center of zoom, relative to original frame / image
        self.zoom_selection_active = False
        self.zoom_region = None
        self.zoom_region_center = None # Center of zoom, relative to current video frame / image
        self.original_frame = None
        self.is_zoomed = False
        self.dragging = False
        self.drag_start_pos = None

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
            "3. Adjust zoom and position the zoom box using mouse or arrow keys\n"
            "4. Press 'L' or click 'Set Position' to lock the eye position\n"
            "5. Click 'Start Test' when ready"
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
        self.video_widget.mousePressEvent = self.on_video_mouse_press
        self.video_widget.mouseMoveEvent = self.on_video_mouse_move
        self.video_widget.mouseReleaseEvent = self.on_video_mouse_release
        self.video_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.video_widget.keyPressEvent = self.on_video_key_press
        # Set external paint function to draw zoom overlay
        self.video_widget.external_paint = self.on_video_paint
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
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(self.threshold_value)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_value_label = QLabel(f"Current: {self.threshold_value}")
        threshold_layout.addWidget(self.threshold_value_label)
        
        controls_layout.addWidget(threshold_group)

        # Zoom control
        zoom_group = QGroupBox("Zoom Adjustment")
        zoom_layout = QVBoxLayout(zoom_group)
        
        zoom_label = QLabel("Adjust zoom factor:")
        zoom_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(30)
        self.zoom_slider.setValue(self.zoom_factor)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        
        self.zoom_factor_label = QLabel(f"Current: {self.zoom_factor}x")
        zoom_layout.addWidget(self.zoom_factor_label)
        
        zoom_buttons_layout = QHBoxLayout()
        self.set_zoom_btn = QPushButton("Set Zoom")
        self.set_zoom_btn.clicked.connect(self.set_zoom)
        self.set_zoom_btn.setEnabled(False)  # Enabled when zoom factor > 1
        zoom_buttons_layout.addWidget(self.set_zoom_btn)
        
        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.reset_zoom_btn.setEnabled(False)  # Enabled after zoom is applied
        zoom_buttons_layout.addWidget(self.reset_zoom_btn)
        
        zoom_layout.addLayout(zoom_buttons_layout)
        
        controls_layout.addWidget(zoom_group)
        
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
    
    def on_zoom_changed(self, value):
        """Handle zoom slider value change"""
        self.zoom_factor = value
        self.zoom_factor_label.setText(f"Current: {value}x")
        
        # Enable/disable set zoom button based on zoom factor
        self.set_zoom_btn.setEnabled(value > 1)
        
        # Activate zoom region selection when zoom factor > 1
        if value > 1:
            self.zoom_selection_active = True
            self.update_zoom_region()
        elif value == 1:
            self.zoom_selection_active = False
            
        # Force repaint to show/hide the zoom box
        self.video_widget.update()
    
    def update_zoom_region(self):
        """Calculate and update the zoom region based on current zoom factor"""
        if not hasattr(self.video_widget, 'pixmap') or self.video_widget.pixmap is None:
            return

        # Size of the selection box IF IT WERE ON THE ORIGINAL, UNZOOMED FRAME
        selection_width_in_original_coords = self.original_frame.width() / self.zoom_factor
        selection_height_in_original_coords = self.original_frame.height() / self.zoom_factor
        
        # How large this selection box should APPEAR on the currently displayed video_widget.
        # If current display is zoomed by previous_total_zoom_factor, the drawn box appears that much larger.
        drawn_width_on_widget = selection_width_in_original_coords * self.previous_zoom_factor
        drawn_height_on_widget = selection_height_in_original_coords * self.previous_zoom_factor
        
        # Default center is the middle of the video widget
        if self.zoom_region_center is None:
            self.zoom_region_center = QPoint(
                self.video_widget.width() // 2,
                self.video_widget.height() // 2
            )

            if not self.zoom_center:
                self.zoom_center =  self.zoom_region_center

        # Calculate top-left for the QRect to be drawn on the widget
        x_widget = self.zoom_region_center.x() - (drawn_width_on_widget / 2)
        y_widget = self.zoom_region_center.y() - (drawn_height_on_widget / 2)
        
        # Clamp the drawn box to stay within video_widget bounds
        x_widget = max(0, min(x_widget, self.video_widget.width() - drawn_width_on_widget))
        y_widget = max(0, min(y_widget, self.video_widget.height() - drawn_height_on_widget))
        
        # Ensure width/height are not negative after clamping position
        final_drawn_width = max(0, min(drawn_width_on_widget, self.video_widget.width() - x_widget))
        final_drawn_height = max(0, min(drawn_height_on_widget, self.video_widget.height() - y_widget))

        self.zoom_region = QRect(int(x_widget), int(y_widget), int(final_drawn_width), int(final_drawn_height))
        self.video_widget.update() # Request repaint

    
    def set_zoom(self):
        """Apply the zoom to the region centered at self.zoom_region_center."""
        if not self.original_frame or not self.zoom_selection_active or self.zoom_factor <= 1.0:
            return
            
        # This is the point on the video_widget that the user wants to be the center of the new zoom.
        # It should have been updated by mouse movements.
        click_on_widget = self.zoom_region_center
        if click_on_widget is None: # Fallback if mouse hasn't moved over widget yet
            click_on_widget = QPoint(self.video_widget.width() // 2, self.video_widget.height() // 2)

        new_center_orig_x = 0.0
        new_center_orig_y = 0.0

        if self.previous_zoom_factor == 1.0 or not self.is_zoomed:
            # Current view is the original frame (or a 1x scaled version of it).
            # Map click on widget directly to original frame coordinates via ratios.
            new_center_orig_x = (click_on_widget.x() / self.video_widget.width()) * self.original_frame.width()
            new_center_orig_y = (click_on_widget.y() / self.video_widget.height()) * self.original_frame.height()
        else:
            # We are already zoomed in.
            # self.zoom_center is the center of the current view (in original_frame coords).
            # self.previous_zoom_factor is the zoom factor of this current view.
            
            # Dimensions of the currently visible part of the original_frame (in original_frame units)
            current_view_width_orig = self.original_frame.width() / self.previous_zoom_factor
            current_view_height_orig = self.original_frame.height() / self.previous_zoom_factor

            # Top-left of this visible part, in original_frame coordinates
            current_view_tl_x_orig = self.zoom_center.x() - current_view_width_orig / 2.0
            current_view_tl_y_orig = self.zoom_center.y() - current_view_height_orig / 2.0
            
            # Relative position of the click within the video_widget
            rel_x_in_widget = click_on_widget.x() / self.video_widget.width()
            rel_y_in_widget = click_on_widget.y() / self.video_widget.height()

            # Map this relative click to an absolute point in original_frame coordinates
            new_center_orig_x = current_view_tl_x_orig + rel_x_in_widget * current_view_width_orig
            new_center_orig_y = current_view_tl_y_orig + rel_y_in_widget * current_view_height_orig

        # Clamp the new center to be within the bounds of the original frame
        new_center_orig_x = max(0.0, min(new_center_orig_x, float(self.original_frame.width())))
        new_center_orig_y = max(0.0, min(new_center_orig_y, float(self.original_frame.height())))
        
        self.zoom_center = QPoint(int(new_center_orig_x), int(new_center_orig_y))
        
        self.is_zoomed = True
        self.zoom_selection_active = False # Turn off selection box drawing after zoom is set

        # Calculate center ratio for eye_tracker, relative to the original frame.
        # self.zoom_factor is the new total zoom factor from the slider.
        rel_center_x_for_tracker = self.zoom_center.x() / self.original_frame.width()
        rel_center_y_for_tracker = self.zoom_center.y() / self.original_frame.height()

        # Apply zoom to eye tracker (or your main frame processing logic)
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            self.parent.eye_tracker.set_zoom(self.zoom_factor, center=(rel_center_x_for_tracker, rel_center_y_for_tracker))
        # If you have a method like your static `zoom_frame` that you call to get the actual
        # pixmap for video_widget, you would call it here using self.zoom_factor and these ratios.
        # e.g., zoomed_pixmap = ZoomHandler.zoom_frame(self.original_frame_pixmap, self.zoom_factor, center=(rel_center_x_for_tracker, rel_center_y_for_tracker))
        # self.video_widget.setPixmap(zoomed_pixmap)

        # Update button states
        self.set_zoom_btn.setEnabled(False) # Usually disable until zoom_factor changes again
        self.reset_zoom_btn.setEnabled(True)
        
        # Store the zoom factor that was just applied for the next iteration's calculations
        self.previous_zoom_factor = self.zoom_factor 
        
        self.video_widget.update() # Force repaint to display the newly zoomed frame
    
    def reset_zoom(self):
        """Reset zoom to default state"""
        self.zoom_factor = 1
        self.zoom_slider.setValue(1)
        self.zoom_factor_label.setText("Current: 1x")
        self.is_zoomed = False
        self.zoom_selection_active = False
        self.zoom_region_center = None
        
        # Reset zoom in eye tracker
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            self.parent.eye_tracker.set_zoom(1)
            
        # Update button states
        self.set_zoom_btn.setEnabled(False)
        self.reset_zoom_btn.setEnabled(False)
        
        # Force repaint to update the display
        self.video_widget.update()

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
                qt_image = self.video_widget.update_frame(frame)

                return qt_image
        
            else:
                print("No frame detected")

        return None
    
    def on_video_paint(self, painter):
        """Custom paint function for the video widget to overlay zoom selection box"""
        # Draw zoom selection box if active
        if self.zoom_selection_active and self.zoom_region:
            # Set up semi-transparent overlay for the non-selected area
            overlay_color = QColor(0, 0, 0, 100)  # Semi-transparent black
            painter.fillRect(0, 0, self.video_widget.width(), self.zoom_region.y(), overlay_color)
            painter.fillRect(0, self.zoom_region.y() + self.zoom_region.height(), 
                            self.video_widget.width(), self.video_widget.height() - (self.zoom_region.y() + self.zoom_region.height()), 
                            overlay_color)
            painter.fillRect(0, self.zoom_region.y(), self.zoom_region.x(), self.zoom_region.height(), overlay_color)
            painter.fillRect(self.zoom_region.x() + self.zoom_region.width(), self.zoom_region.y(), 
                            self.video_widget.width() - (self.zoom_region.x() + self.zoom_region.width()), 
                            self.zoom_region.height(), overlay_color)
            
            # Draw border around selection box
            border_pen = QPen(QColor(255, 255, 0))  # Yellow border
            border_pen.setWidth(2)
            painter.setPen(border_pen)
            painter.drawRect(self.zoom_region)
            
            # Draw instructions inside the zoom box
            text_pen = QPen(QColor(255, 255, 255))  # White text
            painter.setPen(text_pen)

            # If box has not been shifted, show shifting instructions
            if self.zoom_region_center == (self.original_frame.width() // 2, self.original_frame.height() // 2) :
                painter.drawText(
                    self.zoom_region.x() + 5, 
                    self.zoom_region.y() + 20, 
                    "Drag or use arrow keys to position"
                )
    
    def on_video_mouse_press(self, event):
        """Handle mouse press events on the video widget"""
        if self.zoom_selection_active and self.zoom_region:
            if self.zoom_region.contains(event.position().toPoint()):
                self.dragging = True
                self.drag_start_pos = event.position().toPoint()
            else:
                # If clicked outside the current zoom region, recenter it
                self.zoom_region_center = event.position().toPoint()
                self.update_zoom_region()
                self.dragging = True
                self.drag_start_pos = event.position().toPoint()
            
            # Force repaint to update the display
            self.video_widget.update()
    
    def on_video_mouse_move(self, event):
        """Handle mouse move events on the video widget"""
        if self.dragging and self.zoom_selection_active:
            # Calculate the movement delta
            delta_x = event.position().toPoint().x() - self.drag_start_pos.x()
            delta_y = event.position().toPoint().y() - self.drag_start_pos.y()
            
            # Update drag start position for next move
            self.drag_start_pos = event.position().toPoint()
            
            # Move the zoom center
            if self.zoom_region_center:
                self.zoom_region_center = QPoint(
                    self.zoom_region_center.x() + delta_x,
                    self.zoom_region_center.y() + delta_y
                )
                
                # Make sure center stays within video bounds
                self.zoom_region_center.setX(max(0, min(self.zoom_region_center.x(), self.video_widget.width())))
                self.zoom_region_center.setY(max(0, min(self.zoom_region_center.y(), self.video_widget.height())))
                
                # Update the zoom region rectangle
                self.update_zoom_region()
                
                # Force repaint to update the display
                self.video_widget.update()
    
    def on_video_mouse_release(self, event):
        """Handle mouse release events on the video widget"""
        self.dragging = False
    
    def on_video_key_press(self, event):
        """Handle key press events on the video widget"""
        step = 10  # Pixels to move per key press
        
        if self.zoom_selection_active and self.zoom_region_center:
            if event.key() == Qt.Key.Key_Left:
                self.zoom_region_center.setX(max(0, self.zoom_region_center.x() - step))
                self.update_zoom_region()
                self.video_widget.update()
            elif event.key() == Qt.Key.Key_Right:
                self.zoom_region_center.setX(min(self.video_widget.width(), self.zoom_region_center.x() + step))
                self.update_zoom_region()
                self.video_widget.update()
            elif event.key() == Qt.Key.Key_Up:
                self.zoom_region_center.setY(max(0, self.zoom_region_center.y() - step))
                self.update_zoom_region()
                self.video_widget.update()
            elif event.key() == Qt.Key.Key_Down:
                self.zoom_region_center.setY(min(self.video_widget.height(), self.zoom_region_center.y() + step))
                self.update_zoom_region()
                self.video_widget.update()
            elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.set_zoom()
            elif event.key() == Qt.Key.Key_Escape:
                if self.is_zoomed:
                    self.reset_zoom()
                else:
                    self.zoom_selection_active = False
                    self.video_widget.update()
        elif event.key() == Qt.Key.Key_L:
            self.set_position()
        else:
            # Pass the event to the parent handler
            super(QWidget, self.video_widget).keyPressEvent(event)
    
    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        
        # Start video timer when the view is shown
        if self.parent and hasattr(self.parent, 'eye_tracker') and self.parent.eye_tracker:
            self.video_timer.start(8)  # ~120 fps

            self.initialise_original_frame()
    
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

    def initialise_original_frame(self):
        """Set original frame on entry"""
        self.original_frame = self.update_video_feed()
        print(self.original_frame.width(), self.original_frame.height())


