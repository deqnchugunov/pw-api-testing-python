import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class CustomFormatter(logging.Formatter):
    """Custom log formatter with colors"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_str = "%(asctime)s [%(service)s] %(levelname)s: %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class Logger:
    """Logger class for API testing"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger("pw_api_testing")
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(CustomFormatter())
            self.logger.addHandler(console_handler)
            
            # File handler for all logs
            file_handler = logging.FileHandler(
                logs_dir / f"api_tests_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s [%(service)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Error file handler
            error_handler = logging.FileHandler(logs_dir / "errors.log")
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            self.logger.addHandler(error_handler)
        
        self._initialized = True
    
    def _get_extra(self, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get extra fields for log record"""
        extra_dict = {"service": "pw-api-testing"}
        if extra:
            extra_dict.update(extra)
        return extra_dict
    
    def info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message"""
        self.logger.info(message, extra=self._get_extra(extra))
    
    def error(self, message: str, extra: Dict[str, Any] = None):
        """Log error message"""
        self.logger.error(message, extra=self._get_extra(extra))
    
    def warning(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message"""
        self.logger.warning(message, extra=self._get_extra(extra))
    
    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message"""
        self.logger.debug(message, extra=self._get_extra(extra))
    
    def http(self, message: str, extra: Dict[str, Any] = None):
        """Log HTTP message"""
        self.logger.info(f"HTTP: {message}", extra=self._get_extra(extra))


# Singleton instance
logger = Logger()