"""
Test suite for the exceptions module.
"""

import pytest

from bunnystream.exceptions import (
    BunnyStreamError,
    ExcangeNameError,
    RabbitCredentialsError,
    RabbitHostError,
    RabbitPortError,
    RabbitVHostError,
    WarrenNotConfigured,
)


class TestExceptions:
    """Test all custom exceptions for default and custom messages."""

    def test_rabbit_port_error_default_message(self):
        """Test RabbitPortError with default message."""
        with pytest.raises(RabbitPortError) as exc_info:
            raise RabbitPortError()
        assert ("Rabbit port must be a positive integer or a string that can be converted") in str(
            exc_info.value
        )

    def test_rabbit_port_error_custom_message(self):
        """Test RabbitPortError with custom message."""
        custom_message = "Custom port error message"
        with pytest.raises(RabbitPortError) as exc_info:
            raise RabbitPortError(custom_message)
        assert custom_message in str(exc_info.value)

    def test_rabbit_host_error_default_message(self):
        """Test RabbitHostError with default message."""
        with pytest.raises(RabbitHostError) as exc_info:
            raise RabbitHostError()
        assert "Rabbit host cannot be empty." in str(exc_info.value)

    def test_rabbit_host_error_custom_message(self):
        """Test RabbitHostError with custom message."""
        custom_message = "Custom host error message"
        with pytest.raises(RabbitHostError) as exc_info:
            raise RabbitHostError(custom_message)
        assert custom_message in str(exc_info.value)

    def test_rabbit_vhost_error_default_message(self):
        """Test RabbitVHostError with default message."""
        with pytest.raises(RabbitVHostError) as exc_info:
            raise RabbitVHostError()
        assert "Rabbit vhost must be a non-empty string." in str(exc_info.value)

    def test_rabbit_vhost_error_custom_message(self):
        """Test RabbitVHostError with custom message."""
        custom_message = "Custom vhost error message"
        with pytest.raises(RabbitVHostError) as exc_info:
            raise RabbitVHostError(custom_message)
        assert custom_message in str(exc_info.value)

    def test_rabbit_credentials_error_default_message(self):
        """Test RabbitCredentialsError with default message."""
        with pytest.raises(RabbitCredentialsError) as exc_info:
            raise RabbitCredentialsError()
        assert "Rabbit credentials must be a non-empty string." in str(exc_info.value)

    def test_rabbit_credentials_error_custom_message(self):
        """Test RabbitCredentialsError with custom message."""
        custom_message = "Custom credentials error message"
        with pytest.raises(RabbitCredentialsError) as exc_info:
            raise RabbitCredentialsError(custom_message)
        assert custom_message in str(exc_info.value)

    def test_exchange_name_error_default_message(self):
        """Test ExcangeNameError with default message."""
        with pytest.raises(ExcangeNameError) as exc_info:
            raise ExcangeNameError()
        assert "Exchange name must be a non-empty string." in str(exc_info.value)

    def test_exchange_name_error_custom_message(self):
        """Test ExcangeNameError with custom message."""
        custom_message = "Custom exchange name error message"
        with pytest.raises(ExcangeNameError) as exc_info:
            raise ExcangeNameError(custom_message)
        assert custom_message in str(exc_info.value)

    def test_warren_not_configured_default_message(self):
        """Test ExcangeNameError with default message."""
        with pytest.raises(WarrenNotConfigured) as exc_info:
            raise WarrenNotConfigured()
        assert "Warren instance is not configured." in str(exc_info.value)

    def test_warren_not_configured_custom_message(self):
        """Test ExcangeNameError with custom message."""
        custom_message = "Custom exchange name error message"
        with pytest.raises(WarrenNotConfigured) as exc_info:
            raise WarrenNotConfigured(custom_message)
        assert custom_message in str(exc_info.value)

    def test_exceptions_inheritance(self):
        """Test that all custom exceptions inherit from Exception."""
        assert issubclass(RabbitPortError, BunnyStreamError)
        assert issubclass(RabbitHostError, BunnyStreamError)
        assert issubclass(RabbitVHostError, BunnyStreamError)
        assert issubclass(RabbitCredentialsError, BunnyStreamError)
        assert issubclass(ExcangeNameError, BunnyStreamError)
        assert issubclass(WarrenNotConfigured, BunnyStreamError)

    def test_exceptions_are_different_types(self):
        """Test that all exceptions are different types."""
        exceptions = [
            RabbitPortError(),
            RabbitHostError(),
            RabbitVHostError(),
            RabbitCredentialsError(),
            ExcangeNameError(),
            WarrenNotConfigured(),
        ]

        # Check that no two exceptions are of the same type
        for i, exc1 in enumerate(exceptions):
            for j, exc2 in enumerate(exceptions):
                if i != j:
                    assert type(exc1) is not type(exc2)
