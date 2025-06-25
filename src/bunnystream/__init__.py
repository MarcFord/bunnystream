"""
Bunny Stream - A event system that uses RabbitMQ to handle events.

This package provides an easy-to-use interface for publishing and consuming events
using RabbitMQ. It is designed to be simple and efficient, allowing developers to
integrate event-driven architecture into their applications with minimal setup.
"""

# Dynamic version detection
try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("bunnystream")
except ImportError:
    # Python < 3.8
    try:
        from importlib_metadata import PackageNotFoundError, version  # type: ignore

        __version__ = version("bunnystream")
    except ImportError:
        __version__ = "0.0.1-dev"
except (PackageNotFoundError, Exception):  # pylint: disable=broad-exception-caught
    # Fallback for development mode or package not installed
    __version__ = "0.0.1-dev"

# Import main components
from .config import BunnyStreamConfig
from .exceptions import (
    BunnyStreamConfigurationError,
    BunnyStreamModeError,
    ExcangeNameError,
    InvalidTCPOptionsError,
    PrefetchCountError,
    RabbitCredentialsError,
    RabbitHostError,
    RabbitPortError,
    RabbitVHostError,
    SSLOptionsError,
    SubscriptionsNotSetError,
)
from .logger import bunny_logger, configure_bunny_logger, get_bunny_logger
from .subscription import Subscription
from .warren import Warren

# Define what gets imported with "from bunnystream import *"
__all__ = [
    "Warren",
    "BunnyStreamConfig",
    "Subscription",
    "bunny_logger",
    "get_bunny_logger",
    "configure_bunny_logger",
    "RabbitPortError",
    "RabbitHostError",
    "RabbitVHostError",
    "RabbitCredentialsError",
    "ExcangeNameError",
    "PrefetchCountError",
    "BunnyStreamModeError",
    "SSLOptionsError",
    "InvalidTCPOptionsError",
    "BunnyStreamConfigurationError",
    "SubscriptionsNotSetError",
    "__version__",
]
