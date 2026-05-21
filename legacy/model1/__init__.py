"""
UPbit Quantitative Trading Platform

A comprehensive quantitative trading platform for cryptocurrency markets.
"""

__version__ = "1.0.0"
__author__ = "UPbit Quant Team"
__email__ = "team@upbit-quant.com"

from .core.config import Config
from .core.logger import get_logger

# Initialize configuration and logger
config = Config()
logger = get_logger(__name__)

__all__ = ["config", "logger", "Config", "get_logger"]
