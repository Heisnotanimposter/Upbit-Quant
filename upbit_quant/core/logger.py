"""
Logging configuration for UPbit Quantitative Trading Platform.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger as loguru_logger
from .config import config


class LoggerConfig:
    """Logger configuration class."""
    
    def __init__(self):
        self.config = config
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger configuration."""
        # Remove default handler
        loguru_logger.remove()
        
        # Console handler
        loguru_logger.add(
            sys.stdout,
            level=self.config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )
        
        # File handler
        log_file_path = Path(self.config.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        loguru_logger.add(
            log_file_path,
            level=self.config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
        )
        
        # Error file handler
        error_log_file = log_file_path.parent / "error.log"
        loguru_logger.add(
            error_log_file,
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
        )
    
    def get_logger(self, name: str) -> Any:
        """Get logger instance."""
        return loguru_logger.bind(name=name)


def get_logger(name: Optional[str] = None) -> Any:
    """Get logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    if name is None:
        name = __name__
    
    return loguru_logger.bind(name=name)


def setup_logging() -> None:
    """Setup logging configuration."""
    logger_config = LoggerConfig()
    logger = get_logger(__name__)
    logger.info("Logging system initialized")


# Initialize logging
setup_logging()
