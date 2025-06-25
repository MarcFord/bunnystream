"""
Warren class for managing RabbitMQ connections and configurations.

This module provides the Warren class which handles RabbitMQ connection
parameters, URL parsing, and configuration management.
"""

from typing import Any, Callable, Optional, Union

import pika  # type: ignore
from pika.exchange_type import ExchangeType  # type: ignore

from bunnystream.config import BunnyStreamConfig
from bunnystream.exceptions import BunnyStreamConfigurationError, WarrenNotConnected
from bunnystream.logger import get_bunny_logger


class Warren:
    """
    Warren class for managing RabbitMQ connection parameters.

    This class handles configuration of RabbitMQ connection parameters
    including host, port, virtual host, credentials, and URL generation.
    It supports environment variable parsing and property validation.
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

        # Declare exchanges based on subscriptions
        for subscription in self.config.subscriptions:
            self._channel.exchange_declare(
                exchange=subscription.exchange_name,
                exchange_type=subscription.exchange_type,
                durable=True,
            )
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

        # Declare queue
        queue_name = f"{subscription.exchange_name}.{subscription.topic}"
        self._channel.queue_declare(queue=queue_name, durable=True)

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
