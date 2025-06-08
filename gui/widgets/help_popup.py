from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt

class HelpPopup(QtWidgets.QWidget):
    def __init__(self, parent, phase="start"):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground)
        self.setAutoFillBackground(True)
        self.setStyleSheet('''
            HelpPopup {
                background: rgba(0, 0, 0, 128);
            }
            QWidget#container {
                border: 2px solid #34495e;
                border-radius: 8px;
                background: white;
            }
            QWidget#container > QLabel {
                color: #2c3e50;
            }
            QLabel#title {
                font-size: 20pt;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton#close {
                color: white;
                font-weight: bold;
                background: #e74c3c;
                border: none;
                border-radius: 12px;
            }
            QPushButton#close:hover {
                background: #c0392b;
            }
        ''')

        # Main layout fills the entire parent
        full_layout = QtWidgets.QVBoxLayout(self)
        full_layout.setContentsMargins(0, 0, 0, 0)

        # Container widget centered in the popup
        self.container = QtWidgets.QWidget(
            autoFillBackground=True, objectName='container')
        full_layout.addWidget(self.container, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)

        # Close button
        self.close_button = QtWidgets.QPushButton(
            'X', self.container, objectName='close')
        self.close_button.clicked.connect(self.close)

        # Container layout
        layout = QtWidgets.QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # Title
        title = QtWidgets.QLabel(
            self._get_title(phase), 
            objectName='title', 
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Help content
        help_content = self._get_help_content(phase)
        
        help_text = QtWidgets.QLabel(help_content)
        help_text.setWordWrap(True)
        help_text.setTextFormat(QtCore.Qt.TextFormat.RichText)
        help_text.setStyleSheet("""
            font-size: 12px;
            line-height: 1.4;
            color: #34495e;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
        """)
        layout.addWidget(help_text)

        # OK button
        ok_button = QtWidgets.QPushButton("Got it!")
        ok_button.clicked.connect(self.close)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(ok_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Install event filter to handle parent resize
        parent.installEventFilter(self)

    def _get_title(self, phase):
        """Get the appropriate title for the help popup based on phase"""
        titles = {
            "start": "EyeTracker Help",
            "calib": "Calibration Help",
            "test": "Test Instructions",
            "results": "Results Help"
        }
        return titles.get(phase, "Help")

    def _get_help_content(self, phase):
        """Get the appropriate help content based on the current phase"""
        help_content_map = {
            "start": """
                <h3>Getting Started</h3>
                <p><b>Step 1:</b> Connect your Arduino device via USB</p>
                <p><b>Step 2:</b> Connect your eye tracking camera</p>
                <p><b>Step 3:</b> Click "Connect Devices" to initialize hardware</p>
                
                <h3>Calibration</h3> 
                <p>• Position the patient comfortably in front of the screen</p>
                <p>• Use the calibration view to set up eye tracking</p>
                <p>• Adjust sensitivity settings for optimal tracking</p>
                
                <h3>Running Tests</h3>
                <p>• Follow the on-screen instructions during tests</p>
                <p>• Monitor the status bar for real-time feedback</p>
                <p>• Review results in the Results view after completion</p>
                
                <h3>Troubleshooting</h3>
                <p>• Check all USB connections if devices aren't detected</p>
                <p>• Ensure proper lighting for eye tracking</p>
                <p>• Restart the application if tracking becomes unstable</p>
            """,
            
            "calib": """
                <h3>Calibration Instructions</h3>
                <p><b>Step 1:</b> Instruct the patient to look at the centerpoint.</p>
                <p><b>Step 2:</b> Position the subject so their eye is in the center of the frame</p>
                <p><b>Step 3:</b> Adjust the zoom slider, to increase the image zoom. Drag yellow focus box to re-position.</p>
                <p><b>Step 4:</b> Once pupil is accurately and consistently dected, click 'Set Position Button'.</p>
                <p><b>Step 5:</b> If user's pupil deviates from set position, bound colour will change from green to blue.</p>
                <p><b>Step 6:</b> Adjust the threshold slider if needed to increase or decrease deviation allowance.</p>
                <p><b>Step 7:</b> Click 'Start Test' when calibration is complete.</p>
                
                <h3>Tips</h3>
                <p>• Ensure good lighting on the subject's face and pupil</p>
                <p>• The eye should be clearly visible and centered, ensure that the pupil only takes up 20%\ of the screen </p>
                <p>• Use 'up', 'down', 'left', 'right' keys to shift zoom box, 'Enter' to select zoom and 'Escape' to reset zoom</p>
                <p>• Use 'L' to set position of pupil</p>
                <p>• Adjust threshold slider to increase or decrease sensitivity to pupil movement</p>
            """,
            
            "test": """
                <h3>Test Instructions</h3>
                <p>During the test, follow these guidelines:</p>
                <p>• Keep your head still and look naturally</p>
                <p>• Follow the on-screen prompts</p>
                <p>• Try to blink normally</p>
                <p>• Alert the operator if you feel uncomfortable</p>
                
                <h3>What to Expect</h3>
                <p>• The test will track your eye movements</p>
                <p>• You will see visual stimuli to follow</p>
                <p>• The test duration varies by protocol</p>
            """,
            
            "results": """
                <h3>Understanding Results</h3>
                <p>The results section displays:</p>
                <p>• Eye movement data and statistics</p>
                <p>• Visual representations of tracking</p>
                <p>• Analysis metrics and measurements</p>
                
                <h3>Export Options</h3>
                <p>• Save results to file for further analysis</p>
                <p>• Print summary reports</p>
                <p>• Export raw data for external processing</p>
            """
        }
        
        return help_content_map.get(phase, "<p>No help available for this section.</p>")

    def showEvent(self, event):
        # Make popup fill the entire parent
        self.setGeometry(self.parent().rect())

    def resizeEvent(self, event):
        # Position close button at top-right of container
        if hasattr(self, 'close_button') and hasattr(self, 'container'):
            button_rect = self.close_button.rect()
            container_rect = self.container.rect()
            button_rect.moveTopRight(container_rect.topRight() + QtCore.QPoint(-10, 10))
            self.close_button.setGeometry(button_rect)

    def eventFilter(self, source, event):
        # Keep popup sized to match parent
        if event.type() == QtCore.QEvent.Type.Resize:
            self.setGeometry(source.rect())
        return super().eventFilter(source, event)