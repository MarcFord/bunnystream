"""
Tests for the BunnyStreamConfig class.

This module contains comprehensive tests for the BunnyStreamConfig class,
covering configuration management, validation, and environment variable parsing.
"""

import os
from unittest.mock import patch

import pytest

from bunnystream.config import (
    DEFAULT_EXCHANGE_NAME,
    DEFAULT_PREFETCH_COUNT,
    BunnyStreamConfig,
)
from bunnystream.exceptions import (
    BunnyStreamModeError,
    ExcangeNameError,
    PrefetchCountError,
    RabbitCredentialsError,
    RabbitHostError,
    RabbitPortError,
    RabbitVHostError,
    InvalidTCPOptionsError,
    SubscriptionsNotSetError,
    SSLOptionsError,
)
from bunnystream.logger import get_bunny_logger
from bunnystream.subscription import Subscription


class TestBunnyStreamConfigInitialization:
    """Test BunnyStreamConfig initialization."""

    def test_default_initialization(self):
        """Test BunnyStreamConfig with minimal parameters."""
        config = BunnyStreamConfig(mode="producer")

        assert config.mode == "producer"
        assert config.rabbit_host == "localhost"
        assert config.rabbit_port == 5672
        assert config.rabbit_vhost == "/"
        assert config.rabbit_user == "guest"
        assert config.rabbit_pass == "guest"
        assert config.exchange_name == "bunnystream"

    def test_initialization_with_all_parameters(self):
        """Test BunnyStreamConfig with all parameters provided."""
        config = BunnyStreamConfig(
            mode="consumer",
            exchange_name="test_exchange",
            rabbit_host="test.host.com",
            rabbit_port=5673,
            rabbit_vhost="/test",
            rabbit_user="testuser",
            rabbit_pass="testpass",
        )

        assert config.mode == "consumer"
        assert config.exchange_name == "test_exchange"
        assert config.rabbit_host == "test.host.com"
        assert config.rabbit_port == 5673
        assert config.rabbit_vhost == "/test"
        assert config.rabbit_user == "testuser"
        assert config.rabbit_pass == "testpass"

    def test_initialization_with_partial_parameters(self):
        """Test BunnyStreamConfig with some parameters provided."""
        config = BunnyStreamConfig(
            mode="producer", rabbit_host="myhost.com", rabbit_port=6672
        )

        assert config.mode == "producer"
        assert config.rabbit_host == "myhost.com"
        assert config.rabbit_port == 6672
        assert config.rabbit_vhost == "/"  # Default
        assert config.rabbit_user == "guest"  # Default
        assert config.rabbit_pass == "guest"  # Default


class TestBunnyStreamConfigModeProperty:
    """Test BunnyStreamConfig mode property."""

    def test_mode_getter_with_valid_mode(self):
        """Test mode getter with valid mode."""
        config = BunnyStreamConfig(mode="producer")
        assert config.mode == "producer"

    def test_mode_setter_with_valid_mode(self):
        """Test mode setter with valid mode."""
        config = BunnyStreamConfig(mode="producer")
        config.mode = "consumer"
        assert config.mode == "consumer"

    def test_mode_setter_with_invalid_mode(self):
        """Test mode setter with invalid mode."""
        config = BunnyStreamConfig(mode="producer")
        with pytest.raises(BunnyStreamModeError) as exc_info:
            config.mode = "invalid_mode"
        assert "invalid_mode" in str(exc_info.value)
        assert "producer" in str(exc_info.value)
        assert "consumer" in str(exc_info.value)

    def test_mode_setter_with_none(self):
        """Test mode setter with None."""
        config = BunnyStreamConfig(mode="producer")
        with pytest.raises(BunnyStreamModeError):
            config.mode = None

    def test_mode_setter_with_empty_string(self):
        """Test mode setter with empty string."""
        config = BunnyStreamConfig(mode="producer")
        with pytest.raises(BunnyStreamModeError):
            config.mode = ""


class TestBunnyStreamConfigRabbitProperties:
    """Test BunnyStreamConfig RabbitMQ properties."""

    def test_rabbit_host_property(self):
        """Test rabbit_host property getter and setter."""
        config = BunnyStreamConfig(mode="producer")

        # Test getter
        assert config.rabbit_host == "localhost"

        # Test setter
        config.rabbit_host = "newhost.com"
        assert config.rabbit_host == "newhost.com"

    def test_rabbit_host_setter_with_invalid_values(self):
        """Test rabbit_host setter with invalid values."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(RabbitHostError):
            config.rabbit_host = ""

        with pytest.raises(RabbitHostError):
            config.rabbit_host = "   "

        with pytest.raises(RabbitHostError):
            config.rabbit_host = None

    def test_rabbit_port_property(self):
        """Test rabbit_port property getter and setter."""
        config = BunnyStreamConfig(mode="producer")

        # Test getter
        assert config.rabbit_port == 5672

        # Test setter
        config.rabbit_port = 5673
        assert config.rabbit_port == 5673

    def test_rabbit_port_setter_with_string(self):
        """Test rabbit_port setter with string value."""
        config = BunnyStreamConfig(mode="producer")
        config.rabbit_port = "5674"
        assert config.rabbit_port == 5674

    def test_rabbit_port_setter_with_invalid_values(self):
        """Test rabbit_port setter with invalid values."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(RabbitPortError):
            config.rabbit_port = 0

        with pytest.raises(RabbitPortError):
            config.rabbit_port = -1

        with pytest.raises(RabbitPortError):
            config.rabbit_port = "invalid"

    def test_rabbit_vhost_property(self):
        """Test rabbit_vhost property getter and setter."""
        config = BunnyStreamConfig(mode="producer")

        # Test getter
        assert config.rabbit_vhost == "/"

        # Test setter
        config.rabbit_vhost = "/test"
        assert config.rabbit_vhost == "/test"

    def test_rabbit_vhost_setter_with_invalid_values(self):
        """Test rabbit_vhost setter with invalid values."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(RabbitVHostError):
            config.rabbit_vhost = ""

        with pytest.raises(RabbitVHostError):
            config.rabbit_vhost = "   "

    def test_rabbit_credentials_properties(self):
        """Test rabbit_user and rabbit_pass properties."""
        config = BunnyStreamConfig(mode="producer")

        # Test getters
        assert config.rabbit_user == "guest"
        assert config.rabbit_pass == "guest"

        # Test setters
        config.rabbit_user = "newuser"
        config.rabbit_pass = "newpass"
        assert config.rabbit_user == "newuser"
        assert config.rabbit_pass == "newpass"

    def test_rabbit_credentials_setter_with_invalid_values(self):
        """Test rabbit credentials setters with invalid values."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(RabbitCredentialsError):
            config.rabbit_user = ""

        with pytest.raises(RabbitCredentialsError):
            config.rabbit_user = "   "

        with pytest.raises(RabbitCredentialsError):
            config.rabbit_pass = ""

        with pytest.raises(RabbitCredentialsError):
            config.rabbit_pass = "   "


class TestBunnyStreamConfigExchangeName:
    """Test BunnyStreamConfig exchange_name property."""

    def test_exchange_name_default_initialization(self):
        """Test exchange_name with default initialization."""
        config = BunnyStreamConfig(mode="producer")
        assert config.exchange_name == "bunnystream"

    def test_exchange_name_custom_initialization(self):
        """Test exchange_name with custom initialization."""
        config = BunnyStreamConfig(mode="producer", exchange_name="custom_exchange")
        assert config.exchange_name == "custom_exchange"

    def test_exchange_name_setter_valid_string(self):
        """Test exchange_name setter with valid string."""
        config = BunnyStreamConfig(mode="producer")
        config.exchange_name = "new_exchange"
        assert config.exchange_name == "new_exchange"

    def test_exchange_name_setter_invalid_values(self):
        """Test exchange_name setter with invalid values."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ExcangeNameError):
            config.exchange_name = ""

        with pytest.raises(ExcangeNameError):
            config.exchange_name = "   "

        with pytest.raises(ExcangeNameError):
            config.exchange_name = None


class TestBunnyStreamConfigEnvironmentVariables:
    """Test BunnyStreamConfig environment variable parsing."""

    @patch.dict(os.environ, {}, clear=True)
    def test_no_environment_variable_uses_defaults(self):
        """Test that no environment variables results in default values."""
        config = BunnyStreamConfig(mode="producer")

        assert config.rabbit_host == "localhost"
        assert config.rabbit_port == 5672
        assert config.rabbit_vhost == "/"
        assert config.rabbit_user == "guest"
        assert config.rabbit_pass == "guest"

    @patch.dict(os.environ, {"RABBITMQ_URL": "amqp://user:pass@host:5673/vhost"})
    def test_full_rabbitmq_url_parsing(self):
        """Test parsing of complete RABBITMQ_URL environment variable."""
        config = BunnyStreamConfig(mode="producer")

        assert config.rabbit_host == "host"
        assert config.rabbit_port == 5673
        assert config.rabbit_vhost == "/vhost"
        assert config.rabbit_user == "user"
        assert config.rabbit_pass == "pass"

    @patch.dict(
        os.environ, {"RABBITMQ_URL": "amqps://user:pass@secure.host:5671/secure_vhost"}
    )
    def test_amqps_scheme_parsing(self):
        """Test parsing of AMQPS scheme in RABBITMQ_URL."""
        config = BunnyStreamConfig(mode="producer")

        assert config.rabbit_host == "secure.host"
        assert config.rabbit_port == 5671
        assert config.rabbit_vhost == "/secure_vhost"
        assert config.rabbit_user == "user"
        assert config.rabbit_pass == "pass"

    @patch.dict(os.environ, {"RABBITMQ_URL": "amqp://localhost"})
    def test_minimal_rabbitmq_url_parsing(self):
        """Test parsing of minimal RABBITMQ_URL."""
        config = BunnyStreamConfig(mode="producer")

        assert config.rabbit_host == "localhost"
        assert config.rabbit_port == 5672  # Default
        assert config.rabbit_vhost == "/"  # Default
        assert config.rabbit_user == "guest"  # Default
        assert config.rabbit_pass == "guest"  # Default

    @patch.dict(os.environ, {"RABBITMQ_URL": "amqp://user:pass@host:5673/"})
    def test_url_with_default_vhost(self):
        """Test URL parsing with default vhost (/)."""
        config = BunnyStreamConfig(mode="producer")

        assert config.rabbit_host == "host"
        assert config.rabbit_port == 5673
        assert config.rabbit_vhost == "/"
        assert config.rabbit_user == "user"
        assert config.rabbit_pass == "pass"

    @patch.dict(os.environ, {"RABBITMQ_URL": "amqp://user:pass@host:5673/custom"})
    def test_constructor_parameters_override_environment(self):
        """Test that constructor parameters override environment variables."""
        config = BunnyStreamConfig(
            mode="producer",
            rabbit_host="override.host",
            rabbit_port=9999,
            rabbit_user="override_user",
        )

        assert config.rabbit_host == "override.host"
        assert config.rabbit_port == 9999
        assert config.rabbit_user == "override_user"
        # These should come from environment
        assert config.rabbit_pass == "pass"
        assert config.rabbit_vhost == "/custom"

    @patch.dict(os.environ, {"RABBITMQ_URL": "invalid://invalid"})
    def test_invalid_url_scheme_raises_error(self):
        """Test that invalid URL scheme raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            BunnyStreamConfig(mode="producer")
        assert "Invalid URL scheme" in str(exc_info.value)

    @patch.dict(os.environ, {"RABBITMQ_URL": "not_a_valid_url"})
    def test_malformed_url_raises_error(self):
        """Test that malformed URL raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            BunnyStreamConfig(mode="producer")
        assert "Invalid RABBITMQ_URL format" in str(exc_info.value)


class TestBunnyStreamConfigSubscriptions:
    """Test BunnyStreamConfig subscription management."""

    def test_default_subscription_created(self):
        """Test that a default subscription is created."""
        config = BunnyStreamConfig(mode="consumer", exchange_name="test_exchange")

        subscriptions = config.subscriptions
        assert len(subscriptions) == 1
        assert subscriptions[0].exchange_name == "test_exchange"
        assert isinstance(subscriptions[0], Subscription)
        # Check that "test_exchange" is in config.subscription_mappings
        assert "test_exchange" in config.subscription_mappings
        assert isinstance(config.subscription_mappings["test_exchange"], dict)

    def test_subscription_mappings_raises_error_when_subscriptions_none(self):
        """Test that accessing subscription_mappings raises error when subscriptions are None."""
        config = BunnyStreamConfig(mode="consumer")
        config._subscriptions = None

        with pytest.raises(SubscriptionsNotSetError, match="Subscriptions have not been set."):
            _ = config.subscription_mappings

    def test_subscription_mappings_returns_dict_correctly(self):
        """Test that subscription_mappings returns a dict of subscriptions."""
        config = BunnyStreamConfig(mode="consumer", exchange_name="test_exchange")

        mappings = config.subscription_mappings
        assert isinstance(mappings, dict)
        assert "test_exchange" in mappings
        assert isinstance(mappings["test_exchange"], dict)

        # Check that the default subscription is in the mappings
        assert len(mappings) == 1
        print(mappings["test_exchange"])
        assert mappings["test_exchange"]["topics"] == []
        assert mappings["test_exchange"]["type"] == 'topic'

    def test_add_subscription(self):
        """Test adding a new subscription."""
        config = BunnyStreamConfig(mode="consumer")

        new_subscription = Subscription(exchange_name="custom_exchange")
        config.add_subscription(new_subscription)

        subscriptions = config.subscriptions
        assert len(subscriptions) == 2  # Default + new
        # Check if custom_exchange subscription exists
        exchange_names = [sub.exchange_name for sub in subscriptions]
        assert "custom_exchange" in exchange_names
        # Find the custom subscription
        custom_sub = next(
            sub for sub in subscriptions if sub.exchange_name == "custom_exchange"
        )
        assert custom_sub == new_subscription
        assert "custom_exchange" in config.subscription_mappings
        assert isinstance(config.subscription_mappings["custom_exchange"], dict)

    def test_remove_subscription(self):
        """Test removing a subscription."""
        config = BunnyStreamConfig(mode="consumer", exchange_name="test_exchange")

        # Remove the default subscription
        config.remove_subscription("test_exchange")

        subscriptions = config.subscriptions
        assert len(subscriptions) == 0
        assert "test_exchange" not in subscriptions
        assert "test_exchange" not in config.subscription_mappings

    def test_remove_nonexistent_subscription(self):
        """Test removing a subscription that does not exist."""
        config = BunnyStreamConfig(mode="consumer")

        # Attempt to remove a non-existent subscription
        with pytest.raises(ValueError, match="Subscription for exchange 'nonexistent' not found"):
            config.remove_subscription("nonexistent")

    def test_remove_subscription_with_no_subscriptions(self):
        """Test removing a subscription when no subscriptions exist."""
        config = BunnyStreamConfig(mode="consumer")

        # Remove the default subscription
        config._subscriptions = None
        with pytest.raises(SubscriptionsNotSetError, match="Subscriptions have not been set."):
            config.remove_subscription("test_exchange")

    def test_add_subscription_works_when_subscriptions_are_none(self):
        """Test adding a subscription when subscriptions are None."""
        config = BunnyStreamConfig(mode="consumer")
        config._subscriptions = None
        new_subscription = Subscription(exchange_name="new_exchange")
        config.add_subscription(new_subscription)
        assert len(config.subscriptions) == 1

    def test_add_subscription_raises_error_when_given_bad_type(self):
        """Test adding a subscription with an invalid type."""
        config = BunnyStreamConfig(mode="consumer")

        with pytest.raises(ValueError, match="Subscription must be an instance of Subscription."):
            config.add_subscription("not_a_subscription")

    def test_subscriptions_raises_error_when_none(self):
        """Test that accessing subscriptions raises error when they are None."""
        config = BunnyStreamConfig(mode="consumer")
        config._subscriptions = None

        with pytest.raises(SubscriptionsNotSetError, match="Subscriptions have not been set."):
            _ = config.subscriptions


class TestBunnyStreamConfigAdvancedProperties:
    """Test BunnyStreamConfig advanced properties."""

    def test_prefetch_count_property(self):
        """Test prefetch_count property."""
        config = BunnyStreamConfig(mode="consumer")

        # Test default
        assert config.prefetch_count >= 0

        # Test setter
        config.prefetch_count = 10
        assert config.prefetch_count == 10

    def test_prefetch_count_setter_with_invalid_values(self):
        """Test prefetch_count setter with invalid values."""
        config = BunnyStreamConfig(mode="consumer")

        with pytest.raises(PrefetchCountError):
            config.prefetch_count = -1

    def test_connection_parameters_properties(self):
        """Test connection parameter properties."""
        config = BunnyStreamConfig(mode="producer")

        # Test default values
        assert config.channel_max is not None
        assert config.frame_max is not None
        assert config.connection_attempts is not None
        assert config.retry_delay is not None
        assert config.socket_timeout is not None
        assert config.stack_timeout is not None
        assert config.locale is not None

    def test_locale_setter_raises_error_on_empty_string(self):
        """Test locale setter raises error on empty string."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ValueError, match="RabbitMQ locale cannot be empty."):
            config.locale = ""

    def test_locale_setter_raises_error_for_non_string(self):
        """Test locale setter raises error for non-string values."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ValueError, match="RabbitMQ locale must be a string."):
            config.locale = 123

    @patch.dict(os.environ, {"RABBITMQ_LOCALE": ""})
    def test_locale_getter_uses_default_on_bad_environment_value(self):
        """Test locale getter uses default when environment value is invalid."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should not override the default
        assert config.locale == "en_US"

    def test_locale_getter_uses_stored_value(self):
        """Test locale getter uses stored value."""
        config = BunnyStreamConfig(mode="producer")
        config._locale = "fr_FR"

        # Should return the stored value
        assert config.locale == "fr_FR"

    def test_ssl_options_setter_raises_error_on_invalid_type(self):
        """Test ssl_options setter raises error on invalid type."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(SSLOptionsError):
            config.ssl_options = "not_a_valid_ssl_options"

    def test_ssl_options_setter_normal_case(self):
        """Test ssl_options setter with valid SSLOptions."""
        from pika import SSLOptions
        from ssl import SSLContext
        config = BunnyStreamConfig(mode="producer")
        ssl_options = SSLOptions(
            SSLContext(),  # Using default SSLContext for testing
            server_hostname="test.server",
        )
        config.ssl_options = ssl_options
        assert isinstance(config.ssl_options, SSLOptions)

    def test_ssl_options_getter_returns_default(self):
        """Test ssl_options getter returns default when not set."""
        config = BunnyStreamConfig(mode="producer")
        assert config.ssl_options is None

    def test_ssl_port_setter_raises_error_on_invalid_type(self):
        """Test ssl_port setter raises error on invalid type."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ValueError, match="SSL port must be an integer."):
            config.ssl_port = "not_an_integer"

    def test_ssl_port_setter_raises_error_on_negative_value(self):
        """Test ssl_port setter raises error on negative value."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ValueError, match="SSL port must be a positive integer."):
            config.ssl_port = -1

    def test_ssl_port_setter_normal_case(self):
        """Test ssl_port setter with valid integer."""
        config = BunnyStreamConfig(mode="producer")
        config.ssl_port = 5671
        assert config.ssl_port == 5671

    @patch.dict(os.environ, {"RABBITMQ_SSL_PORT": "-123"})
    def test_ssl_port_getter_uses_default_on_invalid_environment_value(self):
        """Test ssl_port getter uses default when environment value is invalid."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should not override the default
        assert config.ssl_port == 5671

    @patch.dict(os.environ, {"RABBITMQ_SSL_PORT": "123"})
    def test_ssl_port_getter_uses_valid_environment_value(self):
        """Test ssl_port getter uses default when environment value is invalid."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should not override the default
        assert config.ssl_port == 123

    def test_ssl_setter_raises_error_on_invalid_type(self):
        """Test ssl setter raises error on invalid type."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ValueError, match="SSL must be a boolean."):
            config.ssl = "not_a_boolean"

    def test_ssl_setter_normal_case(self):
        """Test ssl setter with valid boolean."""
        config = BunnyStreamConfig(mode="producer")
        config.ssl = True
        assert config.ssl is True

    @patch.dict(os.environ, {"RABBITMQ_SSL": "1"})
    def test_ssl_getter_uses_environment_value_1(self):
        """Test ssl getter uses environment value '1'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is True

    @patch.dict(os.environ, {"RABBITMQ_SSL": "TRUE"})
    def test_ssl_getter_uses_environment_value_TRUE(self):
        """Test ssl getter uses environment value 'TRUE'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is True

    @patch.dict(os.environ, {"RABBITMQ_SSL": "true"})
    def test_ssl_getter_uses_environment_value_true(self):
        """Test ssl getter uses environment value 'true'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is True

    @patch.dict(os.environ, {"RABBITMQ_SSL": "yes"})
    def test_ssl_getter_uses_environment_value_yes(self):
        """Test ssl getter uses environment value 'YES'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is True

    @patch.dict(os.environ, {"RABBITMQ_SSL": "YES"})
    def test_ssl_getter_uses_environment_value_yes(self):
        """Test ssl getter uses environment value 'yes'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is True

    @patch.dict(os.environ, {"RABBITMQ_SSL": "0"})
    def test_ssl_getter_uses_environment_value_0(self):
        """Test ssl getter uses environment value '0"""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is False

    @patch.dict(os.environ, {"RABBITMQ_SSL": "FALSE"})
    def test_ssl_getter_uses_environment_value_FALSE(self):
        """Test ssl getter uses environment value 'FALSE'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is False

    @patch.dict(os.environ, {"RABBITMQ_SSL": "false"})
    def test_ssl_getter_uses_environment_value_false(self):
        """Test ssl getter uses environment value 'false'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is False

    @patch.dict(os.environ, {"RABBITMQ_SSL": "no"})
    def test_ssl_getter_uses_environment_value_no(self):
        """Test ssl getter uses environment value 'no'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is False

    @patch.dict(os.environ, {"RABBITMQ_SSL": "NO"})
    def test_ssl_getter_uses_environment_value_NO(self):
        """Test ssl getter uses environment value 'NO'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is False

    @patch.dict(os.environ, {"RABBITMQ_SSL": "HAPPY"})
    def test_ssl_getter_uses_default_value_when_environment_value_bad(self):
        """Test ssl getter uses environment value 'HAPPY'."""
        config = BunnyStreamConfig(mode="producer")

        # Environment variable should override the default
        assert config.ssl is False

    def test_tcp_options_setter_allows_none(self):
        """Test tcp_options setter allows None."""
        config = BunnyStreamConfig(mode="producer")
        config.tcp_options = None
        assert config.tcp_options is None

    @patch.dict(os.environ, {"RABBITMQ_TCP_OPTIONS": '{"TCP_KEEPIDLE": 60, "TCP_KEEPINTVL": 10, "TCP_KEEPCNT": 5, "TCP_USER_TIMEOUT": 30000}'})
    def test_tcp_options_setter_with_valid_environment(self):
        """Test tcp_options setter with valid environment variable."""
        config = BunnyStreamConfig(mode="producer")
        tcp_options = {"TCP_KEEPIDLE": 60, "TCP_KEEPINTVL": 10, "TCP_KEEPCNT": 5, "TCP_USER_TIMEOUT": 30000}
        assert isinstance(config.tcp_options, dict)
        for key, value in tcp_options.items():
            assert key in config.tcp_options
            assert config.tcp_options[key] == value

    @patch.dict(os.environ, {"RABBITMQ_TCP_OPTIONS": '[bad_json'})
    def test_tcp_options_getter_with_invalid_jason_environment_value(self):
        """Test tcp_options getter with invalid environment variable."""
        config = BunnyStreamConfig(mode="producer")

        assert config.tcp_options is None  # Should fallback to None

    @patch.dict(os.environ, {"RABBITMQ_TCP_OPTIONS": '{"bad_json": 1}'})
    def test_tcp_options_getter_with_invalid_environment(self):
        """Test tcp_options getter with invalid environment variable."""
        config = BunnyStreamConfig(mode="producer")

        assert config.tcp_options is None  # Should fallback to None

    def test_socket_timeout_setter_with_invalid_type(self):
        """Test socket_timeout setter raises error on invalid type."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ValueError, match="Socket timeout must be a float or an integer."):
            config.socket_timeout = "not_a_number"

    def test_socket_timeout_setter_with_invalid_value(self):
        """Test socket_timeout setter raises error on invalid value."""
        config = BunnyStreamConfig(mode="producer")

        with pytest.raises(ValueError, match="Socket timeout must be a float or an integer."):
            config.socket_timeout = 0

    def test_socket_timeout_setter_with_valid_value(self):
        """Test socket_timeout setter with valid value."""
        config = BunnyStreamConfig(mode="producer")
        config.socket_timeout = 5.0
        assert config.socket_timeout == 5.0


class TestBunnyStreamConfigIntegration:
    """Integration tests for BunnyStreamConfig."""

    def test_complete_configuration_flow(self):
        """Test a complete configuration workflow."""
        # Create config with custom settings
        config = BunnyStreamConfig(
            mode="consumer",
            exchange_name="integration_test",
            rabbit_host="test.rabbitmq.com",
            rabbit_port=5673,
            rabbit_vhost="/test_vhost",
            rabbit_user="test_user",
            rabbit_pass="test_pass",
        )

        # Verify all settings
        assert config.mode == "consumer"
        assert config.exchange_name == "integration_test"
        assert config.rabbit_host == "test.rabbitmq.com"
        assert config.rabbit_port == 5673
        assert config.rabbit_vhost == "/test_vhost"
        assert config.rabbit_user == "test_user"
        assert config.rabbit_pass == "test_pass"

        # Verify subscription was created
        subscriptions = config.subscriptions
        assert len(subscriptions) == 1
        assert subscriptions[0].exchange_name == "integration_test"

        # Modify configuration
        config.exchange_name = "updated_exchange"
        config.rabbit_port = 5674

        # Verify changes
        assert config.exchange_name == "updated_exchange"
        assert config.rabbit_port == 5674

    @patch.dict(
        os.environ, {"RABBITMQ_URL": "amqp://env_user:env_pass@env.host:5999/env_vhost"}
    )
    def test_environment_and_parameter_interaction(self):
        """Test interaction between environment variables and constructor parameters."""
        config = BunnyStreamConfig(
            mode="producer",
            rabbit_host="param.host",  # This should override environment
            exchange_name="param_exchange",
        )

        # Constructor parameters should override environment
        assert config.rabbit_host == "param.host"
        assert config.exchange_name == "param_exchange"

        # Environment values should be used where not overridden
        assert config.rabbit_user == "env_user"
        assert config.rabbit_pass == "env_pass"
        assert config.rabbit_vhost == "/env_vhost"
        assert config.rabbit_port == 5999


class TestBunnyStreamConfigEdgeCases:
    """Test edge cases and error conditions for BunnyStreamConfig."""

    def test_mode_getter_without_mode_set(self):
        """Test that mode getter raises error when mode is not set."""
        # Create config without setting mode properly (using private attribute)
        config = BunnyStreamConfig.__new__(BunnyStreamConfig)
        config._mode = None
        config.logger = get_bunny_logger("test")

        with pytest.raises(BunnyStreamModeError):
            _ = config.mode

    def test_exchange_name_getter_with_default(self):
        """Test that exchange name returns default when not set."""
        config = BunnyStreamConfig(mode="consumer")
        config._exchange_name = None  # Reset to test default behavior

        assert config.exchange_name == DEFAULT_EXCHANGE_NAME

    def test_prefetch_count_default_when_zero(self):
        """Test that prefetch count returns default when set to zero."""
        config = BunnyStreamConfig(mode="consumer")
        config._prefetch_count = 0

        assert config.prefetch_count == DEFAULT_PREFETCH_COUNT

    def test_url_property_construction(self):
        """Test URL property construction."""
        config = BunnyStreamConfig(
            mode="consumer",
            rabbit_host="test.host",
            rabbit_port=5672,
            rabbit_user="testuser",
            rabbit_pass="testpass",
            rabbit_vhost="/testvhost",
        )

        expected_url = "amqp://testuser:testpass@test.host:5672//testvhost"
        assert config.url == expected_url

        # Test that url is cached
        assert config._url is not None
        assert config.url == expected_url

    def test_url_property_with_empty_password(self):
        """Test URL property when password is empty (should reject empty password)."""
        with pytest.raises(
            RabbitCredentialsError, match="Rabbit password cannot be empty"
        ):
            BunnyStreamConfig(
                mode="consumer",
                rabbit_host="test.host",
                rabbit_port=5672,
                rabbit_user="testuser",
                rabbit_pass="",
                rabbit_vhost="/testvhost",
            )

    def test_rabbit_port_none_fallback(self):
        """Test rabbit_port property when None, should return default."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_port = None

        # This should test the line: if self._rabbit_port is None:
        assert config.rabbit_port == 5672

    def test_rabbit_port_string_conversion_in_getter(self):
        """Test rabbit_port property with string conversion in getter."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_port = "8080"  # Set as string

        # This should test the string conversion logic in getter
        assert config.rabbit_port == 8080
        assert isinstance(config._rabbit_port, int)  # Should be converted to int

    def test_rabbit_port_invalid_string_in_getter(self):
        """Test rabbit_port property with invalid string in getter."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_port = "invalid"  # Set as invalid string

        # This should test the ValueError exception in getter
        with pytest.raises(RabbitPortError):
            _ = config.rabbit_port

    def test_rabbit_port_invalid_type_in_getter(self):
        """Test rabbit_port property with invalid type in getter."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_port = []  # Set as invalid type

        # This should test the type check in getter
        with pytest.raises(RabbitPortError):
            _ = config.rabbit_port

    def test_rabbit_port_negative_in_getter(self):
        """Test rabbit_port property with negative value in getter."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_port = -5  # Set as negative

        # This should test the positive value check in getter
        with pytest.raises(RabbitPortError):
            _ = config.rabbit_port


class TestBunnyStreamConfigGetterValidation:
    """Test validation in property getters."""

    def test_exchange_name_setter_with_non_string(self):
        """Test exchange name setter with non-string value."""
        config = BunnyStreamConfig(mode="consumer")
        with pytest.raises(ExcangeNameError):
            config.exchange_name = 123  # Not a string

    def test_exchange_name_setter_with_empty_string(self):
        """Test exchange name setter with empty string."""
        config = BunnyStreamConfig(mode="consumer")
        with pytest.raises(ExcangeNameError):
            config.exchange_name = "   "  # Empty/whitespace string

    def test_rabbit_host_getter_when_none(self):
        """Test rabbit host getter when internal value is None."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_host = None
        result = config.rabbit_host
        assert result == ""

    def test_rabbit_host_setter_with_amqp_prefix(self):
        """Test rabbit host setter rejects amqp:// prefix."""
        config = BunnyStreamConfig(mode="consumer")
        with pytest.raises(RabbitHostError, match="should not start with 'amqp://'"):
            config.rabbit_host = "amqp://test.host"

    def test_rabbit_vhost_getter_validation_when_not_string(self):
        """Test rabbit vhost getter validation when value is not a string."""
        config = BunnyStreamConfig(mode="consumer", rabbit_vhost="/test")
        config._rabbit_vhost = 123  # Set invalid type
        with pytest.raises(RabbitVHostError, match="must be a string"):
            _ = config.rabbit_vhost

    def test_rabbit_vhost_getter_validation_when_empty(self):
        """Test rabbit vhost getter validation when value is empty."""
        config = BunnyStreamConfig(mode="consumer", rabbit_vhost="/test")
        config._rabbit_vhost = "   "  # Set empty string
        with pytest.raises(RabbitVHostError, match="cannot be empty"):
            _ = config.rabbit_vhost

    def test_rabbit_vhost_getter_default_when_none(self):
        """Test rabbit vhost getter sets default when None."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_vhost = None
        result = config.rabbit_vhost
        assert result == "/"
        assert config._rabbit_vhost == "/"

    def test_rabbit_user_getter_validation_when_not_string(self):
        """Test rabbit user getter validation when value is not a string."""
        config = BunnyStreamConfig(mode="consumer", rabbit_user="testuser")
        config._rabbit_user = 123  # Set invalid type
        with pytest.raises(RabbitCredentialsError, match="must be a string"):
            _ = config.rabbit_user

    def test_rabbit_user_getter_validation_when_empty(self):
        """Test rabbit user getter validation when value is empty."""
        config = BunnyStreamConfig(mode="consumer", rabbit_user="testuser")
        config._rabbit_user = "   "  # Set empty string
        with pytest.raises(RabbitCredentialsError, match="cannot be empty"):
            _ = config.rabbit_user

    def test_rabbit_user_getter_default_when_none(self):
        """Test rabbit user getter sets default when None."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_user = None
        result = config.rabbit_user
        assert result == "guest"
        assert config._rabbit_user == "guest"

    def test_rabbit_pass_getter_validation_when_not_string(self):
        """Test rabbit pass getter validation when value is not a string."""
        config = BunnyStreamConfig(mode="consumer", rabbit_pass="testpass")
        config._rabbit_pass = 123  # Set invalid type
        with pytest.raises(RabbitCredentialsError, match="must be a string"):
            _ = config.rabbit_pass

    def test_rabbit_pass_getter_validation_when_empty(self):
        """Test rabbit pass getter validation when value is empty."""
        config = BunnyStreamConfig(mode="consumer", rabbit_pass="testpass")
        config._rabbit_pass = "   "  # Set empty string
        with pytest.raises(RabbitCredentialsError, match="cannot be empty"):
            _ = config.rabbit_pass

    def test_rabbit_pass_getter_default_when_none(self):
        """Test rabbit pass getter sets default when None."""
        config = BunnyStreamConfig(mode="consumer")
        config._rabbit_pass = None
        result = config.rabbit_pass
        assert result == "guest"
        assert config._rabbit_pass == "guest"

    def test_prefetch_count_setter_with_non_integer(self):
        """Test prefetch count setter with non-integer value."""
        config = BunnyStreamConfig(mode="consumer")
        with pytest.raises(PrefetchCountError, match="must be an integer"):
            config.prefetch_count = "10"  # String instead of int

    def test_prefetch_count_setter_with_zero_or_negative(self):
        """Test prefetch count setter with zero or negative value."""
        config = BunnyStreamConfig(mode="consumer")
        with pytest.raises(PrefetchCountError, match="must be a positive integer"):
            config.prefetch_count = 0

        with pytest.raises(PrefetchCountError, match="must be a positive integer"):
            config.prefetch_count = -5


class TestBunnyStreamConfigValidateTCPOptions:
    """Test BunnyStreamConfig TCP options validation."""

    def test_tcp_options_default(self):
        """Test default TCP options."""
        config = BunnyStreamConfig(mode="producer")
        assert config.tcp_options is None

    def test_tcp_options_custom(self):
        """Test custom TCP options."""
        custom_options = {
            "TCP_KEEPIDLE": False,
            "TCP_KEEPINTVL": False,
            "TCP_KEEPCNT": False,
            "TCP_USER_TIMEOUT": 5000
        }
        config = BunnyStreamConfig(mode="producer")
        config.tcp_options = custom_options
        assert config.tcp_options == custom_options

    def test_tcp_options_invalid_type(self):
        """Test TCP options with invalid type."""
        config = BunnyStreamConfig(mode="producer")
        with pytest.raises(InvalidTCPOptionsError, match="CP options must be a dictionary."):
            config.tcp_options = "invalid_type"

    def test_tcp_options_invalid_key(self):
        """Test TCP options with invalid key."""
        config = BunnyStreamConfig(mode="producer")
        with pytest.raises(InvalidTCPOptionsError):
            config.tcp_options = {"invalid_key": True}

    def test_tcp_options_empty_dict(self):
        """Test TCP options with invalid key."""
        config = BunnyStreamConfig(mode="producer")
        with pytest.raises(InvalidTCPOptionsError, match="TCP options cannot be an empty dictionary."):
            config.tcp_options = {}
