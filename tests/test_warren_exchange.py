"""
Comprehensive tests for Warren exchange_name functionality and environment variables.

This module tests all aspects of the exchange_name property including:
- Environment variable handling (BUNNYSTREAM_EXCHANGE_NAME)
- Property getter and setter validation
- Error handling for invalid exchange names
- Default value behavior
"""
import os
import pytest
from unittest.mock import patch
from bunnystream.warren import Warren
from bunnystream.exceptions import ExcangeNameError


class TestWarrenExchangeName:
    """Test Warren exchange_name property functionality."""

    def test_exchange_name_default_initialization(self):
        """Test that exchange_name defaults to 'bunnystream_exchange'."""
        warren = Warren(rabbit_host="localhost")
        assert warren.exchange_name == "bunnystream_exchange"

    def test_exchange_name_custom_initialization(self):
        """Test that custom exchange_name is set during initialization."""
        custom_name = "my_custom_exchange"
        warren = Warren(rabbit_host="localhost", exchange_name=custom_name)
        assert warren.exchange_name == custom_name

    def test_exchange_name_getter_with_none_sets_default(self):
        """Test that getter sets default when _exchange_name is None."""
        warren = Warren(rabbit_host="localhost")
        # Manually set to None to test the getter logic
        warren._exchange_name = None  # pylint: disable=protected-access
        assert warren.exchange_name == "bunnystream_exchange"

    def test_exchange_name_getter_invalid_type_error(self):
        """Test that getter raises error when _exchange_name is not a string."""
        warren = Warren(rabbit_host="localhost")
        # Manually set to invalid type to test error handling
        setattr(warren, '_exchange_name', 123)  # pylint: disable=protected-access
        with pytest.raises(ExcangeNameError, match="Exchange name must be a string"):
            _ = warren.exchange_name

    def test_exchange_name_getter_empty_string_error(self):
        """Test that getter raises error when _exchange_name is empty."""
        warren = Warren(rabbit_host="localhost")
        # Manually set to empty string to test error handling
        setattr(warren, '_exchange_name', "   ")  # pylint: disable=protected-access
        with pytest.raises(ExcangeNameError, match="Exchange name cannot be empty"):
            _ = warren.exchange_name

    def test_exchange_name_setter_valid_string(self):
        """Test setting exchange_name with valid string."""
        warren = Warren(rabbit_host="localhost")
        new_name = "new_exchange_name"
        warren.exchange_name = new_name
        assert warren.exchange_name == new_name

    def test_exchange_name_setter_invalid_type_error(self):
        """Test that setter raises error for non-string values."""
        warren = Warren(rabbit_host="localhost")
        with pytest.raises(ExcangeNameError, match="Exchange name must be a string"):
            setattr(warren, 'exchange_name', 123)  # Bypass type checking for test

    def test_exchange_name_setter_empty_string_error(self):
        """Test that setter raises error for empty strings."""
        warren = Warren(rabbit_host="localhost")
        with pytest.raises(ExcangeNameError, match="Exchange name cannot be empty"):
            warren.exchange_name = ""

    def test_exchange_name_setter_whitespace_only_error(self):
        """Test that setter raises error for whitespace-only strings."""
        warren = Warren(rabbit_host="localhost")
        with pytest.raises(ExcangeNameError, match="Exchange name cannot be empty"):
            warren.exchange_name = "   "


class TestWarrenExchangeNameEnvironment:
    """Test Warren exchange_name environment variable functionality."""

    @patch.dict(os.environ, {'BUNNYSTREAM_EXCHANGE_NAME': 'env_exchange'})
    def test_exchange_name_from_environment_variable(self):
        """Test that exchange_name is set from BUNNYSTREAM_EXCHANGE_NAME environment variable."""
        warren = Warren(rabbit_host="localhost")
        assert warren.exchange_name == "env_exchange"

    @patch.dict(os.environ, {'BUNNYSTREAM_EXCHANGE_NAME': 'env_exchange'})
    def test_exchange_name_environment_overrides_default(self):
        """Test that environment variable overrides default exchange_name."""
        warren = Warren(rabbit_host="localhost", exchange_name="param_exchange")
        # Environment variable should override the parameter
        assert warren.exchange_name == "env_exchange"

    @patch.dict(os.environ, {}, clear=True)
    def test_exchange_name_no_environment_uses_parameter(self):
        """Test that parameter is used when no environment variable is set."""
        warren = Warren(rabbit_host="localhost", exchange_name="param_exchange")
        assert warren.exchange_name == "param_exchange"

    @patch.dict(os.environ, {}, clear=True)
    def test_exchange_name_no_environment_uses_default(self):
        """Test that default is used when no environment variable or parameter is set."""
        warren = Warren(rabbit_host="localhost")
        assert warren.exchange_name == "bunnystream_exchange"


class TestWarrenExchangeNameIntegration:
    """Integration tests for exchange_name with other Warren functionality."""

    def test_exchange_name_with_all_parameters(self):
        """Test exchange_name works correctly with all other Warren parameters."""
        warren = Warren(
            rabbit_host="localhost",
            rabbit_port=5672,
            rabbit_vhost="/test",
            rabbit_user="testuser",
            rabbit_pass="testpass",
            exchange_name="test_exchange"
        )
        assert warren.exchange_name == "test_exchange"
        assert warren.rabbit_host == "localhost"
        assert warren.rabbit_port == 5672

    @patch.dict(os.environ, {
        'RABBITMQ_URL': 'amqp://user:pass@host:5672/vhost',
        'BUNNYSTREAM_EXCHANGE_NAME': 'env_exchange'
    })
    def test_exchange_name_with_rabbitmq_url_environment(self):
        """Test exchange_name environment variable works with RABBITMQ_URL."""
        warren = Warren()
        assert warren.exchange_name == "env_exchange"
        assert warren.rabbit_host == "host"
        assert warren.rabbit_port == 5672

    def test_exchange_name_property_updates(self):
        """Test that exchange_name can be updated after initialization."""
        warren = Warren(rabbit_host="localhost", exchange_name="initial_exchange")
        assert warren.exchange_name == "initial_exchange"
        
        warren.exchange_name = "updated_exchange"
        assert warren.exchange_name == "updated_exchange"

    def test_exchange_name_persistence(self):
        """Test that exchange_name value persists across property accesses."""
        warren = Warren(rabbit_host="localhost", exchange_name="persistent_exchange")
        # Access multiple times to ensure value persists
        assert warren.exchange_name == "persistent_exchange"
        assert warren.exchange_name == "persistent_exchange"
        assert warren.exchange_name == "persistent_exchange"
