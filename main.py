"""
EyeTracker - Main Application Entry Point
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication

from app.gui.main_window import MainWindow
from app.utils.config import load_config
from app.utils.logger import setup_logger


def main():
    """Main application entry point"""
    # Set application metadata
    QCoreApplication.setOrganizationName("EyeTracker")
    QCoreApplication.setApplicationName("EyeTracker")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Setup logger
    logger = setup_logger()
    logger.info("Starting EyeTracker application")
    
    # Load configuration
    config = load_config()
    
    # Create and show the main window
    main_window = MainWindow(config)
    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()