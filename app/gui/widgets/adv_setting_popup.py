from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal

class AdvancedSettingsPopup(QtWidgets.QWidget):
    """Advanced Settings Popup for power optimization and other advanced features."""
    
    # Signal emitted when power mode changes
    power_mode_changed = pyqtSignal(str)  # Emits 'low', 'medium', or 'high'

    def __init__(self, parent, current_power_mode="high"):
        super().__init__(parent)
        self.current_power_mode = current_power_mode
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground)
        self.setAutoFillBackground(True)

        # StyleSheet remains unchanged
        self.setStyleSheet('''
            AdvancedSettingsPopup {
                background: rgba(0, 0, 0, 128);
            }
            QWidget#container {
                border: 2px solid #34495e;
                border-radius: 12px;
                background: white;
            }
            QLabel#title {
                font-size: 22pt;
                font-weight: bold;
                color: #2c3e50;
            }
            QPushButton#close {
                color: white;
                font-weight: bold;
                font-size: 14px;
                background-color: #e74c3c;
                border: none;
                border-radius: 15px;
                width: 30px;
                height: 30px;
            }
            QPushButton#close:hover {
                background-color: #c0392b;
            }
        ''')

        # Outer layout with transparent background
        full_layout = QtWidgets.QVBoxLayout(self)
        full_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QtWidgets.QWidget(objectName='container')
        full_layout.addStretch()
        full_layout.addWidget(self.container, alignment=Qt.AlignmentFlag.AlignCenter)
        full_layout.addStretch()

        self.container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Maximum
        )

        layout = QtWidgets.QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 20)
        layout.setSpacing(25)

        # --- Header Layout (Title + Close) ---
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QtWidgets.QLabel("Advanced Settings", objectName='title')
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.close_button = QtWidgets.QPushButton("X", objectName='close')
        self.close_button.clicked.connect(self.close)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.close_button)

        layout.addLayout(header_layout)

        # --- Power Optimization Settings ---
        self.setup_power_optimization_section(layout)

        # --- Apply Button ---
        apply_button = QtWidgets.QPushButton("Apply")
        apply_button.clicked.connect(self.apply_settings)
        apply_button.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)

        # Center the button using alignment
        layout.addWidget(apply_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        parent.installEventFilter(self)

    def setup_power_optimization_section(self, layout):
        """Setup the power optimization section with radio buttons and descriptions."""
        
        # Section title
        section_title = QtWidgets.QLabel("Power Optimization")
        section_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        layout.addWidget(section_title)

        # Description
        description = QtWidgets.QLabel(
            "Select the computational intensity level for the eye tracking algorithm. "
            "Lower power modes reduce CPU usage but may affect tracking precision.")
        description.setWordWrap(True)
        description.setStyleSheet("""
            font-size: 12px;
            color: #7f8c8d;
            margin-bottom: 15px;
            line-height: 1.3;
        """)
        layout.addWidget(description)

        # Power mode selection group
        power_group = QtWidgets.QGroupBox()
        power_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                background: #f8f9fa;
            }
        """)
        power_layout = QtWidgets.QVBoxLayout(power_group)
        power_layout.setSpacing(12)

        # Create radio buttons for power modes
        self.power_mode_group = QtWidgets.QButtonGroup()
        
        # Low Power Mode
        self.low_power_radio = QtWidgets.QRadioButton("Low Power Mode")
        self.low_power_radio.setStyleSheet("""
            QRadioButton {
                font-weight: bold;
                color: #27ae60;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        power_layout.addWidget(self.low_power_radio)
        
        low_power_desc = QtWidgets.QLabel("• Minimal CPU usage\n• Basic tracking algorithm\n• Recommended for older systems")
        low_power_desc.setStyleSheet("""
            font-size: 11px;
            color: #7f8c8d;
            margin-left: 25px;
            margin-bottom: 8px;
        """)
        power_layout.addWidget(low_power_desc)

        # Medium Power Mode
        self.medium_power_radio = QtWidgets.QRadioButton("Medium Power Mode")
        self.medium_power_radio.setStyleSheet("""
            QRadioButton {
                font-weight: bold;
                color: #f39c12;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        power_layout.addWidget(self.medium_power_radio)
        
        medium_power_desc = QtWidgets.QLabel("• Balanced performance and accuracy\n• Standard tracking algorithm\n• Recommended for most systems")
        medium_power_desc.setStyleSheet("""
            font-size: 11px;
            color: #7f8c8d;
            margin-left: 25px;
            margin-bottom: 8px;
        """)
        power_layout.addWidget(medium_power_desc)

        # High Power Mode
        self.high_power_radio = QtWidgets.QRadioButton("High Power Mode")
        self.high_power_radio.setStyleSheet("""
            QRadioButton {
                font-weight: bold;
                color: #e74c3c;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        power_layout.addWidget(self.high_power_radio)
        
        high_power_desc = QtWidgets.QLabel("• Maximum precision and features\n• Advanced tracking algorithm\n• Requires powerful hardware")
        high_power_desc.setStyleSheet("""
            font-size: 11px;
            color: #7f8c8d;
            margin-left: 25px;
            margin-bottom: 8px;
        """)
        power_layout.addWidget(high_power_desc)

        # Add radio buttons to button group
        self.power_mode_group.addButton(self.low_power_radio, 0)
        self.power_mode_group.addButton(self.medium_power_radio, 1)
        self.power_mode_group.addButton(self.high_power_radio, 2)

        # Set current selection
        self.set_current_power_mode(self.current_power_mode)

        layout.addWidget(power_group)

    def set_current_power_mode(self, mode):
        """Set the current power mode selection."""
        mode_map = {
            'low': self.low_power_radio,
            'medium': self.medium_power_radio,
            'high': self.high_power_radio
        }
        
        if mode in mode_map:
            mode_map[mode].setChecked(True)
            self.current_power_mode = mode

    def get_selected_power_mode(self):
        """Get the currently selected power mode."""
        if self.low_power_radio.isChecked():
            return 'low'
        elif self.medium_power_radio.isChecked():
            return 'medium'
        elif self.high_power_radio.isChecked():
            return 'high'
        return 'medium'  # Default fallback

    def apply_settings(self):
        selected_mode = self.get_selected_power_mode()
        if selected_mode != self.current_power_mode:
            self.power_mode_changed.emit(selected_mode)
            self.current_power_mode = selected_mode

        self.close()

    def showEvent(self, event):
        """Make popup fill the entire parent."""
        self.setGeometry(self.parent().rect())

    def resizeEvent(self, event):
        """Position close button at top-right of container."""
        if hasattr(self, 'close_button') and hasattr(self, 'container'):
            button_rect = self.close_button.rect()
            container_rect = self.container.rect()
            button_rect.moveTopRight(container_rect.topRight() + QtCore.QPoint(-10, 10))
            self.close_button.setGeometry(button_rect)

    def eventFilter(self, source, event):
        """Keep popup sized to match parent."""
        if event.type() == QtCore.QEvent.Type.Resize:
            self.setGeometry(source.rect())
        return super().eventFilter(source, event)