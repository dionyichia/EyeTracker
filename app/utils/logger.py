"""
Logger utilities for the EyeTracker application
"""
import os
import logging
import logging.handlers
import sys
from datetime import datetime


def get_log_dir():
    """Get the directory for log files"""
    # Platform-specific log directory
    if os.name == 'nt':  # Windows
        log_dir = os.path.join(os.environ['APPDATA'], 'EyeTracker', 'logs')
    else:  # macOS, Linux
        log_dir = os.path.join(os.path.expanduser('~'), '.config', 'eyetracker', 'logs')
    
    # Create directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    return log_dir


def setup_logger(level=logging.INFO):
    """Set up the application logger
    
    Args:
        level: Logging level (default: logging.INFO)
    
    Returns:
        Logger: Configured logger instance
    """
    logger = logging.getLogger('eyetracker')
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates when reloading
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler with rotation
    log_dir = get_log_dir()
    log_file = os.path.join(log_dir, f'eyetracker_{datetime.now().strftime("%Y-%m-%d")}.log')
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Log system info at startup
    logger.info("-------------- EyeTracker Started --------------")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    
    return logger


def get_logger():
    """Get the application logger
    
    Returns:
        Logger: Application logger instance
    """
    logger = logging.getLogger('eyetracker')
    
    # If logger hasn't been set up yet, set it up
    if not logger.handlers:
        logger = setup_logger()
    
    return logger


class LoggingContext:
    """Context manager for temporary logging level changes"""
    
    def __init__(self, logger, level=None):
        self.logger = logger
        self.level = level
        self.old_level = logger.level
    
    def __enter__(self):
        if self.level is not None:
            self.logger.setLevel(self.level)
        return self.logger
    
    def __exit__(self, et, ev, tb):
        self.logger.setLevel(self.old_level)


def log_exception(exc_info=True):
    """Log an exception with traceback"""
    logger = get_logger()
    logger.error("An exception occurred", exc_info=exc_info)


def create_status_handler(status_bar):
    """Create a logging handler that updates a status bar
    
    Args:
        status_bar: PyQt status bar widget
    
    Returns:
        Handler: Logging handler for status bar
    """
    class StatusBarHandler(logging.Handler):
        def __init__(self, status_bar):
            super().__init__()
            self.status_bar = status_bar
        
        def emit(self, record):
            msg = self.format(record)
            self.status_bar.showMessage(msg, 5000)  # Show for 5 seconds
    
    handler = StatusBarHandler(status_bar)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    return handler