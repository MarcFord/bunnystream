"""
Warren class for managing RabbitMQ connections and configurations.

This module provides the Warren class which handles RabbitMQ connection
parameters, URL parsing, and configuration management.
"""

from typing import Optional, Union

import pika

from bunnystream.config import BunnyStreamConfig
from bunnystream.exceptions import BunnyStreamConfigurationError
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
            config (BunnyStreamConfig): Configuration object containing BunnyStream parameters.
        """
        self._rabbit_connection = None
        self._config = config

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
            BunnyStreamConfigurationError: If the provided value is not a valid BunnyStreamConfig instance.
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
        # Example: open a channel when the connection opens
        connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel: pika.channel.Channel):
        """
        Callback when the RabbitMQ channel is opened.

        Args:
            channel: The opened RabbitMQ channel.
        """
        self.logger.info("RabbitMQ channel opened successfully.")

    def on_connection_error(
        self, connection: pika.SelectConnection, error: Exception
    ) -> None:
        """
        Callback when there is an error opening the RabbitMQ connection.

        Args:
            connection (pika.SelectConnection): The RabbitMQ connection.
            error (Exception): The error that occurred.
        """
        self.logger.error("Error opening RabbitMQ connection: %s", str(error))
        self._rabbit_connection = None

    def on_connection_closed(
        self, connection: pika.SelectConnection, reason: Union[str, None]
    ) -> None:
        """
        Callback when the RabbitMQ connection is closed.

        Args:
            connection (pika.SelectConnection): The RabbitMQ connection.
            reason (Union[str, None]): The reason for the closure.
        """
        self.logger.warning("RabbitMQ connection closed: %s", reason)
        self._rabbit_connection = None
