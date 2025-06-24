"""
Custom exceptions for the bunnystream package.

This module defines custom exception classes for handling errors
related to RabbitMQ configuration and connection parameters.
"""


class RabbitPortError(Exception):
    """Exception raised for errors in the RabbitMQ port configuration."""
    def __init__(self, message: str = "Rabbit port must be a positive integer "
                                      "or a string that can be converted to "
                                      "an integer."):
        super().__init__(message)


class RabbitHostError(Exception):
    """Exception raised for errors in the RabbitMQ host configuration."""
    def __init__(self, message: str = "Rabbit host cannot be empty."):
        super().__init__(message)


class RabbitVHostError(Exception):
    """Exception raised for errors in the RabbitMQ virtual host configuration."""
    def __init__(self, message: str = "Rabbit vhost must be a non-empty string."):
        super().__init__(message)


class RabbitCredentialsError(Exception):
    """Exception raised for errors in the RabbitMQ credentials configuration."""
    def __init__(self, message: str = "Rabbit credentials must be a non-empty string."):
        super().__init__(message)


class ExcangeNameError(Exception):
    """Exception raised for errors in the RabbitMQ exchange name configuration."""
    def __init__(self, message: str = "Exchange name must be a non-empty string."):
        super().__init__(message)
