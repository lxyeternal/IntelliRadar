"""
Logging configuration for the downloader module
"""
import os
import sys
from loguru import logger
from pathlib import Path


def setup_downloader_logger(log_dir: str = None):
    """
    Configure logger for downloader module
    
    Args:
        log_dir: Directory to store log files. Defaults to /app/logs
    """
    # Remove default handler
    logger.remove()
    
    # Determine log directory
    if log_dir is None:
        # Default to /app/logs in Docker, or ./logs locally
        if os.path.exists('/app'):
            log_dir = '/app/logs'
        else:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    
    # Create log directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Console handler - only show INFO and above
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # File handler - detailed logs with rotation
    log_file = os.path.join(log_dir, "downloader.log")
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress rotated logs
        encoding="utf-8"
    )
    
    # Error file handler - separate file for errors
    error_log_file = os.path.join(log_dir, "downloader_errors.log")
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="60 days",  # Keep error logs longer
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info(f"Downloader logger initialized. Logs directory: {log_dir}")
    return logger


# Initialize logger when module is imported
downloader_logger = setup_downloader_logger()

