"""
Main application window for the EyeTracker application
"""
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QMessageBox, QStatusBar, QHBoxLayout,
    QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QFont, QPixmap, QGuiApplication

from gui.calibration_view import CalibrationView
from gui.test_view import TestView
from gui.results_view import ResultsView
from core.pupil_tracker import EyeTracker
from core.arduino_tracker import ArduinoTracker

from gui.widgets.help_popup import HelpPopup 

class MainWindow(QMainWindow):
    """Main application window for the EyeTracker application"""
    
    def __init__(self, config):
        super().__init__()
        
        self.config = config

        # Set Minimum Window Size
        screen_size = QGuiApplication.primaryScreen().availableGeometry()
        width = int(screen_size.width() * 0.9)
        height = int(screen_size.height() * 0.9)
        self.resize(width, height)

        # self.setMinimumSize(WIDTH, HEIGHT)
        
        # Define application color palette
        self.app_colors = {
            "primary": "#262e36",      # Dark blue for headers and main elements
            "secondary": "#6c6d74",    # Lighter blue for accent elements
            "success": "#b3b7ba",      # Green for success actions
            "warning": "#fdb440",      # Orange for warnings
            "danger": "#F20101",       # Red for critical actions
            "light": "#d3d1ce",        # Light gray for backgrounds
            "dark": "#090f15",         # Darker shade for text
            "white": "#ffffff",        # White for contrast elements
            "black": "#090f15"         # Black for text
        }
        
        self.setup_ui()
        
        # Initialize core components
        self.eye_tracker = None
        self.arduino_tracker = None
        
        # Setup connections and timers
        self.setup_connections()
        
        # Used to track application state
        self.is_connected = False
        self.is_test_running = False
        
        # Initialize with welcome screen
        self.show_welcome_view()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Set window properties
        self.setWindowTitle("EyeTracker - Visual Field Test Assistant")
        
        # Set application stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.app_colors["light"]};
            }}
            QLabel {{
                color: {self.app_colors["dark"]};
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {self.app_colors["secondary"]};
                color: {self.app_colors["white"]};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
            QStatusBar {{
                background-color: {self.app_colors["primary"]};
                color: {self.app_colors["white"]};
                font-weight: bold;
                min-height: 25px;
            }}
            QMenuBar {{
                background-color: {self.app_colors["primary"]};
                color: {self.app_colors["white"]};
            }}
            QMenuBar::item {{
                background-color: {self.app_colors["primary"]};
                color: {self.app_colors["white"]};
                padding: 8px 16px;
            }}
            QMenuBar::item:selected {{
                background-color: {self.app_colors["secondary"]};
            }}
            QMenu {{
                background-color: {self.app_colors["white"]};
                color: {self.app_colors["dark"]};
                border: 1px solid #bdc3c7;
            }}
            QMenu::item:selected {{
                background-color: {self.app_colors["secondary"]};
                color: {self.app_colors["white"]};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: {self.app_colors["primary"]};
            }}
        """)
        
        # Create central widget with stacked layout for different views
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create header frame
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(f"""
            background-color: {self.app_colors["primary"]};
            color: {self.app_colors["white"]};
            padding: 10px;
            min-height: 70px;
        """)
        self.header_layout = QHBoxLayout(self.header_frame)
        
        # Add logo (placeholder)
        self.logo_label = QLabel("EyeTracker")
        self.logo_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
        """)
        self.header_layout.addWidget(self.logo_label)
        
        # Add header text
        self.header_text = QLabel("Visual Field Test Assistant")
        self.header_text.setStyleSheet("""
            font-size: 18px;
            color: white;
            padding-left: 20px;
        """)
        self.header_layout.addWidget(self.header_text)
        self.header_layout.addStretch()
        
        # Add header to main layout
        self.main_layout.addWidget(self.header_frame)
        
        # Container for the stacked widget with margin
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget)
        
        # Add content container to main layout
        self.main_layout.addWidget(self.content_container)
        
        # Create the different views
        self.welcome_view = self.create_welcome_view()
        self.stacked_widget.addWidget(self.welcome_view)
        
        self.calibration_view = CalibrationView(self)
        self.stacked_widget.addWidget(self.calibration_view)
        
        self.test_view = TestView(self)
        self.stacked_widget.addWidget(self.test_view)
        
        self.results_view = ResultsView(self)
        self.stacked_widget.addWidget(self.results_view)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create menubar
        self.setup_menu()
    
    def setup_menu(self):
        """Create the menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # Connect to device action
        connect_action = QAction("&Connect Devices", self)
        connect_action.triggered.connect(self.connect_devices)
        file_menu.addAction(connect_action)
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_welcome_view(self):
        """Create the welcome view"""
        welcome_widget = QWidget()
        welcome_widget.setStyleSheet(f"""
            background-color: {self.app_colors["white"]};
            border-radius: 8px;
        """)
        
        layout = QVBoxLayout(welcome_widget)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(20)
        
        # Welcome container
        welcome_container = QFrame()
        welcome_container.setStyleSheet("""
            background-color: #f5f5f5;
            border-radius: 8px;
            padding: 20px;
        """)
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setSpacing(20)
        
        # Welcome Header with help button
        header_layout = QtWidgets.QHBoxLayout()
        
        # Welcome label
        welcome_label = QtWidgets.QLabel("Welcome to EyeTracker")
        welcome_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
            margin: 20px;
        """)
        header_layout.addWidget(welcome_label)
        
        # Help button
        help_button = QtWidgets.QPushButton("Help!")
        help_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        help_button.clicked.connect(self.show_help_popup)
        header_layout.addWidget(help_button, alignment=QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignRight)
        
        welcome_layout.addLayout(header_layout)
        # Description label
        description = (
            "This application assists in administering the Humphrey Visual Field Test "
            "by tracking patient eye position and movement.\n\n"
            "To begin, please connect your Arduino device and eye tracking camera."
        )
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 16px;
            color: #34495e;
            margin: 10px 30px;
            line-height: 1.5;
        """)
        welcome_layout.addWidget(desc_label)

        welcome_layout.addStretch()
        
        # Connect button
        connect_button = QPushButton("Connect Devices")
        connect_button.clicked.connect(self.connect_devices)
        connect_button.setMinimumHeight(50)
        connect_button.setStyleSheet(f"""
            background-color: {self.app_colors["success"]};
            font-size: 16px;
            padding: 12px;
        """)
        welcome_layout.addWidget(connect_button)
        
        layout.addWidget(welcome_container)     
        return welcome_widget

    def show_help_popup(self):
        """Show the help popup"""
        popup = HelpPopup(self)
        popup.show()
    
    def setup_connections(self):
        """Set up signal/slot connections"""
        # Will be implemented as more components are added
        pass
    
    def show_welcome_view(self):
        """Switch to welcome view"""
        self.header_text.setText("Visual Field Test Assistant")
        self.stacked_widget.setCurrentWidget(self.welcome_view)
    
    def show_calibration_view(self):
        """Switch to calibration view"""
        self.header_text.setText("Eye Position Calibration")
        self.stacked_widget.setCurrentWidget(self.calibration_view)
    
    def show_test_view(self):
        """Switch to test view"""
        self.header_text.setText("Visual Field Test")
        self.stacked_widget.setCurrentWidget(self.test_view)
    
    def show_results_view(self, results=None):
        """Switch to results view"""
        self.header_text.setText("Test Results")
        if results:
            self.results_view.set_results(results)
        self.stacked_widget.setCurrentWidget(self.results_view)
    
    def connect_devices(self):
        """Connect to Arduino and camera"""
        try:            
            # Show connecting message
            self.status_bar.showMessage("Connecting to devices...")
            
            # Initialize Arduino tracker with port selection callback
            self.arduino_tracker = ArduinoTracker(
                auto_connect=True,
                baud_rate=self.config['arduino']['baud_rate'],
                on_detect_callback=self.select_arduino_port,
                port_identifiers=self.config['arduino']['port_identifiers']
            )
            
            # Initialize eye tracker
            self.eye_tracker = EyeTracker(arduino_tracker=self.arduino_tracker)
            
            if self.arduino_tracker.is_connected():
                self.is_connected = True
                self.status_bar.showMessage("Connected to devices")
                self.show_calibration_view()
            else:
                # Arduino connection failed or was cancelled
                QMessageBox.warning(
                    self, 
                    "Connection Error", 
                    "Could not connect to Arduino device. Please check connections and try again."
                )
            self.show_calibration_view()
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred while connecting devices: {str(e)}"
            )
    
    def select_arduino_port(self, ports):
        pass
    #     """Show dialog to let user select the correct Arduino port
        
    #     Args:
    #         ports: List of available ports
            
    #     Returns:
    #         str: Selected port or None if canceled
    #     """
    #     from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
        
    #     dialog = QDialog(self)
    #     dialog.setWindowTitle("Select Arduino Port")
    #     dialog.setMinimumWidth(400)
    #     dialog.setStyleSheet(f"""
    #         QDialog {{
    #             background-color: {self.app_colors["white"]};
    #         }}
    #         QLabel {{
    #             color: {self.app_colors["dark"]};
    #             font-size: 14px;
    #             margin-bottom: 10px;
    #         }}
    #         QListWidget {{
    #             border: 1px solid #bdc3c7;
    #             border-radius: 4px;
    #             padding: 5px;
    #             background-color: {self.app_colors["white"]};
    #         }}
    #         QListWidget::item {{
    #             padding: 8px;
    #             border-bottom: 1px solid #ecf0f1;
    #         }}
    #         QListWidget::item:selected {{
    #             background-color: {self.app_colors["secondary"]};
    #             color: {self.app_colors["white"]};
    #         }}
    #         QPushButton {{
    #             background-color: {self.app_colors["secondary"]};
    #             color: {self.app_colors["white"]};
    #             border: none;
    #             padding: 8px 16px;
    #             border-radius: 4px;
    #             font-weight: bold;
    #         }}        
    #     """)
        
    #     layout = QVBoxLayout(dialog)
    #     layout.setContentsMargins(20, 20, 20, 20)
    #     layout.setSpacing(15)
        
    #     # Add helpful message
    #     message = QLabel("Multiple Arduino devices detected. Please select the correct port:")
    #     layout.addWidget(message)
        
    #     # Create list widget for port selection
    #     port_list = QListWidget()
    #     for port_info in ports:
    #         item = QListWidgetItem(f"{port_info['port']} - {port_info['description']}")
    #         item.setData(Qt.ItemDataRole.UserRole, port_info['port'])
    #         port_list.addWidget(item)
        
    #     layout.addWidget(port_list)
        
    #     # Add buttons
    #     buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    #     buttons.accepted.connect(dialog.accept)
    #     buttons.rejected.connect(dialog.reject)
    #     layout.addWidget(buttons)
        
    #     # Show dialog and process result
    #     if dialog.exec() == QDialog.DialogCode.Accepted:
    #         selected_items = port_list.selectedItems()
    #         if selected_items:
    #             return selected_items[0].data(Qt.ItemDataRole.UserRole)
        
    #     return None  # User canceled or no selection

    
    def start_test(self):
        """Start the vision test"""
        if not self.is_connected:
            QMessageBox.warning(
                self, 
                "Not Connected", 
                "Please connect to devices first."
            )
            return
        
        try:
            self.is_test_running = True
            self.show_test_view()
            self.status_bar.showMessage("Test in progress")
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred while starting the test: {str(e)}"
            )
    
    def end_test(self, results):
        """End the test and show results"""
        self.is_test_running = False
        self.status_bar.showMessage("Test completed")
        self.show_results_view(results)
    
    def show_about(self):
        """Show about dialog"""
        about_box = QMessageBox(self)
        about_box.setWindowTitle("About EyeTracker")
        about_box.setTextFormat(Qt.TextFormat.RichText)
        about_box.setText(
            "<h2>EyeTracker v1.0</h2>"
            "<p>A lightweight, robust eye-tracking system used as part of the "
            "pre-assessment preparation for patients undergoing the Humphrey Visual Field Test.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Real-time pupil detection and tracking</li>"
            "<li>Arduino integration for stimulus control</li>"
            "<li>Advanced calibration tools</li>"
            "<li>Comprehensive test results</li>"
            "</ul>"
        )
        about_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        about_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.app_colors["white"]};
            }}
            QPushButton {{
                background-color: {self.app_colors["secondary"]};
                color: {self.app_colors["white"]};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)
        about_box.exec()
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up resources
        if self.arduino_tracker and self.is_connected:
            try:
                self.arduino_tracker.disconnect()
            except:
                pass
        
        if self.eye_tracker:
            try:
                self.eye_tracker.release()
            except:
                pass
        
        event.accept()