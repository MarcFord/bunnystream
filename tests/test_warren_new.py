"""
Tests for the Warren class.

This module contains comprehensive tests for the Warren class,
covering connection management and configuration integration.
"""

from unittest.mock import Mock, patch

import pika
import pytest

from bunnystream.config import BunnyStreamConfig
from bunnystream.exceptions import BunnyStreamConfigurationError
from bunnystream.warren import Warren


class TestWarrenInitialization:
    """Test Warren class initialization."""

    def test_initialization_with_config(self):
        """Test Warren initialization with BunnyStreamConfig."""
        config = BunnyStreamConfig(mode="producer", exchange_name="test_exchange")
        warren = Warren(config)

        assert warren.config == config
        assert warren.config.exchange_name == "test_exchange"
        assert warren.config.mode == "producer"
        assert warren.rabbit_connection is None

    def test_initialization_sets_logger(self):
        """Test that Warren initialization sets up logger."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        assert hasattr(warren, "logger")
        assert warren.logger is not None


class TestWarrenConfigProperty:
    """Test Warren config property."""

    def test_config_getter(self):
        """Test config property getter."""
        config = BunnyStreamConfig(mode="producer", exchange_name="test")
        warren = Warren(config)

        retrieved_config = warren.config
        assert retrieved_config == config
        assert retrieved_config.exchange_name == "test"

    def test_config_setter_with_valid_config(self):
        """Test config property setter with valid BunnyStreamConfig."""
        initial_config = BunnyStreamConfig(mode="producer", exchange_name="initial")
        warren = Warren(initial_config)

        new_config = BunnyStreamConfig(mode="consumer", exchange_name="new")
        warren.config = new_config

        assert warren.config == new_config
        assert warren.config.exchange_name == "new"
        assert warren.config.mode == "consumer"

    def test_config_setter_with_invalid_config(self):
        """Test config property setter with invalid config type."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        with pytest.raises(BunnyStreamConfigurationError) as exc_info:
            warren.config = "invalid_config"

        assert "BunnyStreamConfig" in str(exc_info.value)

    def test_config_setter_with_none(self):
        """Test config property setter with None."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        with pytest.raises(BunnyStreamConfigurationError):
            warren.config = None


class TestWarrenBunnyModeProperty:
    """Test Warren bunny_mode property."""

    def test_bunny_mode_getter(self):
        """Test bunny_mode property getter."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        assert warren.bunny_mode == "producer"

    def test_bunny_mode_setter(self):
        """Test bunny_mode property setter."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        warren.bunny_mode = "consumer"
        assert warren.bunny_mode == "consumer"
        assert warren.config.mode == "consumer"

    def test_bunny_mode_setter_with_invalid_mode(self):
        """Test bunny_mode setter with invalid mode."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        with pytest.raises(Exception):  # Should propagate from config.mode setter
            warren.bunny_mode = "invalid_mode"


class TestWarrenConnectionProperty:
    """Test Warren rabbit_connection property."""

    def test_rabbit_connection_getter_initial_none(self):
        """Test that rabbit_connection is initially None."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        assert warren.rabbit_connection is None

    def test_rabbit_connection_after_setting(self):
        """Test rabbit_connection after manual setting."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_connection = Mock(spec=pika.SelectConnection)
        warren._rabbit_connection = mock_connection

        assert warren.rabbit_connection == mock_connection


class TestWarrenConnectionParameters:
    """Test Warren connection_parameters property."""

    def test_connection_parameters_creation(self):
        """Test that connection_parameters creates proper pika.ConnectionParameters."""
        config = BunnyStreamConfig(
            mode="producer",
            rabbit_host="test.host",
            rabbit_port=5673,
            rabbit_vhost="/test",
            rabbit_user="testuser",
            rabbit_pass="testpass",
        )
        warren = Warren(config)

        params = warren.connection_parameters

        assert isinstance(params, pika.ConnectionParameters)
        assert params.host == "test.host"
        assert params.port == 5673
        assert params.virtual_host == "/test"
        assert params.credentials.username == "testuser"
        assert params.credentials.password == "testpass"

    def test_connection_parameters_with_defaults(self):
        """Test connection_parameters with default config values."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        params = warren.connection_parameters

        assert isinstance(params, pika.ConnectionParameters)
        assert params.host == "localhost"
        assert params.port == 5672
        assert params.virtual_host == "/"
        assert params.credentials.username == "guest"
        assert params.credentials.password == "guest"

    def test_connection_parameters_includes_advanced_settings(self):
        """Test that connection_parameters includes advanced settings."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        params = warren.connection_parameters

        # Test that advanced parameters are included
        assert hasattr(params, "channel_max")
        assert hasattr(params, "frame_max")
        assert hasattr(params, "heartbeat")
        assert hasattr(params, "blocked_connection_timeout")


class TestWarrenConnect:
    """Test Warren connect method."""

    @patch("pika.SelectConnection")
    def test_connect_creates_connection(self, mock_select_connection):
        """Test that connect() creates a SelectConnection."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_connection_instance = Mock()
        mock_select_connection.return_value = mock_connection_instance

        warren.connect()

        # Verify SelectConnection was called with correct parameters
        mock_select_connection.assert_called_once()
        call_args = mock_select_connection.call_args

        # Check that parameters were passed
        assert "parameters" in call_args.kwargs
        assert "on_open_callback" in call_args.kwargs
        assert "on_open_error_callback" in call_args.kwargs
        assert "on_close_callback" in call_args.kwargs

        # Check that connection was stored
        assert warren._rabbit_connection == mock_connection_instance

    @patch("pika.SelectConnection")
    def test_connect_only_once(self, mock_select_connection):
        """Test that connect() doesn't create multiple connections."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_connection_instance = Mock()
        warren._rabbit_connection = mock_connection_instance

        warren.connect()

        # SelectConnection should not be called if connection exists
        mock_select_connection.assert_not_called()
        assert warren._rabbit_connection == mock_connection_instance


class TestWarrenCallbacks:
    """Test Warren callback methods."""

    def test_on_connection_open_callback(self):
        """Test on_connection_open callback."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_connection = Mock(spec=pika.SelectConnection)

        # Test the callback doesn't raise errors
        warren.on_connection_open(mock_connection)

        # Verify channel is requested
        mock_connection.channel.assert_called_once_with(on_open_callback=warren.on_channel_open)

    def test_on_channel_open_callback(self):
        """Test on_channel_open callback."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_channel = Mock()

        # Test the callback doesn't raise errors
        warren.on_channel_open(mock_channel)

    def test_on_connection_error_callback(self):
        """Test on_connection_error callback."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_connection = Mock(spec=pika.SelectConnection)
        test_error = Exception("Test error")

        warren.on_connection_error(mock_connection, test_error)

        # Connection should be reset to None
        assert warren._rabbit_connection is None

    def test_on_connection_closed_callback(self):
        """Test on_connection_closed callback."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_connection = Mock(spec=pika.SelectConnection)
        reason = "Connection closed for testing"

        warren.on_connection_closed(mock_connection, reason)

        # Connection should be reset to None
        assert warren._rabbit_connection is None

    def test_on_connection_closed_callback_with_none_reason(self):
        """Test on_connection_closed callback with None reason."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        mock_connection = Mock(spec=pika.SelectConnection)

        warren.on_connection_closed(mock_connection, None)

        # Connection should be reset to None
        assert warren._rabbit_connection is None


class TestWarrenIntegration:
    """Integration tests for Warren class."""

    def test_complete_warren_workflow(self):
        """Test a complete Warren workflow."""
        # Create configuration
        config = BunnyStreamConfig(
            mode="producer",
            exchange_name="integration_test",
            rabbit_host="test.host",
            rabbit_port=5673,
            rabbit_user="testuser",
            rabbit_pass="testpass",
        )

        # Create Warren instance
        warren = Warren(config)

        # Verify configuration is properly set
        assert warren.config == config
        assert warren.bunny_mode == "producer"
        assert warren.rabbit_connection is None

        # Test connection parameters
        params = warren.connection_parameters
        assert params.host == "test.host"
        assert params.port == 5673
        assert params.credentials.username == "testuser"
        assert params.credentials.password == "testpass"

        # Test configuration updates
        new_config = BunnyStreamConfig(mode="consumer", exchange_name="new_exchange")
        warren.config = new_config

        assert warren.config == new_config
        assert warren.bunny_mode == "consumer"

    @patch("pika.SelectConnection")
    def test_warren_with_mocked_connection(self, mock_select_connection):
        """Test Warren with mocked pika connection."""
        config = BunnyStreamConfig(mode="consumer")
        warren = Warren(config)

        mock_connection_instance = Mock()
        mock_select_connection.return_value = mock_connection_instance

        # Test connection establishment
        warren.connect()

        # Verify connection was created and stored
        assert warren.rabbit_connection == mock_connection_instance
        mock_select_connection.assert_called_once()

        # Test callbacks
        warren.on_connection_open(mock_connection_instance)
        warren.on_connection_error(mock_connection_instance, Exception("test"))
        assert warren.rabbit_connection is None  # Should be reset by error callback

    def test_warren_config_validation(self):
        """Test Warren validates configuration properly."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        # Test that Warren enforces config validation
        with pytest.raises(BunnyStreamConfigurationError):
            warren.config = {"invalid": "config"}

        with pytest.raises(BunnyStreamConfigurationError):
            warren.config = None

        # Verify original config is unchanged
        assert warren.config == config


class TestWarrenLogging:
    """Test Warren logging functionality."""

    def test_logger_initialization(self):
        """Test that Warren initializes logger correctly."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        assert hasattr(warren, "logger")
        assert warren.logger is not None
        # Logger should be named 'warren'
        assert "warren" in warren.logger.name

    @patch("bunnystream.warren.get_bunny_logger")
    def test_logger_called_with_correct_name(self, mock_get_logger):
        """Test that get_bunny_logger is called with correct name."""
        config = BunnyStreamConfig(mode="producer")
        Warren(config)

        mock_get_logger.assert_called_with("warren")


class TestWarrenEdgeCases:
    """Test Warren edge cases and error conditions."""

    def test_warren_with_minimal_config(self):
        """Test Warren with minimal configuration."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        # Should work with defaults
        assert warren.config.rabbit_host == "localhost"
        assert warren.config.rabbit_port == 5672
        assert warren.bunny_mode == "producer"

        # Connection parameters should be valid
        params = warren.connection_parameters
        assert isinstance(params, pika.ConnectionParameters)

    def test_warren_mode_changes(self):
        """Test Warren mode changes through bunny_mode property."""
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        assert warren.bunny_mode == "producer"

        warren.bunny_mode = "consumer"
        assert warren.bunny_mode == "consumer"
        assert warren.config.mode == "consumer"

    def test_config_replacement_preserves_functionality(self):
        """Test that replacing config preserves Warren functionality."""
        original_config = BunnyStreamConfig(mode="producer", exchange_name="original")
        warren = Warren(original_config)

        new_config = BunnyStreamConfig(mode="consumer", exchange_name="replacement")
        warren.config = new_config

        # All functionality should work with new config
        assert warren.bunny_mode == "consumer"
        params = warren.connection_parameters
        assert isinstance(params, pika.ConnectionParameters)

        # Original config should not affect Warren anymore
        original_config.mode = "producer"  # This shouldn't affect warren
        assert warren.bunny_mode == "consumer"
