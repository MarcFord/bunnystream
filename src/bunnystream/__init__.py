"""
BunnyStream: High-Performance RabbitMQ Event Streaming Library.

BunnyStream is a comprehensive Python library for building robust, event-driven
applications using RabbitMQ. It provides intuitive APIs for publishing and consuming
events with automatic connection management, error handling, and monitoring capabilities.

Key Features:
    - Simple, intuitive API for event publishing and consumption
    - Automatic RabbitMQ connection and channel management
    - Built-in support for quorum queues and high availability
    - Comprehensive error handling and logging
    - Environment-based configuration
    - SSL/TLS support for secure connections
    - Connection health monitoring and status reporting
    - Type-safe event handling with BaseEvent classes

Core Components:
    Warren: Connection and messaging management
    BunnyStreamConfig: Configuration management with environment support
    BaseEvent: Type-safe event publishing base class
    BaseReceivedEvent: Convenient event consumption with attribute access
    Subscription: Queue and exchange configuration

Quick Start Examples:

    Publishing Events:
        >>> from bunnystream import Warren, BunnyStreamConfig, BaseEvent
        >>>
        >>> # Simple message publishing
        >>> config = BunnyStreamConfig(mode="producer")
        >>> warren = Warren(config)
        >>> warren.connect()
        >>> warren.publish("Hello World", "events", "test.message")
        >>>
        >>> # Type-safe event publishing
        >>> class UserEvent(BaseEvent):
        ...     EXCHANGE = "user_events"
        ...     TOPIC = "user.created"
        ...
        >>> event = UserEvent({"user_id": 123, "email": "user@example.com"})
        >>> event.fire(warren)

    Consuming Events:
        >>> from bunnystream import Warren, BunnyStreamConfig, BaseReceivedEvent
        >>>
        >>> # Simple message consumption
        >>> def process_message(channel, method, properties, body):
        ...     print(f"Received: {body.decode()}")
        ...
        >>> config = BunnyStreamConfig(mode="consumer")
        >>> warren = Warren(config)
        >>> warren.connect()
        >>> warren.start_consuming(process_message)
        >>>
        >>> # Type-safe event consumption
        >>> def process_user_event(channel, method, properties, body):
        ...     event = BaseReceivedEvent(body)
        ...     print(f"User {event.user_id} created with email {event.email}")

    Connection Monitoring:
        >>> warren = Warren(config)
        >>> print(f"Connected: {warren.is_connected}")
        >>> print(f"Status: {warren.connection_status}")
        >>>
        >>> # Detailed connection information
        >>> info = warren.get_connection_info()
        >>> print(f"Host: {info['host']}, Has Channel: {info['has_channel']}")

    Environment Configuration:
        >>> import os
        >>> os.environ['RABBITMQ_URL'] = 'amqp://user:pass@rabbit.example.com:5672/'
        >>> config = BunnyStreamConfig()  # Auto-configures from environment
        >>> warren = Warren(config)

    SSL/TLS Connections:
        >>> import ssl
        >>> config = BunnyStreamConfig(
        ...     rabbit_host="secure.rabbit.example.com",
        ...     ssl=True,
        ...     ssl_port=5671,
        ...     ssl_options={
        ...         'cert_reqs': ssl.CERT_REQUIRED,
        ...         'ca_certs': '/path/to/ca_bundle.crt'
        ...     }
        ... )

    Custom Subscriptions:
        >>> from bunnystream import Subscription
        >>> from pika.exchange_type import ExchangeType
        >>>
        >>> subscription = Subscription(
        ...     exchange_name="orders",
        ...     exchange_type=ExchangeType.topic,
        ...     topic="order.*"
        ... )
        >>> config = BunnyStreamConfig(
        ...     mode="consumer",
        ...     subscriptions=[subscription]
        ... )

Environment Variables:
    BunnyStream supports configuration via environment variables:

    Connection Settings:
        RABBITMQ_URL: Complete connection string (overrides individual settings)
        RABBIT_HOST: RabbitMQ hostname (default: localhost)
        RABBIT_PORT: RabbitMQ port (default: 5672)
        RABBIT_USER: Username (default: guest)
        RABBIT_PASS: Password (default: guest)
        RABBIT_VHOST: Virtual host (default: /)

    SSL Settings:
        RABBIT_SSL: Enable SSL (true/false, default: false)
        RABBIT_SSL_PORT: SSL port (default: 5671)

    Advanced Settings:
        RABBIT_CHANNEL_MAX: Max channels per connection (default: 2047)
        RABBIT_FRAME_MAX: Max frame size (default: 131072)
        RABBIT_HEARTBEAT: Heartbeat interval in seconds (default: 600)
        RABBIT_PREFETCH_COUNT: Consumer prefetch count (default: 1)

Error Handling:
    BunnyStream provides specific exception types for different error conditions:

    >>> from bunnystream import (
    ...     BunnyStreamConfigurationError,  # Configuration errors
    ...     WarrenNotConnected,             # Connection not available
    ...     RabbitHostError,                # Invalid host
    ...     RabbitPortError,                # Invalid port
    ...     # ... other specific exceptions
    ... )
    >>>
    >>> try:
    ...     warren.publish("message", "exchange", "topic")
    ... except WarrenNotConnected:
    ...     print("Not connected to RabbitMQ")
    ... except BunnyStreamConfigurationError as e:
    ...     print(f"Configuration error: {e}")

Logging:
    BunnyStream includes comprehensive logging support:

    >>> from bunnystream import configure_bunny_logger, get_bunny_logger
    >>>
    >>> # Configure logging for the entire package
    >>> configure_bunny_logger(level="DEBUG")
    >>>
    >>> # Get logger for specific component
    >>> logger = get_bunny_logger("my_app")
    >>> logger.info("Application starting")

Best Practices:
    1. Use type-safe BaseEvent classes for publishing
    2. Use BaseReceivedEvent for convenient message consumption
    3. Monitor connection health with warren.is_connected
    4. Handle specific exceptions appropriately
    5. Use environment variables for configuration
    6. Enable logging for debugging and monitoring
    7. Use quorum queues for high availability (automatic)
    8. Implement proper error handling and retries

Performance Tips:
    - Reuse Warren instances when possible
    - Use appropriate prefetch_count for consumers
    - Monitor queue depths and consumer lag
    - Consider connection pooling for high-throughput apps
    - Use batch publishing for better performance

Thread Safety:
    Warren instances are not thread-safe. Use separate instances for different
    threads or implement appropriate synchronization.

Version: {version}

See Also:
    - RabbitMQ documentation: https://www.rabbitmq.com/documentation.html
    - Pika documentation: https://pika.readthedocs.io/
    - GitHub repository: [Your repository URL]
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
from .events import BaseEvent, BaseReceivedEvent, DataObject
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
    "BaseEvent",
    "BaseReceivedEvent",
    "DataObject",
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
