"""
Custom exceptions for the bunnystream package.

This module defines custom exception classes for handling errors
related to RabbitMQ configuration and connection parameters.
"""

from typing import Union


class BunnyStreamError(Exception):
    """Base class for all BunnyStream exceptions."""

    def __init__(self, message: str = "An error occurred in BunnyStream."):
        super().__init__(message)


class RabbitPortError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ port configuration."""

    def __init__(
        self,
        message: str = "Rabbit port must be a positive integer "
        "or a string that can be converted to "
        "an integer.",
    ):
        super().__init__(message)


class RabbitHostError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ host configuration."""

    def __init__(self, message: str = "Rabbit host cannot be empty."):
        super().__init__(message)


class RabbitVHostError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ virtual host configuration."""

    def __init__(self, message: str = "Rabbit vhost must be a non-empty string."):
        super().__init__(message)


class RabbitCredentialsError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ credentials configuration."""

    def __init__(self, message: str = "Rabbit credentials must be a non-empty string."):
        super().__init__(message)


class ExcangeNameError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ exchange name configuration."""

    def __init__(self, message: str = "Exchange name must be a non-empty string."):
        super().__init__(message)


class PrefetchCountError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ prefetch count configuration."""

    def __init__(self, message: str = "Prefetch count must be a positive integer."):
        super().__init__(message)


class BunnyStreamModeError(BunnyStreamError):
    """Exception raised for errors in the BunnyStream mode configuration."""

    def __init__(
        self,
        message: Union[str, None] = None,
        value: Union[str, None] = None,
        valid_modes: Union[list, None] = None,
    ):
        if value is not None and valid_modes is not None:
            message = (
                f"BunnyStream mode '{value}' is invalid. "
                f"Valid modes are: {', '.join(valid_modes)}."
            )
        if message is None:
            message = "BunnyStream mode must be either 'producer' or 'consumer'."
        super().__init__(message)


class SSLOptionsError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ SSL options configuration."""

    def __init__(self) -> None:
        message = """
        BunnyStream uses the pika library for RabbitMQ connections.
        The SSLOptions class is provided by pika please refer to the pika documentation for more information:
        https://pika.readthedocs.io/en/stable/modules/parameters.html#pika.connection.ConnectionParameters.ssl_options
        """  # noqa: E501
        super().__init__(message)


class InvalidTCPOptionsError(BunnyStreamError):
    """Exception raised for errors in the RabbitMQ TCP options configuration."""

    def __init__(
        self,
        message: str = "TCP options must be a dictionary with valid TCP parameters.",
    ):
        super().__init__(message)


class BunnyStreamConfigurationError(BunnyStreamError):
    """Exception raised for errors in the BunnyStream configuration."""

    def __init__(self, message: str = "BunnyStream configuration is invalid."):
        super().__init__(message)


class SubscriptionsNotSetError(BunnyStreamError):
    """Exception raised when subscriptions are not set in BunnyStream."""

    def __init__(
        self,
        message: str = ("Subscriptions must be set before starting the BunnyStream consumer."),
    ):
        super().__init__(message)


class WarrenNotConfigured(BunnyStreamError):
    """Exception raised when the Warren instance is not configured."""

    def __init__(self, message: str = "Warren instance is not configured."):
        super().__init__(message)


class WarrenNotConnected(BunnyStreamError):
    """Exception raised when the Warren instance is not connected."""

    def __init__(self, message: str = "Warren instance is not connected."):
        super().__init__(message)
