"""
Main application window for the EyeTracker application
"""
from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from gui.calibration_view import CalibrationView
from gui.test_view import TestView
from gui.results_view import ResultsView
from core.pupil_tracker import EyeTracker
from core.arduino_tracker import ArduinoTracker


class MainWindow(QMainWindow):
    """Main application window for the EyeTracker application"""
    
    def __init__(self, config):
        super().__init__()
        
        self.config = config
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
        self.setWindowTitle("EyeTracker")
        self.setMinimumSize(800, 600)
        
        # Create central widget with stacked layout for different views
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
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
        layout = QVBoxLayout(welcome_widget)
        
        # Welcome label
        welcome_label = QLabel("Welcome to EyeTracker")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(welcome_label)
        
        # Description label
        description = (
            "This application helps administer the Humphrey Visual Field Test.\n\n"
            "Please connect your Arduino device and eye tracking camera, then click 'Connect Devices'."
        )
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Connect button
        connect_button = QPushButton("Connect Devices")
        connect_button.clicked.connect(self.connect_devices)
        connect_button.setMinimumHeight(50)
        layout.addWidget(connect_button)
        
        layout.addStretch()
        
        return welcome_widget
    
    def setup_connections(self):
        """Set up signal/slot connections"""
        # Will be implemented as more components are added
        pass
    
    def show_welcome_view(self):
        """Switch to welcome view"""
        self.stacked_widget.setCurrentWidget(self.welcome_view)
    
    def show_calibration_view(self):
        """Switch to calibration view"""
        self.stacked_widget.setCurrentWidget(self.calibration_view)
    
    def show_test_view(self):
        """Switch to test view"""
        self.stacked_widget.setCurrentWidget(self.test_view)
    
    def show_results_view(self, results=None):
        """Switch to results view"""
        if results:
            self.results_view.set_results(results)
        self.stacked_widget.setCurrentWidget(self.results_view)
    
    def connect_devices(self):
        """Connect to Arduino and camera"""
        try:            
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
            # else:
            #     # Arduino connection failed or was cancelled
            #     QMessageBox.warning(
            #         self, 
            #         "Connection Error", 
            #         "Could not connect to Arduino device. Please check connections and try again."
            #     )
            self.show_calibration_view()
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred while connecting devices: {str(e)}"
            )
    
    def select_arduino_port(self, ports):
        """Show dialog to let user select the correct Arduino port
        
        Args:
            ports: List of available ports
            
        Returns:
            str: Selected port or None if canceled
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Arduino Port")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Add helpful message
        message = QLabel("Multiple Arduino devices detected. Please select the correct port:")
        layout.addWidget(message)
        
        # Create list widget for port selection
        port_list = QListWidget()
        for port_info in ports:
            item = QListWidgetItem(f"{port_info['port']} - {port_info['description']}")
            item.setData(Qt.ItemDataRole.UserRole, port_info['port'])
            port_list.addWidget(item)
        
        layout.addWidget(port_list)
        
        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show dialog and process result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = port_list.selectedItems()
            if selected_items:
                return selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        return None  # User canceled or no selection

    
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
            self.arduino_tracker.start_test()
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
        QMessageBox.about(
            self,
            "About EyeTracker",
            "EyeTracker v1.0\n\n"
            "A lightweight, robust eye-tracking system used as part of the "
            "pre-assessment preparation for patients undergoing the Humphrey Visual Field Test."
        )
    
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