"""
Warren: RabbitMQ Connection and Configuration Management Module.

This module provides the Warren class, which serves as the primary interface for
managing RabbitMQ connections, channels, and messaging operations in BunnyStream.
Warren handles both producer and consumer patterns with automatic resource
management and comprehensive connection monitoring.

The module implements:
    - Asynchronous RabbitMQ connection handling via pika
    - Automatic queue and exchange declaration
    - Connection status monitoring and health checks
    - Robust error handling and logging
    - Support for SSL/TLS connections
    - Environment-based configuration

Classes:
    Warren: Main connection and messaging management class

Dependencies:
    - pika: RabbitMQ client library
    - bunnystream.config: Configuration management
    - bunnystream.exceptions: Custom exception classes
    - bunnystream.logger: Logging utilities

Examples:
    Quick Start - Producer:
        >>> from bunnystream import BunnyStreamConfig, Warren
        >>> config = BunnyStreamConfig(mode="producer")
        >>> warren = Warren(config)
        >>> warren.connect()
        >>> warren.publish("Hello World", "my_exchange", "my.topic")

    Quick Start - Consumer:
        >>> def process_message(channel, method, properties, body):
        ...     print(f"Got: {body.decode()}")
        ...
        >>> config = BunnyStreamConfig(mode="consumer")
        >>> warren = Warren(config)
        >>> warren.connect()
        >>> warren.start_consuming(process_message)

    Connection Monitoring:
        >>> if warren.is_connected:
        ...     print("RabbitMQ is available")
        ... else:
        ...     print(f"Status: {warren.connection_status}")

Environment Variables:
    The Warren class respects these environment variables through BunnyStreamConfig:

    RABBITMQ_URL: Complete connection string (amqp://user:pass@host:port/vhost)
    RABBIT_HOST: RabbitMQ server hostname (default: localhost)
    RABBIT_PORT: RabbitMQ server port (default: 5672)
    RABBIT_USER: Username for authentication (default: guest)
    RABBIT_PASS: Password for authentication (default: guest)
    RABBIT_VHOST: Virtual host (default: /)

    Advanced options:
    RABBIT_CHANNEL_MAX: Maximum channels per connection
    RABBIT_FRAME_MAX: Maximum frame size
    RABBIT_HEARTBEAT: Heartbeat interval
    RABBIT_SSL: Enable SSL (true/false)
    RABBIT_SSL_PORT: SSL port (default: 5671)

Thread Safety:
    Warren is not thread-safe. Create separate instances for different threads
    or use appropriate synchronization mechanisms.

Performance Notes:
    - Use connection pooling for high-throughput applications
    - Consider batch publishing for better performance
    - Monitor queue depths and consumer lag
    - Tune prefetch_count for optimal consumer performance
"""

from typing import Any, Callable, Optional, Union

import pika  # type: ignore
from pika.exchange_type import ExchangeType  # type: ignore

from bunnystream.config import BunnyStreamConfig
from bunnystream.exceptions import BunnyStreamConfigurationError, WarrenNotConnected
from bunnystream.logger import get_bunny_logger


class Warren:
    """
    Warren: Advanced RabbitMQ Connection and Message Management System.

    The Warren class is the core component of BunnyStream that manages RabbitMQ
    connections, channels, and messaging operations. It provides a high-level
    interface for both producing and consuming messages with automatic resource
    management, connection monitoring, and robust error handling.

    Key Features:
        - Asynchronous RabbitMQ connection management
        - Automatic queue declaration with quorum support
        - Connection status monitoring and health checks
        - Support for both producer and consumer modes
        - Comprehensive error handling and logging
        - Environment variable configuration support
        - SSL/TLS connection support

    Connection States:
        The Warren instance can be in one of three connection states:
        - 'not_initialized': No connection attempt made
        - 'disconnected': Connection exists but is closed
        - 'connected': Active connection to RabbitMQ

    Attributes:
        config (BunnyStreamConfig): Configuration object containing RabbitMQ parameters
        logger: Instance logger for debugging and monitoring
        is_connected (bool): True if actively connected to RabbitMQ
        connection_status (str): Human-readable connection state
        rabbit_connection: The underlying pika connection object
        bunny_mode (str): Current operating mode ('producer' or 'consumer')

    Examples:
        Basic Producer Setup:
            >>> from bunnystream import BunnyStreamConfig, Warren
            >>> config = BunnyStreamConfig(mode="producer")
            >>> warren = Warren(config)
            >>> warren.connect()
            >>> warren.start_io_loop()

        Basic Consumer Setup:
            >>> def message_handler(channel, method, properties, body):
            ...     print(f"Received: {body.decode()}")
            ...
            >>> config = BunnyStreamConfig(mode="consumer")
            >>> warren = Warren(config)
            >>> warren.connect()
            >>> warren.start_consuming(message_handler)
            >>> warren.start_io_loop()

        Connection Monitoring:
            >>> warren = Warren(config)
            >>> print(f"Connected: {warren.is_connected}")
            >>> print(f"Status: {warren.connection_status}")
            >>> info = warren.get_connection_info()
            >>> print(f"Host: {info['host']}, Port: {info['port']}")

        Publishing Messages:
            >>> warren.publish(
            ...     message='{"user_id": 123, "action": "login"}',
            ...     exchange="user_events",
            ...     topic="user.login"
            ... )

        Environment Configuration:
            >>> import os
            >>> os.environ['RABBITMQ_URL'] = 'amqp://user:pass@localhost:5672/vhost'
            >>> config = BunnyStreamConfig()  # Automatically reads env vars
            >>> warren = Warren(config)

        SSL Connection:
            >>> config = BunnyStreamConfig(
            ...     rabbit_host="secure.rabbitmq.com",
            ...     rabbit_port=5671,
            ...     ssl=True,
            ...     ssl_options={
            ...         'cert_reqs': ssl.CERT_REQUIRED,
            ...         'ca_certs': '/path/to/ca_bundle.crt'
            ...     }
            ... )
            >>> warren = Warren(config)

        Custom Subscription with Quorum Queues:
            >>> from bunnystream import Subscription
            >>> from pika.exchange_type import ExchangeType
            >>>
            >>> subscription = Subscription(
            ...     exchange_name="orders",
            ...     exchange_type=ExchangeType.topic,
            ...     topic="order.created"
            ... )
            >>> config = BunnyStreamConfig(
            ...     mode="consumer",
            ...     subscriptions=[subscription]
            ... )
            >>> warren = Warren(config)
            >>> # Queues are automatically declared with x-queue-type=quorum

        Error Handling:
            >>> try:
            ...     warren.connect()
            ...     warren.publish("test", "exchange", "topic")
            ... except WarrenNotConnected as e:
            ...     print(f"Connection error: {e}")
            ... except BunnyStreamConfigurationError as e:
            ...     print(f"Configuration error: {e}")

        Connection Lifecycle Management:
            >>> warren = Warren(config)
            >>> warren.connect()  # Establish connection
            >>> warren.start_io_loop()  # Start event loop (blocking)
            >>> # In another thread/process:
            >>> warren.stop_io_loop()  # Stop event loop
            >>> warren.disconnect()  # Close connection

    Notes:
        - Warren uses pika's SelectConnection for asynchronous operations
        - All queues are declared with 'x-queue-type=quorum' for high availability
        - Connection parameters support all pika ConnectionParameters options
        - The IO loop is blocking and should be run in a separate thread for non-blocking apps
        - Connection callbacks handle automatic reconnection scenarios
        - Message acknowledgment is handled automatically in consumer mode

    Raises:
        BunnyStreamConfigurationError: Invalid configuration parameters
        WarrenNotConnected: Operations attempted without active connection

    See Also:
        BunnyStreamConfig: Configuration management class
        Subscription: Queue subscription configuration
        BaseEvent: Event publishing base class
        BaseReceivedEvent: Event consumption helper class
    """

    def __init__(self, config: BunnyStreamConfig):
        """
        Initialize Warren with RabbitMQ connection parameters.

        Args:
            config (BunnyStreamConfig): Configuration object containing
                BunnyStream parameters.
        """
        self._rabbit_connection = None
        self._config = config
        self._channel = None
        self._consumer_tag = None
        self._consumer_callback: Optional[Callable] = None

        # Initialize logger for this instance
        self.logger = get_bunny_logger("warren")

    @property
    def config(self) -> BunnyStreamConfig:
        """
        Returns the BunnyStream configuration object.

        This property is used to access the BunnyStream configuration
        parameters such as RabbitMQ connection details and other settings.

        Returns:
            BunnyStreamConfig: The current BunnyStream configuration.
        """
        return self._config

    @config.setter
    def config(self, value: BunnyStreamConfig) -> None:
        """
        Sets the BunnyStream configuration object.

        Args:
            value (BunnyStreamConfig): The new BunnyStream configuration to set.

        Raises:
            BunnyStreamConfigurationError: If the provided value is not a valid
                BunnyStreamConfig instance.
        """
        if not isinstance(value, BunnyStreamConfig):
            raise BunnyStreamConfigurationError(
                "Configuration must be an instance of BunnyStreamConfig."
            )
        self.logger.debug("Setting new BunnyStream configuration.")
        self._config = value

    @property
    def bunny_mode(self) -> str:
        """
        Returns the current BunnyStream mode.

        This property is used to determine the mode of operation for the
        BunnyStream instance, which can be either 'producer' or 'consumer'.

        Returns:
            str: The current BunnyStream mode.
        """
        return self.config.mode

    @bunny_mode.setter
    def bunny_mode(self, value: str) -> None:
        """
        Sets the BunnyStream mode.

        Args:
            value (str): The mode to set, either 'producer' or 'consumer'.

        Raises:
            BunnyStreamModeError: If the provided value is not a valid mode.

        Side Effects:
            Updates the internal _bunny_mode attribute.
        """
        self.config.mode = value

    @property
    def rabbit_connection(self) -> Optional[pika.SelectConnection]:
        """
        Returns the RabbitMQ connection object.

        This property is used to access the RabbitMQ connection instance.
        If the connection is not established, it will return None.

        Returns:
            Optional: The RabbitMQ connection object or None if not connected.
        """
        return self._rabbit_connection

    @property
    def is_connected(self) -> bool:
        """
        Returns True if connected to RabbitMQ, False otherwise.

        This property checks if there is an active RabbitMQ connection
        that is open and not closed.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._rabbit_connection is not None and not self._rabbit_connection.is_closed

    @property
    def connection_status(self) -> str:
        """
        Returns the current connection status as a string.

        This property provides a human-readable description of the current
        connection state to RabbitMQ.

        Returns:
            str: Connection status - 'connected', 'disconnected', or 'not_initialized'.
        """
        if self._rabbit_connection is None:
            return "not_initialized"
        if self._rabbit_connection.is_closed:
            return "disconnected"
        return "connected"

    def get_connection_info(self) -> dict:
        """
        Returns detailed information about the current RabbitMQ connection.

        This method provides comprehensive information about the connection
        state, including connection parameters and channel status.

        Returns:
            dict: Dictionary containing connection information including:
                - status: Current connection status
                - host: RabbitMQ host
                - port: RabbitMQ port
                - virtual_host: RabbitMQ virtual host
                - username: RabbitMQ username
                - has_channel: Whether a channel is available
                - mode: Current Warren mode (producer/consumer)
        """
        return {
            "status": self.connection_status,
            "is_connected": self.is_connected,
            "host": self.config.rabbit_host,
            "port": self.config.rabbit_port,
            "virtual_host": self.config.rabbit_vhost,
            "username": self.config.rabbit_user,
            "has_channel": self._channel is not None,
            "mode": self.config.mode,
            "connection_object": self._rabbit_connection is not None,
        }

    @property
    def connection_parameters(self) -> pika.ConnectionParameters:
        """
        Constructs and returns the connection parameters for RabbitMQ.

        This property creates a pika.ConnectionParameters object using the
        current RabbitMQ configuration, including host, port, virtual host,
        and credentials.

        Returns:
            pika.ConnectionParameters: The connection parameters for RabbitMQ.
        """
        return pika.ConnectionParameters(
            host=self.config.rabbit_host,
            port=self.config.rabbit_port,
            virtual_host=self.config.rabbit_vhost,
            credentials=pika.PlainCredentials(
                username=self.config.rabbit_user, password=self.config.rabbit_pass
            ),
            channel_max=self.config.channel_max,
            frame_max=self.config.frame_max,
            heartbeat=self.config.heartbeat,
            blocked_connection_timeout=self.config.blocked_connection_timeout,
            ssl_options=self.config.ssl_options,
            retry_delay=self.config.retry_delay,
            connection_attempts=self.config.connection_attempts,
            tcp_options=self.config.tcp_options,
            locale=self.config.locale,
            socket_timeout=self.config.socket_timeout,
            stack_timeout=self.config.stack_timeout,
        )

    def connect(self) -> None:
        """
        Establishes a connection to the RabbitMQ server.

        This method creates a new RabbitMQ connection using the provided
        parameters and sets up the necessary callbacks for connection events.
        It uses pika's SelectConnection for asynchronous operations.
        """
        if self._rabbit_connection is None:
            self.logger.debug("Using asynchronous RabbitMQ connection.")
            self._rabbit_connection = pika.SelectConnection(
                parameters=self.connection_parameters,
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_error,
                on_close_callback=self.on_connection_closed,
            )

    def on_connection_open(self, connection: pika.SelectConnection) -> None:
        """
        Callback when the RabbitMQ connection is opened.

        Args:
            connection (pika.SelectConnection): The opened RabbitMQ connection.
        """
        self.logger.info("RabbitMQ connection opened successfully.")
        # Open a channel when the connection opens
        connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel: Any) -> None:
        """
        Callback when the RabbitMQ channel is opened.

        Args:
            channel: The opened RabbitMQ channel.
        """
        self.logger.info("RabbitMQ channel opened successfully.")
        self._channel = channel

        # Set up channel based on mode
        if self.config.mode == "consumer":
            self._setup_consumer()
        elif self.config.mode == "producer":
            self._setup_producer()

    def _setup_producer(self) -> None:
        """Setup channel for producer mode."""
        if self._channel is None:
            raise WarrenNotConnected("Channel not available")

        # Declare exchanges and queues based on subscriptions
        for subscription in self.config.subscriptions:
            self._declare_consumer_resources(subscription)
        self.logger.debug("Producer setup completed")

    def _setup_consumer(self) -> None:
        """Setup channel for consumer mode."""
        if self._channel is None:
            raise WarrenNotConnected("Channel not available")

        self._channel.basic_qos(prefetch_count=self.config.prefetch_count)

        # Declare exchanges and queues based on subscriptions
        for subscription in self.config.subscriptions:
            self._declare_consumer_resources(subscription)

        self.logger.debug("Consumer setup completed")

    def _declare_consumer_resources(self, subscription: Any) -> None:
        """Declare exchange, queue, and bindings for a subscription."""
        if self._channel is None:
            raise WarrenNotConnected("Channel not available")

        # Declare exchange
        self._channel.exchange_declare(
            exchange=subscription.exchange_name,
            exchange_type=subscription.exchange_type,
            durable=True,
        )

        # Declare queue with quorum type
        queue_name = f"{subscription.exchange_name}.{subscription.topic}"
        self._channel.queue_declare(
            queue=queue_name, durable=True, arguments={"x-queue-type": "quorum"}
        )

        # Bind queue to exchange
        self._channel.queue_bind(
            exchange=subscription.exchange_name,
            queue=queue_name,
            routing_key=subscription.topic,
        )

        self.logger.debug(
            "Declared resources for exchange=%s, queue=%s, topic=%s",
            subscription.exchange_name,
            queue_name,
            subscription.topic,
        )

    def on_connection_error(self, _connection: pika.SelectConnection, error: Exception) -> None:
        """
        Callback when there is an error opening the RabbitMQ connection.

        Args:
            connection (pika.SelectConnection): The RabbitMQ connection.
            error (Exception): The error that occurred.
        """
        self.logger.error("Error opening RabbitMQ connection: %s", str(error))
        self._rabbit_connection = None

    def on_connection_closed(
        self, _connection: pika.SelectConnection, reason: Union[str, None]
    ) -> None:
        """
        Callback when the RabbitMQ connection is closed.

        Args:
            connection (pika.SelectConnection): The RabbitMQ connection.
            reason (Union[str, None]): The reason for the closure.
        """
        self.logger.warning("RabbitMQ connection closed: %s", reason)
        self._rabbit_connection = None

    def publish(
        self,
        message: str,
        exchange: str,
        topic: str,
        exchange_type: ExchangeType = ExchangeType.topic,
    ) -> None:
        """
        Publishes a message to the specified exchange and topic.

        Args:
            message (str): The message to publish.
            exchange (str): The name of the exchange to publish to.
            topic (str): The routing key for the message.
            exchange_type (ExchangeType): The type of the exchange.

        Raises:
            WarrenNotConnected: If the channel is not available for publishing.
        """
        if self._channel is None:
            raise WarrenNotConnected("Cannot publish, channel not available.")

        self.logger.debug("Publishing message to exchange '%s' with topic '%s'", exchange, topic)
        self._channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=True)

        self._channel.basic_publish(
            exchange=exchange,
            routing_key=topic,
            body=message,
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )

    def start_consuming(self, message_callback: Callable) -> None:
        """
        Start consuming messages from queues.

        Args:
            message_callback (Callable): Function to call when a message is received.
                Should accept (channel, method, properties, body) arguments.

        Raises:
            WarrenNotConnected: If not connected to RabbitMQ.
            BunnyStreamConfigurationError: If not in consumer mode.
        """
        if self._channel is None:
            raise WarrenNotConnected("Cannot start consuming, channel not available.")

        if self.config.mode != "consumer":
            raise BunnyStreamConfigurationError(
                "Warren must be in 'consumer' mode to start consuming messages."
            )

        self._consumer_callback = message_callback

        # Start consuming from all subscription queues
        for subscription in self.config.subscriptions:
            queue_name = f"{subscription.exchange_name}.{subscription.topic}"
            self._consumer_tag = self._channel.basic_consume(
                queue=queue_name, on_message_callback=self._on_message, auto_ack=False
            )
            self.logger.info(
                "Started consuming from queue '%s' with consumer tag '%s'",
                queue_name,
                self._consumer_tag,
            )

    def _on_message(self, channel: Any, method: Any, properties: Any, body: Any) -> None:
        """
        Internal message handler that wraps the user callback.

        Args:
            channel: The channel object.
            method: Delivery method.
            properties: Message properties.
            body: The message body.
        """
        try:
            if self._consumer_callback:
                self._consumer_callback(channel, method, properties, body)
            # Acknowledge the message
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except (ValueError, TypeError, KeyError) as e:
            self.logger.error("Error processing message: %s", str(e))
            # Reject the message and requeue it
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("Unexpected error processing message: %s", str(e))
            # Reject the message and requeue it
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def stop_consuming(self) -> None:
        """Stop consuming messages."""
        if self._channel and self._consumer_tag:
            self._channel.basic_cancel(self._consumer_tag)
            self._consumer_tag = None
            self.logger.info("Stopped consuming messages")

    def start_io_loop(self) -> None:
        """Start the IO loop for async operations."""
        if self._rabbit_connection:
            self.logger.info("Starting IO loop")
            self._rabbit_connection.ioloop.start()

    def stop_io_loop(self) -> None:
        """Stop the IO loop."""
        if self._rabbit_connection:
            self.logger.info("Stopping IO loop")
            self._rabbit_connection.ioloop.stop()

    def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._rabbit_connection and not self._rabbit_connection.is_closed:
            self.logger.info("Disconnecting from RabbitMQ")
            self._rabbit_connection.close()
