"""
Configuration module for BunnyStream.

This module provides the BunnyStreamConfig class for managing RabbitMQ connection
parameters, subscriptions, and other configuration options. It supports
environment variable parsing, advanced connection settings, and subscription
management for both producer and consumer modes.

Classes:
    BunnyStreamConfig: Main configuration class for RabbitMQ connections.

Constants:
    Various default values for connection parameters, timeouts, and limits.
"""

import json
import os
from typing import Optional, Union
from urllib.parse import unquote, urlparse

import pika  # type: ignore
import pika.connection  # type: ignore

from bunnystream.exceptions import (
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
from bunnystream.logger import get_bunny_logger
from bunnystream.subscription import Subscription

DEFAULT_PREFETCH_COUNT = 2  # Default prefetch count for consumers
DEFAULT_BLOCKED_CONNECTION_TIMEOUT = None
DEFAULT_CHANNEL_MAX = 65535  # per AMQP 0.9.1 spec.
MAX_CHANNELS = 65535
DEFAULT_CLIENT_PROPERTIES = None
DEFAULT_CONNECTION_ATTEMPTS = 2
DEFAULT_FRAME_MAX = 131072
FRAME_MAX_SIZE = 131072
FRAME_MIN_SIZE = 4096
DEFAULT_HEARTBEAT_TIMEOUT = None  # None accepts server's proposal
DEFAULT_LOCALE = "en_US"
DEFAULT_RETRY_DELAY = 2.0
DEFAULT_SOCKET_TIMEOUT = 10.0  # socket.connect() timeout
DEFAULT_STACK_TIMEOUT = 15.0  # full-stack TCP/[SSl]/AMQP bring-up timeout
DEFAULT_SSL = False
DEFAULT_SSL_OPTIONS = None
DEFAULT_SSL_PORT = 5671
DEFAULT_TCP_OPTIONS = None
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5672
DEFAULT_VHOST = "/"
DEFAULT_USER = "guest"
DEFAULT_PASS = "guest"  # nosec B105 - This is the standard RabbitMQ default
DEFAULT_EXCHANGE_NAME = "bunnystream"

NOT_SET = "Not Set"
NOT_SET_INT = -1
NOT_SET_FLOAT = -1.0
NOT_SET_DICT: dict[str, str] = {}

BUNNYSTREAM_MODE_PRODUCER = "producer"
BUNNYSTREAM_MODE_CONSUMER = "consumer"
VALID_MODES = [BUNNYSTREAM_MODE_PRODUCER, BUNNYSTREAM_MODE_CONSUMER]


class BunnyStreamConfig:
    """
    Configuration class for BunnyStream RabbitMQ connections.

    This class manages all aspects of RabbitMQ connection configuration including
    connection parameters, subscriptions, SSL settings, and advanced options.
    It supports both producer and consumer modes and can parse configuration
    from environment variables.

    Args:
        mode: The operation mode ("producer" or "consumer")
        exchange_name: Name of the RabbitMQ exchange
        rabbit_host: RabbitMQ server hostname
        rabbit_port: RabbitMQ server port
        rabbit_vhost: RabbitMQ virtual host
        rabbit_user: Username for authentication
        rabbit_pass: Password for authentication
    """

    def __init__(
        self,
        mode: str,
        exchange_name: Union[str, None] = None,
        rabbit_host: Union[str, None] = None,
        rabbit_port: Union[int, str, None] = None,
        rabbit_vhost: Union[str, None] = None,
        rabbit_user: Union[str, None] = None,
        rabbit_pass: Union[str, None] = None,
    ):
        self._url = None
        self._rabbit_port = None
        self._rabbit_host = None
        self._rabbit_vhost = None
        self._rabbit_user = None
        self._rabbit_pass = None
        self._prefetch_count = 0
        self._channel_max = None
        self._frame_max = None
        self._heartbeat = NOT_SET_INT
        self._blocked_connection_timeout = NOT_SET_FLOAT
        self._connection_attempts = None
        self._stack_timeout = None
        self._retry_delay = None
        self._socket_timeout = None
        self._tcp_options = NOT_SET_DICT
        self._ssl = None
        self._ssl_port = None
        self._ssl_options = NOT_SET
        self._locale = None
        self._mode = None
        self._exchange_name = None
        self._subscriptions: list[Subscription] = []
        self._subscription_mappings: dict[str, dict[str, object]] = {}
        self.logger = get_bunny_logger("bunnystream.config")

        # Check for RABBITMQ_URL environment variable first
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        if rabbitmq_url:
            self.logger.debug("Found RABBITMQ_URL environment variable, parsing URL")
            parsed_params = self._parse_rabbitmq_url(rabbitmq_url)

            # Use parsed values if not explicitly provided in constructor
            if rabbit_host is None:
                rabbit_host = parsed_params.get("host", DEFAULT_HOST)
            if rabbit_port is None:
                rabbit_port = parsed_params.get("port", DEFAULT_PORT)
            if rabbit_vhost is None:
                rabbit_vhost = parsed_params.get("vhost", DEFAULT_VHOST)
            if rabbit_user is None:
                rabbit_user = parsed_params.get("user", DEFAULT_USER)
            if rabbit_pass is None:
                rabbit_pass = parsed_params.get("pass", DEFAULT_PASS)

        # Set defaults for any remaining None values
        if rabbit_host is None:
            rabbit_host = os.environ.get("RABBITMQ_HOST", DEFAULT_HOST)
        if rabbit_port is None:
            rabbit_port = os.environ.get("RABBITMQ_PORT", DEFAULT_PORT)
        if rabbit_vhost is None:
            rabbit_vhost = os.environ.get("RABBITMQ_VHOST", DEFAULT_VHOST)
        if rabbit_user is None:
            rabbit_user = os.environ.get("RABBITMQ_USER", DEFAULT_USER)
        if rabbit_pass is None:
            rabbit_pass = os.environ.get("RABBITMQ_PASS", DEFAULT_PASS)
        if exchange_name is None:
            exchange_name = DEFAULT_EXCHANGE_NAME

        self.rabbit_host = rabbit_host
        self.rabbit_port = rabbit_port
        self.rabbit_vhost = rabbit_vhost
        self.rabbit_user = rabbit_user
        self.rabbit_pass = rabbit_pass
        self.exchange_name = exchange_name
        self.mode = mode
        self.add_subscription(Subscription(exchange_name=self.exchange_name))

        self.logger.debug(
            "Config initialized with port=%s, vhost=%s, host=%s",
            rabbit_port,
            rabbit_vhost,
            rabbit_host,
        )

    def _parse_rabbitmq_url(self, url: str) -> dict:
        """
        Parse a RABBITMQ_URL into its components.

        Expected format: amqp://user:pass@host:port/vhost

        Args:
            url (str): The RABBITMQ_URL to parse

        Returns:
            dict: Dictionary containing parsed components

        Raises:
            ValueError: If URL format is invalid
        """
        try:
            parsed = urlparse(url)

            # Validate scheme
            if parsed.scheme not in ["amqp", "amqps"]:
                raise ValueError(
                    f"Invalid URL scheme '{parsed.scheme}'. " "Expected 'amqp' or 'amqps'."
                )

            # Extract components
            result = {}

            if parsed.hostname:
                result["host"] = parsed.hostname

            if parsed.port:
                result["port"] = parsed.port

            if parsed.username:
                result["user"] = unquote(parsed.username)

            if parsed.password:
                result["pass"] = unquote(parsed.password)

            # Handle vhost (path component)
            if parsed.path and parsed.path != "/":
                # Remove leading slash and use as vhost
                result["vhost"] = parsed.path
            elif parsed.path == "/":
                # Explicit root vhost
                result["vhost"] = "/"

            self.logger.debug(
                "Parsed RABBITMQ_URL components: host=%s, port=%s, vhost=%s, user=%s",
                result.get("host"),
                result.get("port"),
                result.get("vhost"),
                result.get("user"),
            )

            return result

        except Exception as e:
            self.logger.error("Failed to parse RABBITMQ_URL: %s", str(e))
            raise ValueError(f"Invalid RABBITMQ_URL format: {str(e)}") from e

    @property
    def exchange_name(self) -> str:
        """
        Returns the name of the exchange used by the BunnyStream instance.

        If the exchange name is not set, it defaults to 'bunnystream_exchange'.
        This property can be used to retrieve or set the exchange name for
        publishing and consuming messages.

        Returns:
            str: The name of the exchange.
        """
        if self._exchange_name is None:
            self._exchange_name = DEFAULT_EXCHANGE_NAME
        return self._exchange_name

    @exchange_name.setter
    def exchange_name(self, value: Union[str, None]) -> None:
        """
        Sets the name of the exchange used by the BunnyStream instance.

        Args:
            value (str): The name of the exchange to set.

        Raises:
            ValueError: If the provided value is not a valid string.
        """
        if value is None:
            raise ExcangeNameError("Exchange name cannot be None.")
        if not isinstance(value, str):
            raise ExcangeNameError()
        if not value.strip():
            raise ExcangeNameError()
        self.logger.debug("Setting exchange name to: %s", value)
        self._exchange_name = value

    @property
    def mode(self) -> str:
        """
        Returns the mode of the BunnyStream instance.

        The mode is set during initialization and can be used to determine
        the operational context of the instance (e.g., 'producer', 'consumer').

        Returns:
            str: The mode of the BunnyStream instance.
        """
        if self._mode is None:
            raise BunnyStreamModeError(message="Mode has not been set.")
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """
        Sets the mode of the BunnyStream instance.

        Args:
            value (str): The mode to set for the BunnyStream instance.

        Raises:
            ValueError: If the provided value is not a valid mode.
        """
        if value not in VALID_MODES:
            raise BunnyStreamModeError(value=value, valid_modes=VALID_MODES)
        self.logger.debug("Setting mode to: %s", value)
        self._mode = value

    @property
    def prefetch_count(self) -> int:
        """
        Returns the number of messages to prefetch.

        Returns:
            int: The number of messages to prefetch.
        """
        if self._prefetch_count == 0:
            self._prefetch_count = DEFAULT_PREFETCH_COUNT
            self.logger.debug("Using default prefetch count: %s", self._prefetch_count)
        return self._prefetch_count

    @prefetch_count.setter
    def prefetch_count(self, value: int) -> None:
        """
        Sets the number of messages to prefetch.

        Args:
            value (int): The number of messages to prefetch.

        Raises:
            PrefetchCountError: If the provided value is not a positive integer.

        Side Effects:
            Updates the internal _prefetch_count attribute.
        """
        if not isinstance(value, int):
            raise PrefetchCountError("Prefetch count must be an integer.")
        if value <= 0:
            raise PrefetchCountError("Prefetch count must be a positive integer.")
        self.logger.debug("Setting prefetch count to: %s", value)
        self._prefetch_count = value

    @property
    def url(self) -> str:
        """
        Constructs and returns the AMQP URL for connecting to the RabbitMQ server.

        Returns:
            str: The AMQP URL in the format
                'amqp://<user>:<password>@<host>:<port>/<vhost>'.
        """
        if self._url is None:
            self._url = (
                f"amqp://{self._rabbit_user}:{self._rabbit_pass}@"
                f"{self._rabbit_host}:{self._rabbit_port}"
                f"/{self._rabbit_vhost}"
            )
            masked_url = self._url.replace(self._rabbit_pass or "", "***")
            self.logger.debug("Generated AMQP URL: %s", masked_url)
        return self._url

    @property
    def rabbit_port(self) -> int:
        """
        Returns the port number used by the rabbit service.

        Returns:
            int: The port number assigned to the rabbit service.
        """
        if self._rabbit_port is None:
            self.logger.info("Rabbit port is not set, using default port 5672.")
            return 5672
        if isinstance(self._rabbit_port, str):
            try:
                self._rabbit_port = int(self._rabbit_port)
            except ValueError as exc:
                raise RabbitPortError(
                    "Rabbit port must be a string that can be converted to an integer."
                ) from exc
        if not isinstance(self._rabbit_port, int):
            raise RabbitPortError("Rabbit port must be an integer.")
        if self._rabbit_port <= 0:
            raise RabbitPortError("Rabbit port must be a positive integer.")
        return self._rabbit_port

    @rabbit_port.setter
    def rabbit_port(self, value: Union[int, str, None]) -> None:
        if value is None:
            raise RabbitPortError("Rabbit port cannot be None.")
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError as exc:
                raise RabbitPortError(
                    "Rabbit port must be a string that can be converted to an integer."
                ) from exc
        if not isinstance(value, int):
            raise RabbitPortError(
                "Rabbit port must be an integer or a string that can be converted to an integer."
            )
        if value <= 0:
            raise RabbitPortError("Rabbit port must be a positive integer.")
        self.logger.debug("Setting rabbit port to: %s", value)
        self._rabbit_port = value
        self._url = None

    @property
    def rabbit_host(self) -> str:
        """
        Returns the value of the internal _rabbit_host attribute.

        If _rabbit_host is None, returns an empty string.

        Returns:
            str: The value of _rabbit_host, or an empty string if it is None.
        """
        if self._rabbit_host is None:
            return ""
        return self._rabbit_host

    @rabbit_host.setter
    def rabbit_host(self, value: Union[str, None]) -> None:
        if value is None:
            raise RabbitHostError("Rabbit host cannot be None.")
        if not isinstance(value, str):
            raise RabbitHostError("Rabbit host must be a string.")
        if not value.strip():
            raise RabbitHostError("Rabbit host cannot be empty.")
        if value.startswith("amqp://"):
            raise RabbitHostError("Rabbit host should not start with 'amqp://'.")
        self.logger.debug("Setting rabbit host to: %s", value)
        self._rabbit_host = value
        self._url = None

    @property
    def rabbit_vhost(self) -> str:
        """
        Returns the RabbitMQ virtual host used by the instance.

        Returns:
            str: The name of the RabbitMQ virtual host.
        """
        if self._rabbit_vhost is None:
            self.logger.info("Rabbit vhost is not set, using default vhost '/'.")
            self._rabbit_vhost = DEFAULT_VHOST
        if not isinstance(self._rabbit_vhost, str):
            raise RabbitVHostError("Rabbit vhost must be a string.")
        if not self._rabbit_vhost.strip():
            raise RabbitVHostError("Rabbit vhost cannot be empty.")
        self.logger.debug("Current rabbit vhost: %s", self._rabbit_vhost)
        return self._rabbit_vhost

    @rabbit_vhost.setter
    def rabbit_vhost(self, value: Union[str, None]) -> None:
        """
        Sets the RabbitMQ virtual host.

        Args:
            value (str): The name of the RabbitMQ virtual host.

        Raises:
            RabbitVHostError: If the provided value is not a string or is empty.

        Side Effects:
            Updates the internal _rabbit_vhost attribute and resets the _url attribute.
        """
        if not isinstance(value, str):
            raise RabbitVHostError("Rabbit vhost must be a string.")
        if not value.strip():
            raise RabbitVHostError("Rabbit vhost cannot be empty.")
        self.logger.debug("Setting rabbit vhost to: %s", value)
        self._rabbit_vhost = value
        self._url = None

    @property
    def rabbit_user(self) -> str:
        """
        Returns the current RabbitMQ username.

        If the username is not set, defaults to 'guest' and logs this event.
        Validates that the username is a non-empty string. Raises a
        RabbitCredentialsError if the username is not a string or is empty.

        Returns:
            str: The current RabbitMQ username.

        Raises:
            RabbitCredentialsError: If the username is not a string or is empty.
        """
        if self._rabbit_user is None:
            self.logger.info("Rabbit user is not set, using default user 'guest'.")
            self._rabbit_user = DEFAULT_USER
        if not isinstance(self._rabbit_user, str):
            raise RabbitCredentialsError("Rabbit user must be a string.")
        if not self._rabbit_user.strip():
            raise RabbitCredentialsError("Rabbit user cannot be empty.")
        self.logger.debug("Current rabbit user: %s", self._rabbit_user)
        return self._rabbit_user

    @rabbit_user.setter
    def rabbit_user(self, value: Union[str, None]) -> None:
        """
        Sets the RabbitMQ username.

        Validates that the provided value is a non-empty string. Raises a
        RabbitCredentialsError if the value is empty or not a string. On success,
        sets the internal rabbit user and resets the connection URL.

        Args:
            value (str): The RabbitMQ username to set.

        Raises:
            RabbitCredentialsError: If the username is empty or not a string.
        """
        if not isinstance(value, str):
            raise RabbitCredentialsError("Rabbit user must be a string.")
        if not value.strip():
            raise RabbitCredentialsError("Rabbit user cannot be empty.")
        self.logger.debug("Setting rabbit user to: %s", value)
        self._rabbit_user = value
        self._url = None

    @property
    def rabbit_pass(self) -> str:
        """
        Retrieves the RabbitMQ password, setting it to the default 'guest'
        if not already set.

        Returns:
            str: The RabbitMQ password.

        Raises:
            RabbitCredentialsError: If the password is not a string or is empty.

        Logs:
            - Info: When the password is not set and defaults to 'guest'.
            - Debug: The current (masked) password value.
        """
        if self._rabbit_pass is None:
            self.logger.info("Rabbit password is not set, using default password 'guest'.")
            self._rabbit_pass = DEFAULT_PASS
        if not isinstance(self._rabbit_pass, str):
            raise RabbitCredentialsError("Rabbit password must be a string.")
        if not self._rabbit_pass.strip():
            raise RabbitCredentialsError("Rabbit password cannot be empty.")
        masked_pass = "***" if self._rabbit_pass else self._rabbit_pass
        self.logger.debug("Current rabbit password: %s", masked_pass)
        return self._rabbit_pass

    @rabbit_pass.setter
    def rabbit_pass(self, value: Union[str, None]) -> None:
        """
        Sets the RabbitMQ password.

        Validates that the provided value is a non-empty string. Raises a
        RabbitCredentialsError if the value is empty or not a string. On success,
        sets the internal rabbit password and resets the connection URL.

        Args:
            value (str): The RabbitMQ password to set.

        Raises:
            RabbitCredentialsError: If the password is empty or not a string.
        """
        if not isinstance(value, str):
            raise RabbitCredentialsError("Rabbit password must be a string.")
        if not value.strip():
            raise RabbitCredentialsError("Rabbit password cannot be empty.")
        self.logger.debug("Setting rabbit password.")
        self._rabbit_pass = value
        self._url = None

    @property
    def channel_max(self) -> int:
        """
        Returns the maximum number of channels allowed in the RabbitMQ connection.

        This property is used to set the maximum number of channels that can be
        opened in a RabbitMQ connection. It defaults to 65535, which is the
        maximum value per AMQP 0.9.1 specification.

        Returns:
            int: The maximum number of channels allowed.
        """
        if self._channel_max is not None:
            self.logger.debug("Using internal channel max: %s", self._channel_max)
            return self._channel_max
        channel_max = os.getenv("RABBITMQ_CHANNEL_MAX")
        if channel_max is not None:
            try:
                channel_max = int(channel_max)
                self.channel_max = int(channel_max)  # Use setter to validate
                return channel_max
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_CHANNEL_MAX value, using default: %s",
                    DEFAULT_CHANNEL_MAX,
                )
                return DEFAULT_CHANNEL_MAX
        self.logger.debug("Using default channel max: %s", DEFAULT_CHANNEL_MAX)
        return DEFAULT_CHANNEL_MAX

    @channel_max.setter
    def channel_max(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("Channel max must be an integer.")
        if value <= 0:
            raise ValueError("Channel max must be a positive integer.")
        if value > MAX_CHANNELS:
            raise ValueError(f"Channel max cannot exceed {MAX_CHANNELS}.")
        self.logger.debug("Setting channel max to: %s", value)
        self._channel_max = value

    @property
    def frame_max(self) -> int:
        """
        Returns the maximum frame size for RabbitMQ connections.

        This property is used to set the maximum frame size for RabbitMQ
        connections. It defaults to 131072 bytes, which is the standard
        maximum frame size per AMQP 0.9.1 specification.

        Returns:
            int: The maximum frame size in bytes.
        """
        if self._frame_max is not None:
            self.logger.debug("Using internal frame max: %s", self._frame_max)
            return self._frame_max
        # Check environment variable for frame max
        frame_max = os.getenv("RABBITMQ_FRAME_MAX")
        if frame_max is not None:
            try:
                frame_max = int(frame_max)
                self.frame_max = frame_max  # Use setter to validate
                return frame_max
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_FRAME_MAX value, using default: %s",
                    DEFAULT_FRAME_MAX,
                )
                return DEFAULT_FRAME_MAX
        self.logger.debug("Using default frame max: %s", DEFAULT_FRAME_MAX)
        return DEFAULT_FRAME_MAX

    @frame_max.setter
    def frame_max(self, value: int) -> None:
        """
        Sets the maximum frame size for RabbitMQ connections.

        Args:
            value (int): The maximum frame size in bytes.

        Raises:
            ValueError: If the provided value is not a positive integer.
        """
        if not isinstance(value, int):
            raise ValueError("Frame max must be an integer.")
        if value <= FRAME_MIN_SIZE:
            raise ValueError(f"Min AMQP 0.9.1 Frame Size is {FRAME_MIN_SIZE}, but got {value!r}")
        if value > FRAME_MAX_SIZE:
            raise ValueError(f"Max AMQP 0.9.1 Frame Size is {FRAME_MAX_SIZE}, but got {value!r}")
        self.logger.debug("Setting frame max to: %s", value)
        self._frame_max = value

    @property
    def heartbeat(self) -> Optional[int]:
        """
        Returns the heartbeat timeout for RabbitMQ connections.

        This property is used to set the heartbeat timeout for RabbitMQ
        connections. It defaults to None, meaning no heartbeat is set.

        Returns:
            Optional[int]: The heartbeat timeout in seconds, or None if not set.
        """
        if self._heartbeat != NOT_SET_INT and self._heartbeat is not None:
            self.logger.debug("Using internal heartbeat: %s", self._heartbeat)
            return self._heartbeat
        # Check environment variable for heartbeat timeout
        heartbeat = os.getenv("RABBITMQ_HEARTBEAT")
        if heartbeat is not None:
            try:
                heartbeat = int(heartbeat)
                self.heartbeat = heartbeat  # Use setter to validate
                return heartbeat
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_HEARTBEAT value, using default: %s",
                    DEFAULT_HEARTBEAT_TIMEOUT,
                )
                return DEFAULT_HEARTBEAT_TIMEOUT
        self.logger.debug("Using default heartbeat timeout: %s", DEFAULT_HEARTBEAT_TIMEOUT)
        return DEFAULT_HEARTBEAT_TIMEOUT

    @heartbeat.setter
    def heartbeat(self, value: int) -> None:
        """
        Sets the heartbeat timeout for RabbitMQ connections.

        Args:
            value (int): The heartbeat timeout in seconds.

        Raises:
            ValueError: If the provided value is not a non-negative integer.
        """
        if not isinstance(value, int):
            raise ValueError("Heartbeat must be an integer.")
        if value < 0:
            raise ValueError("Heartbeat must be a non-negative integer.")
        self.logger.debug("Setting heartbeat to: %s", value)
        self._heartbeat = value

    @property
    def blocked_connection_timeout(self) -> Optional[float]:
        """
        Returns the blocked connection timeout for RabbitMQ connections.

        This property is used to set the timeout for blocked connections.
        It defaults to None, meaning no timeout is set.

        Returns:
            Optional[float]: The blocked connection timeout in seconds,
                or None if not set.
        """
        if (
            self._blocked_connection_timeout != NOT_SET_FLOAT
            and self._blocked_connection_timeout is not None
        ):
            self.logger.debug(
                "Using internal blocked connection timeout: %s",
                self._blocked_connection_timeout,
            )
            return self._blocked_connection_timeout
        blocked_connection_timeout = os.getenv("RABBITMQ_BLOCKED_CONNECTION_TIMEOUT")
        if blocked_connection_timeout is not None:
            try:
                blocked_connection_timeout = float(blocked_connection_timeout)
                self.blocked_connection_timeout = (
                    blocked_connection_timeout  # Use setter to validate
                )
                self.logger.debug(
                    "Using RABBITMQ_BLOCKED_CONNECTION_TIMEOUT from environment: %s",
                    blocked_connection_timeout,
                )
                return blocked_connection_timeout
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_BLOCKED_CONNECTION_TIMEOUT value, using default: %s",
                    DEFAULT_BLOCKED_CONNECTION_TIMEOUT,
                )
                return DEFAULT_BLOCKED_CONNECTION_TIMEOUT
        self.logger.debug(
            "Using default blocked connection timeout: %s",
            DEFAULT_BLOCKED_CONNECTION_TIMEOUT,
        )
        return DEFAULT_BLOCKED_CONNECTION_TIMEOUT

    @blocked_connection_timeout.setter
    def blocked_connection_timeout(self, value: Union[int, float, None]) -> None:
        """
        Sets the blocked connection timeout for RabbitMQ connections.

        Args:
            value (float): The blocked connection timeout in seconds.

        Raises:
            ValueError: If the provided value is not a non-negative float.
        """
        if value is None:
            self.logger.debug("Setting blocked connection timeout to None (no timeout).")
            self._blocked_connection_timeout = None
            return
        if not isinstance(value, (int, float)):
            raise ValueError("Blocked connection timeout must be a float or an integer.")
        if value < 0:
            raise ValueError("Blocked connection timeout must be a non-negative float.")
        self.logger.debug("Setting blocked connection timeout to: %s", value)
        self._blocked_connection_timeout = value

    @property
    def connection_attempts(self) -> int:
        """
        Returns the number of connection attempts for RabbitMQ.

        This property is used to set the number of attempts to connect to
        RabbitMQ before giving up. It defaults to 1.

        Returns:
            int: The number of connection attempts.
        """
        if self._connection_attempts is not None:
            self.logger.debug("Using internal connection attempts: %s", self._connection_attempts)
            return self._connection_attempts
        # Check environment variable for connection attempts
        connection_attempts = os.getenv("RABBITMQ_CONNECTION_ATTEMPTS")
        if connection_attempts is not None:
            try:
                connection_attempts = int(connection_attempts)
                self.connection_attempts = connection_attempts  # Use setter to validate
                return connection_attempts
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_CONNECTION_ATTEMPTS value, using default: %s",
                    DEFAULT_CONNECTION_ATTEMPTS,
                )
                return DEFAULT_CONNECTION_ATTEMPTS
        self.logger.debug("Using default connection attempts: %s", DEFAULT_CONNECTION_ATTEMPTS)
        return DEFAULT_CONNECTION_ATTEMPTS

    @connection_attempts.setter
    def connection_attempts(self, value: int) -> None:
        """
        Sets the number of connection attempts for RabbitMQ.

        Args:
            value (int): The number of connection attempts.

        Raises:
            ValueError: If the provided value is not a positive integer.
        """
        if not isinstance(value, int):
            raise ValueError("Connection attempts must be an integer.")
        if value < 1:
            raise ValueError("Connection attempts must be a greater than 1.")
        self.logger.debug("Setting connection attempts to: %s", value)
        self._connection_attempts = value

    @property
    def stack_timeout(self) -> float:
        """
        Returns the stack timeout for RabbitMQ connections.

        This property is used to set the timeout for the full-stack TCP/SSL/AMQP
        bring-up process. It defaults to 15.0 seconds.

        Returns:
            float: The stack timeout in seconds.
        """
        if self._stack_timeout is not None:
            self.logger.debug("Using internal stack timeout: %s", self._stack_timeout)
            return self._stack_timeout
        # Check environment variable for stack timeout
        stack_timeout = os.getenv("RABBITMQ_STACK_TIMEOUT")
        if stack_timeout is not None:
            try:
                stack_timeout = float(stack_timeout)
                self.stack_timeout = stack_timeout  # Use setter to validate
                return stack_timeout
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_STACK_TIMEOUT value, using default: %s",
                    DEFAULT_STACK_TIMEOUT,
                )
                return DEFAULT_STACK_TIMEOUT
        self.logger.debug("Using default stack timeout: %s", DEFAULT_STACK_TIMEOUT)
        return DEFAULT_STACK_TIMEOUT

    @stack_timeout.setter
    def stack_timeout(self, value: Union[int, float]) -> None:
        """
        Sets the stack timeout for RabbitMQ connections.

        Args:
            value (float): The stack timeout in seconds.

        Raises:
            ValueError: If the provided value is not a positive float.
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Stack timeout must be a float or an integer.")
        if value <= 0:
            raise ValueError("Stack timeout must be a positive float.")
        self.logger.debug("Setting stack timeout to: %s", value)
        self._stack_timeout = value

    @property
    def retry_delay(self) -> float:
        """
        Returns the delay in seconds before retrying a connection.

        This property is used to set the delay between connection retries.
        It defaults to 2.0 seconds.

        Returns:
            float: The retry delay in seconds.
        """
        if self._retry_delay is not None:
            self.logger.debug("Using internal retry delay: %s", self._retry_delay)
            return self._retry_delay
        # Check environment variable for retry delay
        retry_delay = os.getenv("RABBITMQ_RETRY_DELAY")
        if retry_delay is not None:
            try:
                retry_delay = float(retry_delay)
                self.retry_delay = retry_delay  # Use setter to validate
                return retry_delay
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_RETRY_DELAY value, using default: %s",
                    DEFAULT_RETRY_DELAY,
                )
                return DEFAULT_RETRY_DELAY
        self.logger.debug("Using default retry delay: %s", DEFAULT_RETRY_DELAY)
        return DEFAULT_RETRY_DELAY

    @retry_delay.setter
    def retry_delay(self, value: Union[int, float]) -> None:
        """
        Sets the delay in seconds before retrying a connection.

        Args:
            value (float): The retry delay in seconds.

        Raises:
            ValueError: If the provided value is not a non-negative float.
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Retry delay must be a float or an integer.")
        if value < 0:
            raise ValueError("Retry delay must be a non-negative float.")
        self.logger.debug("Setting retry delay to: %s", value)
        self._retry_delay = value

    @property
    def socket_timeout(self) -> float:
        """
        Returns the socket timeout for RabbitMQ connections.

        This property is used to set the socket timeout for RabbitMQ
        connections. It defaults to 10.0 seconds.

        Returns:
            float: The socket timeout in seconds.
        """
        if self._socket_timeout is not None:
            self.logger.debug("Using internal socket timeout: %s", self._socket_timeout)
            return self._socket_timeout
        # Check environment variable for socket timeout
        socket_timeout = os.getenv("RABBITMQ_SOCKET_TIMEOUT")
        if socket_timeout is not None:
            try:
                socket_timeout = float(socket_timeout)
                self.socket_timeout = socket_timeout  # Use setter to validate
                return socket_timeout
            except ValueError:
                self.logger.error(
                    "Invalid RABBITMQ_SOCKET_TIMEOUT value, using default: %s",
                    DEFAULT_SOCKET_TIMEOUT,
                )
                return DEFAULT_SOCKET_TIMEOUT
        self.logger.debug("Using default socket timeout: %s", DEFAULT_SOCKET_TIMEOUT)
        return DEFAULT_SOCKET_TIMEOUT

    @socket_timeout.setter
    def socket_timeout(self, value: Union[int, float]) -> None:
        """
        Sets the socket timeout for RabbitMQ connections.

        Args:
            value (float): The socket timeout in seconds.

        Raises:
            ValueError: If the provided value is not a non-negative float.
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Socket timeout must be a float or an integer.")
        if value <= 0:
            raise ValueError("Socket timeout must be a positive float.")
        self.logger.debug("Setting socket timeout to: %s", value)
        self._socket_timeout = value

    @property
    def tcp_options(self) -> Optional[dict]:
        """
        Returns the TCP options for RabbitMQ connections.

        This property is used to set the TCP options for RabbitMQ connections.
        It defaults to None, meaning no custom TCP options are set. Currently
        supported are TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT and TCP_USER_TIMEOUT.
        Availability of these may depend on your platform.

        Returns:
            Optional[dict]: The TCP options dictionary, or None if not set.
        """
        if self._tcp_options != NOT_SET_DICT and self._tcp_options:
            self.logger.debug("Using internal TCP options: %s", self._tcp_options)
            return self._tcp_options
        # Check environment variable for TCP options
        tcp_options = os.getenv("RABBITMQ_TCP_OPTIONS")
        if tcp_options:
            try:
                tcp_options = json.loads(tcp_options)
                self.tcp_options = tcp_options  # Use setter to validate
                return tcp_options
            except json.JSONDecodeError as e:
                self.logger.error("Invalid RABBITMQ_TCP_OPTIONS JSON format: %s", str(e))
                return None
            except InvalidTCPOptionsError as e:
                self.logger.error("Invalid TCP options: %s", str(e))
                return None
        self.logger.debug("Using default TCP options: None")
        return DEFAULT_TCP_OPTIONS

    @tcp_options.setter
    def tcp_options(self, value: dict) -> None:
        """
        Sets the TCP options for RabbitMQ connections.

        Args:
            value (dict): The TCP options to set.

        Raises:
            InvalidTCPOptionsError: If the provided value is not a valid dictionary
                                    or contains invalid keys.
        """
        if value is None:
            self.logger.debug("Setting TCP options to None (no custom options).")
            self._tcp_options = value
            return
        self._validate_tcp_options(value)
        self.logger.debug("Setting TCP options: %s", value)
        self._tcp_options = value

    @property
    def ssl(self) -> bool:
        """
        Returns whether SSL is enabled for RabbitMQ connections.

        This property indicates if SSL should be used for RabbitMQ connections.
        It defaults to False, meaning SSL is not enabled.

        Returns:
            bool: True if SSL is enabled, False otherwise.
        """
        if self._ssl is not None:
            self.logger.debug("Using internal SSL setting: %s", self._ssl)
            return self._ssl
        # Check environment variable for SSL setting
        ssl = os.getenv("RABBITMQ_SSL", "false").lower()
        if ssl in ["true", "1", "yes"]:
            self._ssl = True
        elif ssl in ["false", "0", "no"]:
            self._ssl = False
        else:
            self._ssl = DEFAULT_SSL
        self.logger.debug("SSL enabled: %s", self._ssl)
        return self._ssl

    @ssl.setter
    def ssl(self, value: bool) -> None:
        """
        Sets whether SSL is enabled for RabbitMQ connections.

        Args:
            value (bool): True to enable SSL, False to disable it.

        Raises:
            ValueError: If the provided value is not a boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("SSL must be a boolean value.")
        self.logger.debug("Setting SSL to: %s", value)
        self._ssl = value

    @property
    def ssl_port(self) -> int:
        """
        Returns the port number for SSL connections.

        This property is used to set the port number for SSL connections to RabbitMQ.
        It defaults to 5671, which is the standard SSL port for RabbitMQ.

        Returns:
            int: The SSL port number.
        """
        if self._ssl_port is not None:
            self.logger.debug("Using internal SSL port: %s", self._ssl_port)
            return self._ssl_port
        # Check environment variable for SSL port
        ssl_port = os.getenv("RABBITMQ_SSL_PORT", str(DEFAULT_SSL_PORT))
        try:
            ssl_port = int(ssl_port)
            self.ssl_port = ssl_port  # Use setter to validate
            self.logger.debug("Using RABBITMQ_SSL_PORT from environment: %s", ssl_port)
            return ssl_port
        except ValueError:
            self.logger.error(
                "Invalid RABBITMQ_SSL_PORT value, using default: %s", DEFAULT_SSL_PORT
            )
            return DEFAULT_SSL_PORT

    @ssl_port.setter
    def ssl_port(self, value: int) -> None:
        """
        Sets the port number for SSL connections.

        Args:
            value (int): The port number to set for SSL connections.

        Raises:
            ValueError: If the provided value is not a positive integer.
        """
        if not isinstance(value, int):
            raise ValueError("SSL port must be an integer.")
        if value <= 0:
            raise ValueError("SSL port must be a positive integer.")
        self.logger.debug("Setting SSL port to: %s", value)
        self._ssl_port = value

    @property
    def ssl_options(self) -> Optional[pika.connection.SSLOptions]:
        """
        Returns the SSL options for RabbitMQ connections.

        This property is used to set the SSL options for RabbitMQ connections.
        It defaults to None, meaning no custom SSL options are set.

        Returns:
            Optional[pika.connection.SSLOptions]: The SSL options, or None if not set.
        """
        if (
            self._ssl_options != NOT_SET
            and self._ssl_options is not None
            and isinstance(self._ssl_options, pika.connection.SSLOptions)
        ):
            self.logger.debug("Using custom SSL options.")
            return self._ssl_options
        self.logger.debug("Using default SSL options: None")
        return DEFAULT_SSL_OPTIONS

    @ssl_options.setter
    def ssl_options(self, value: pika.connection.SSLOptions) -> None:
        """
        Sets the SSL options for RabbitMQ connections.

        Args:
            value (pika.connection.SSLOptions): The SSL options to set.

        Raises:
            TypeError: If the provided value is not an instance of
                pika.connection.SSLOptions.
        """
        if not isinstance(value, pika.connection.SSLOptions):
            raise SSLOptionsError()
        self.logger.debug("Setting SSL options.")
        self._ssl_options = value

    @property
    def locale(self) -> str:
        """
        Returns the locale for RabbitMQ connections.

        This property is used to set the locale for RabbitMQ connections.
        It defaults to 'en_US'.

        Returns:
            str: The locale string.
        """
        if self._locale is not None:
            self.logger.debug("Using internal locale: %s", self._locale)
            return self._locale
        # Check environment variable for locale
        locale = os.getenv("RABBITMQ_LOCALE", DEFAULT_LOCALE)
        try:
            self.locale = locale  # Use setter to validate
            self.logger.debug("Using RABBITMQ_LOCALE from environment: %s", locale)
        except ValueError:
            self.logger.error("Invalid RABBITMQ_LOCALE value, using default: %s", DEFAULT_LOCALE)
            locale = DEFAULT_LOCALE
        self.logger.debug("Using RabbitMQ locale: %s", locale)
        return locale

    @locale.setter
    def locale(self, value: str) -> None:
        """
        Sets the locale for RabbitMQ connections.

        Args:
            value (str): The locale string to set.

        Raises:
            ValueError: If the provided value is not a string.
        """
        if not isinstance(value, str):
            raise ValueError("RabbitMQ locale must be a string.")
        if not value.strip():
            raise ValueError("RabbitMQ locale cannot be empty.")
        self.logger.debug("Setting RabbitMQ locale to: %s", value)
        self._locale = value

    @property
    def subscriptions(self) -> list[Subscription]:
        """
        Returns the subscriptions for RabbitMQ connections.

        This property is used to set the subscriptions for RabbitMQ connections.
        It defaults to an empty dictionary.

        Returns:
            list[Subscription]: The subscriptions dictionary.
        """
        if self._subscriptions is None:
            raise SubscriptionsNotSetError("Subscriptions have not been set.")
        self.logger.debug("Using internal subscriptions: %s", self._subscriptions)
        return self._subscriptions

    @property
    def subscription_mappings(self) -> dict[str, dict[str, object]]:
        """
        Returns a mapping of exchange names to their topics.

        This property provides a dictionary where each key is an exchange name
        and the value is another dictionary containing the topics associated
        with that exchange.

        Returns:
            dict[str, dict[str, object]]: A mapping of exchange names to their
                topics and exchange type.
        """
        if self._subscriptions is None:
            raise SubscriptionsNotSetError("Subscriptions have not been set.")
        if not self._subscription_mappings:
            for subscription in self._subscriptions:
                self._subscription_mappings[subscription.exchange_name] = {
                    "topic": subscription.topic,
                    "type": subscription.exchange_type,
                }
            self.logger.debug("Subscription mappings: %s", self._subscription_mappings)
        return self._subscription_mappings

    def add_subscription(self, subscription: Subscription) -> None:
        """
        Adds a subscription to the RabbitMQ configuration.

        Args:
            subscription (Subscription): The subscription to add.

        Raises:
            ValueError: If the provided subscription is not an instance of Subscription.
        """
        if not isinstance(subscription, Subscription):
            raise ValueError("Subscription must be an instance of Subscription.")
        if self._subscriptions is None:
            self._subscriptions = []
        self._subscriptions.append(subscription)
        self._subscription_mappings[subscription.exchange_name] = {
            "topic": subscription.topic,
            "type": subscription.exchange_type,
        }
        self.logger.debug(
            "Added subscription: %s type: %s topics: %s",
            subscription.exchange_name,
            subscription.exchange_type,
            subscription.topic if not subscription.topic.strip() else "None",
        )

    def remove_subscription(self, exchange_name: str) -> None:
        """
        Removes a subscription from the RabbitMQ configuration.

        Args:
            exchange_name (str): The name of the exchange to remove subscription for.

        Raises:
            ValueError: If the exchange_name is not found in subscriptions.
        """
        if self._subscriptions is None:
            raise SubscriptionsNotSetError("Subscriptions have not been set.")
        for subscription in self._subscriptions:
            if subscription.exchange_name == exchange_name:
                self.logger.debug("Removing subscription for exchange: %s", exchange_name)
                self._subscriptions.remove(subscription)
                self._subscription_mappings.pop(exchange_name, None)
                return
        raise ValueError(f"Subscription for exchange '{exchange_name}' not found.")

    def _validate_tcp_options(self, options: dict) -> None:
        """
        Validates the provided TCP options.

        Args:
            options (dict): The TCP options to validate.

        Raises:
            ValueError: If any of the TCP options are invalid.
        """
        valid_keys = [
            "TCP_KEEPIDLE",
            "TCP_KEEPINTVL",
            "TCP_KEEPCNT",
            "TCP_USER_TIMEOUT",
        ]
        if not isinstance(options, dict):
            raise InvalidTCPOptionsError("TCP options must be a dictionary.")
        if not options:
            raise InvalidTCPOptionsError("TCP options cannot be an empty dictionary.")
        invalid_keys = [key for key in options.keys() if key not in valid_keys]
        if invalid_keys:
            self.logger.error("Invalid TCP options provided: %s", invalid_keys)
            raise InvalidTCPOptionsError(
                f"Invalid TCP options: {invalid_keys}. " f"Valid options are: {valid_keys}"
            )
        self.logger.debug("TCP options validated successfully: %s", options)
