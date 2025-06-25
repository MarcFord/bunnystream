"""
Logging configuration for the bunnystream package.
"""

import logging
import sys
from typing import Optional


def get_bunny_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the bunnystream package.

    Args:
        name (Optional[str]): Optional name suffix for the logger.
                             If provided, logger name will be 'bunnystream.{name}'
                             If None, returns the root bunnystream logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    if name:
        logger_name = f"bunnystream.{name}"
    else:
        logger_name = "bunnystream"

    return logging.getLogger(logger_name)


def configure_bunny_logger(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    handler: Optional[logging.Handler] = None,
) -> logging.Logger:
    """
    Configure the bunnystream logger with custom settings.

    Args:
        level (int): Logging level (default: logging.INFO)
        format_string (Optional[str]): Custom format string for log messages
        handler (Optional[logging.Handler]): Custom handler. If None, uses StreamHandler

    Returns:
        logging.Logger: Configured root bunnystream logger
    """
    logger = get_bunny_logger()

    # Remove existing handlers to avoid duplicates
    for existing_handler in logger.handlers[:]:
        logger.removeHandler(existing_handler)

    # Set up default format if none provided
    if format_string is None:
        format_string = "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"

    # Set up default handler if none provided
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)

    # Configure formatter and handler
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    # Add handler to logger
    logger.addHandler(handler)
    logger.setLevel(level)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


# Create the default bunny_logger instance
bunny_logger = get_bunny_logger()

# Configure with sensible defaults if not already configured
if not bunny_logger.handlers:
    configure_bunny_logger()
