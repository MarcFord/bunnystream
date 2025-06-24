"""
Warren class for managing RabbitMQ connections and configurations.

This module provides the Warren class which handles RabbitMQ connection
parameters, URL parsing, and configuration management.
"""
import os
from typing import Optional, Union
from urllib.parse import urlparse, unquote
from bunnystream.exceptions import (
    RabbitPortError, RabbitHostError, RabbitVHostError, RabbitCredentialsError,
    ExcangeNameError,
)
from bunnystream.logger import get_bunny_logger


class Warren:
    """
    Warren class for managing RabbitMQ connection parameters.

    This class handles configuration of RabbitMQ connection parameters
    including host, port, virtual host, credentials, and URL generation.
    It supports environment variable parsing and property validation.
    """

    def __init__(self,
                 rabbit_port: int = 5672,
                 rabbit_vhost: str = "/",
                 exchange_name: str = 'bunnystream_exchange',
                 rabbit_host: Optional[str] = None,
                 rabbit_user: Optional[str] = None,
                 rabbit_pass: Optional[str] = None):
        """
        Initialize Warren with RabbitMQ connection parameters.

        Args:
            rabbit_port: RabbitMQ port (default: 5672)
            rabbit_vhost: RabbitMQ virtual host (default: "/")
            rabbit_host: RabbitMQ host (default: None)
            rabbit_user: RabbitMQ username (default: None)
            rabbit_pass: RabbitMQ password (default: None)
        """
        self._url = None
        self._rabbit_port = None
        self._rabbit_host = None
        self._rabbit_vhost = None
        self._rabbit_user = None
        self._rabbit_pass = None
        self._exchange_name = None

        # Initialize logger for this instance
        self.logger = get_bunny_logger("warren")

        # Check for RABBITMQ_URL environment variable first
        rabbitmq_url = os.getenv('RABBITMQ_URL')
        if rabbitmq_url:
            self.logger.debug("Found RABBITMQ_URL environment variable, "
                              "parsing URL")
            parsed_params = self._parse_rabbitmq_url(rabbitmq_url)

            # Use parsed values if not explicitly provided in constructor
            if rabbit_host is None:
                rabbit_host = parsed_params.get('host')
            if rabbit_port == 5672:  # Default value, use parsed port
                rabbit_port = parsed_params.get('port', 5672)
            if rabbit_vhost == "/":  # Default value, use parsed vhost
                rabbit_vhost = parsed_params.get('vhost', "/")
            if rabbit_user is None:
                rabbit_user = parsed_params.get('user')
            if rabbit_pass is None:
                rabbit_pass = parsed_params.get('pass')

        # Check for BUNNYSTREAM_EXCHANGE_NAME environment variable first
        bunny_exchange_name = os.getenv('BUNNYSTREAM_EXCHANGE_NAME')
        if bunny_exchange_name:
            self.logger.debug("Found BUNNYSTREAM_EXCHANGE_NAME environment "
                              "variable, using it as exchange name")
            self.exchange_name = bunny_exchange_name
        else:
            # Use provided exchange name or default to 'bunnystream_exchange'
            self.exchange_name = exchange_name

        # Set initial values through properties to trigger validation
        self.rabbit_port = rabbit_port
        self.rabbit_vhost = rabbit_vhost
        if rabbit_host is not None:
            self.rabbit_host = rabbit_host
        self._rabbit_user = rabbit_user
        self._rabbit_pass = rabbit_pass

        self.logger.debug("Warren initialized with port=%s, vhost=%s, host=%s",
                          rabbit_port, rabbit_vhost, rabbit_host)

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
            if parsed.scheme not in ['amqp', 'amqps']:
                raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. "
                                 "Expected 'amqp' or 'amqps'.")

            # Extract components
            result = {}

            if parsed.hostname:
                result['host'] = parsed.hostname

            if parsed.port:
                result['port'] = parsed.port

            if parsed.username:
                result['user'] = unquote(parsed.username)

            if parsed.password:
                result['pass'] = unquote(parsed.password)

            # Handle vhost (path component)
            if parsed.path and parsed.path != '/':
                # Remove leading slash and use as vhost
                result['vhost'] = parsed.path

            self.logger.debug("Parsed RABBITMQ_URL components: host=%s, "
                              "port=%s, vhost=%s, user=%s",
                              result.get('host'), result.get('port'),
                              result.get('vhost'), result.get('user'))

            return result

        except Exception as e:
            self.logger.error("Failed to parse RABBITMQ_URL: %s", str(e))
            raise ValueError(f"Invalid RABBITMQ_URL format: {str(e)}") from e

    @property
    def exchange_name(self) -> str:
        """
        Returns the name of the RabbitMQ exchange used by the instance.

        Returns:
            str: The name of the RabbitMQ exchange.
        """
        if self._exchange_name is None:
            self._exchange_name = "bunnystream_exchange"
            self.logger.debug("Using default exchange name: %s",
                              self._exchange_name)
        if not isinstance(self._exchange_name, str):
            raise ExcangeNameError(
                "Exchange name must be a string."
            )
        if not self._exchange_name.strip():
            raise ExcangeNameError("Exchange name cannot be empty.")
        self.logger.debug("Current exchange name: %s", self._exchange_name)
        return self._exchange_name

    @exchange_name.setter
    def exchange_name(self, value: str) -> None:
        """
        Sets the RabbitMQ exchange name.

        Args:
            value (str): The name of the RabbitMQ exchange.

        Raises:
            ExcangeNameError: If the provided value is not a string or is empty.

        Side Effects:
            Updates the internal _exchange_name attribute.
        """
        if not isinstance(value, str):
            raise ExcangeNameError("Exchange name must be a string.")
        if not value.strip():
            raise ExcangeNameError("Exchange name cannot be empty.")
        self.logger.debug("Setting exchange name to: %s", value)
        self._exchange_name = value

    @property
    def url(self) -> str:
        """
        Constructs and returns the AMQP URL for connecting to the RabbitMQ server.

        Returns:
            str: The AMQP URL in the format
                'amqp://<user>:<password>@<host>:<port>/<vhost>'.
        """
        if self._url is None:
            self._url = (f"amqp://{self._rabbit_user}:{self._rabbit_pass}@"
                         f"{self._rabbit_host}:{self._rabbit_port}"
                         f"/{self._rabbit_vhost}")
            if self._rabbit_pass:
                masked_url = self._url.replace(self._rabbit_pass, '***')
            else:
                masked_url = self._url
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
                    "Rabbit port must be a string that can be converted "
                    "to an integer."
                ) from exc
        if not isinstance(self._rabbit_port, int):
            raise RabbitPortError("Rabbit port must be an integer.")
        if self._rabbit_port <= 0:
            raise RabbitPortError("Rabbit port must be a positive integer.")
        return self._rabbit_port

    @rabbit_port.setter
    def rabbit_port(self, value: Union[int, str]) -> None:
        if isinstance(value, str):
            value = int(value)
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
            return ''
        return self._rabbit_host

    @rabbit_host.setter
    def rabbit_host(self, value: str) -> None:
        if not value:
            raise RabbitHostError()
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
            self._rabbit_vhost = "/"
        if not isinstance(self._rabbit_vhost, str):
            raise RabbitVHostError("Rabbit vhost must be a string.")
        if not self._rabbit_vhost.strip():
            raise RabbitVHostError("Rabbit vhost cannot be empty.")
        self.logger.debug("Current rabbit vhost: %s", self._rabbit_vhost)
        return self._rabbit_vhost

    @rabbit_vhost.setter
    def rabbit_vhost(self, value: str) -> None:
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
        Validates that the username is a non-empty string. Raises a RabbitCredentialsError
        if the username is not a string or is empty.

        Returns:
            str: The current RabbitMQ username.

        Raises:
            RabbitCredentialsError: If the username is not a string or is empty.
        """
        if self._rabbit_user is None:
            self.logger.info("Rabbit user is not set, using default user 'guest'.")
            self._rabbit_user = "guest"
        if not isinstance(self._rabbit_user, str):
            raise RabbitCredentialsError("Rabbit user must be a string.")
        if not self._rabbit_user.strip():
            raise RabbitCredentialsError("Rabbit user cannot be empty.")
        self.logger.debug("Current rabbit user: %s", self._rabbit_user)
        return self._rabbit_user

    @rabbit_user.setter
    def rabbit_user(self, value: str) -> None:
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
        if not value:
            raise RabbitCredentialsError("Rabbit user cannot be empty.")
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
        Retrieves the RabbitMQ password, setting it to the default 'guest' if not already set.

        Returns:
            str: The RabbitMQ password.

        Raises:
            RabbitCredentialsError: If the password is not a string or is empty.

        Logs:
            - Info: When the password is not set and defaults to 'guest'.
            - Debug: The current (masked) password value.
        """
        if self._rabbit_pass is None:
            self.logger.info("Rabbit password is not set, using default "
                             "password 'guest'.")
            self._rabbit_pass = "guest"
        if not isinstance(self._rabbit_pass, str):
            raise RabbitCredentialsError("Rabbit password must be a string.")
        if not self._rabbit_pass.strip():
            raise RabbitCredentialsError("Rabbit password cannot be empty.")
        masked_pass = '***' if self._rabbit_pass else self._rabbit_pass
        self.logger.debug("Current rabbit password: %s", masked_pass)
        return self._rabbit_pass

    @rabbit_pass.setter
    def rabbit_pass(self, value: str) -> None:
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
        if not value:
            raise RabbitCredentialsError("Rabbit password cannot be empty.")
        if not isinstance(value, str):
            raise RabbitCredentialsError("Rabbit password must be a string.")
        if not value.strip():
            raise RabbitCredentialsError("Rabbit password cannot be empty.")
        self.logger.debug("Setting rabbit password.")
        self._rabbit_pass = value
        self._url = None
