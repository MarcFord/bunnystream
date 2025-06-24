"""
Test suite for the Warren class.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock

from bunnystream.warren import Warren
from bunnystream.exceptions import (
    RabbitPortError,
    RabbitHostError,
    RabbitVHostError,
    RabbitCredentialsError
)


class TestWarrenInitialization:
    """Test Warren class initialization."""

    def test_default_initialization(self):
        """Test Warren initialization with default values."""
        warren = Warren()
        
        assert warren.rabbit_port == 5672
        assert warren.rabbit_vhost == "/"
        assert warren.rabbit_host == ""
        assert warren.rabbit_user == "guest"
        assert warren.rabbit_pass == "guest"
        assert warren.logger.name == "bunnystream.warren"

    def test_initialization_with_all_parameters(self):
        """Test Warren initialization with all parameters provided."""
        warren = Warren(
            rabbit_port=5673,
            rabbit_vhost="/test",
            rabbit_host="localhost",
            rabbit_user="testuser",
            rabbit_pass="testpass"
        )
        
        assert warren.rabbit_port == 5673
        assert warren.rabbit_vhost == "/test"
        assert warren.rabbit_host == "localhost"
        assert warren.rabbit_user == "testuser"
        assert warren.rabbit_pass == "testpass"

    def test_initialization_with_partial_parameters(self):
        """Test Warren initialization with partial parameters."""
        warren = Warren(rabbit_host="example.com", rabbit_port=1234)
        
        assert warren.rabbit_port == 1234
        assert warren.rabbit_host == "example.com"
        assert warren.rabbit_vhost == "/"
        assert warren.rabbit_user == "guest"
        assert warren.rabbit_pass == "guest"

    @patch('bunnystream.warren.get_bunny_logger')
    def test_logger_initialization(self, mock_get_logger):
        """Test that logger is properly initialized."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        warren = Warren(rabbit_host="test.com")
        
        mock_get_logger.assert_called_once_with("warren")
        assert warren.logger == mock_logger
        # Debug is called multiple times during initialization (for each property set)
        assert mock_logger.debug.call_count >= 1


class TestWarrenPortProperty:
    """Test rabbit_port property getter and setter."""

    def test_port_getter_with_valid_port(self):
        """Test getting a valid port."""
        warren = Warren(rabbit_port=5672)
        assert warren.rabbit_port == 5672

    def test_port_getter_with_string_port(self):
        """Test getting port when set as string."""
        warren = Warren()
        # Use setattr to bypass type checking for testing edge cases
        setattr(warren, '_rabbit_port', "5673")
        assert warren.rabbit_port == 5673
        assert isinstance(warren.rabbit_port, int)

    def test_port_getter_with_invalid_string(self):
        """Test getting port with invalid string raises error."""
        warren = Warren()
        # Use setattr to bypass type checking for testing edge cases
        setattr(warren, '_rabbit_port', "invalid")
        
        with pytest.raises(RabbitPortError, match="must be a string that can be converted to an integer"):
            _ = warren.rabbit_port

    def test_port_setter_with_valid_int(self):
        """Test setting port with valid integer."""
        warren = Warren()
        warren.rabbit_port = 1234
        assert warren.rabbit_port == 1234

    def test_port_setter_with_valid_string(self):
        """Test setting port with valid string."""
        warren = Warren()
        warren.rabbit_port = "5673"
        assert warren.rabbit_port == 5673

    def test_port_setter_with_zero(self):
        """Test setting port to zero raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitPortError, match="must be a positive integer"):
            warren.rabbit_port = 0

    def test_port_setter_with_negative(self):
        """Test setting negative port raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitPortError, match="must be a positive integer"):
            warren.rabbit_port = -1

    def test_port_setter_with_invalid_type(self):
        """Test setting port with invalid type raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitPortError, match="must be an integer or a string"):
            setattr(warren, 'rabbit_port', 12.34)  # type: ignore

    def test_port_setter_resets_url(self):
        """Test that setting port resets the cached URL."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        _ = warren.url  # Generate URL
        assert getattr(warren, '_url') is not None
        
        warren.rabbit_port = 5673
        assert getattr(warren, '_url') is None


class TestWarrenHostProperty:
    """Test rabbit_host property getter and setter."""

    def test_host_getter_with_set_host(self):
        """Test getting host when it's set."""
        warren = Warren(rabbit_host="localhost")
        assert warren.rabbit_host == "localhost"

    def test_host_getter_with_none_host(self):
        """Test getting host when it's None returns empty string."""
        warren = Warren()
        assert warren.rabbit_host == ""

    def test_host_setter_with_valid_host(self):
        """Test setting valid host."""
        warren = Warren()
        warren.rabbit_host = "example.com"
        assert warren.rabbit_host == "example.com"

    def test_host_setter_with_empty_string(self):
        """Test setting empty host raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitHostError):
            warren.rabbit_host = ""

    def test_host_setter_with_whitespace_only(self):
        """Test setting whitespace-only host raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitHostError, match="cannot be empty"):
            warren.rabbit_host = "   "

    def test_host_setter_with_amqp_prefix(self):
        """Test setting host with amqp:// prefix raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitHostError, match="should not start with 'amqp://'"):
            warren.rabbit_host = "amqp://localhost"

    def test_host_setter_with_invalid_type(self):
        """Test setting host with invalid type raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitHostError, match="must be a string"):
            setattr(warren, 'rabbit_host', 12345)  # type: ignore

    def test_host_setter_resets_url(self):
        """Test that setting host resets the cached URL."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        _ = warren.url  # Generate URL
        assert getattr(warren, '_url') is not None
        
        warren.rabbit_host = "newhost.com"
        assert getattr(warren, '_url') is None


class TestWarrenVHostProperty:
    """Test rabbit_vhost property getter and setter."""

    def test_vhost_getter_with_set_vhost(self):
        """Test getting vhost when it's set."""
        warren = Warren(rabbit_vhost="/myvhost")
        assert warren.rabbit_vhost == "/myvhost"

    def test_vhost_getter_with_none_defaults_to_slash(self):
        """Test getting vhost when None defaults to '/'."""
        warren = Warren()
        setattr(warren, '_rabbit_vhost', None)
        assert warren.rabbit_vhost == "/"

    def test_vhost_setter_with_valid_vhost(self):
        """Test setting valid vhost."""
        warren = Warren()
        warren.rabbit_vhost = "/testvhost"
        assert warren.rabbit_vhost == "/testvhost"

    def test_vhost_setter_with_empty_string(self):
        """Test setting empty vhost raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitVHostError, match="cannot be empty"):
            warren.rabbit_vhost = ""

    def test_vhost_setter_with_whitespace_only(self):
        """Test setting whitespace-only vhost raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitVHostError, match="cannot be empty"):
            warren.rabbit_vhost = "   "

    def test_vhost_setter_with_invalid_type(self):
        """Test setting vhost with invalid type raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitVHostError, match="must be a string"):
            setattr(warren, 'rabbit_vhost', 123)  # type: ignore

    def test_vhost_setter_resets_url(self):
        """Test that setting vhost resets the cached URL."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        _ = warren.url  # Generate URL
        assert getattr(warren, '_url') is not None
        
        warren.rabbit_vhost = "/newvhost"
        assert getattr(warren, '_url') is None


class TestWarrenUserProperty:
    """Test rabbit_user property getter and setter."""

    def test_user_getter_with_set_user(self):
        """Test getting user when it's set."""
        warren = Warren(rabbit_user="testuser")
        assert warren.rabbit_user == "testuser"

    def test_user_getter_with_none_defaults_to_guest(self):
        """Test getting user when None defaults to 'guest'."""
        warren = Warren()
        setattr(warren, '_rabbit_user', None)
        assert warren.rabbit_user == "guest"

    def test_user_setter_with_valid_user(self):
        """Test setting valid user."""
        warren = Warren()
        warren.rabbit_user = "myuser"
        assert warren.rabbit_user == "myuser"

    def test_user_setter_with_empty_string(self):
        """Test setting empty user raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitCredentialsError, match="cannot be empty"):
            warren.rabbit_user = ""

    def test_user_setter_with_whitespace_only(self):
        """Test setting whitespace-only user raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitCredentialsError, match="cannot be empty"):
            warren.rabbit_user = "   "

    def test_user_setter_with_invalid_type(self):
        """Test setting user with invalid type raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitCredentialsError, match="must be a string"):
            setattr(warren, 'rabbit_user', 12345)  # type: ignore

    def test_user_setter_resets_url(self):
        """Test that setting user resets the cached URL."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        _ = warren.url  # Generate URL
        assert getattr(warren, '_url') is not None
        
        warren.rabbit_user = "newuser"
        assert getattr(warren, '_url') is None


class TestWarrenPassProperty:
    """Test rabbit_pass property getter and setter."""

    def test_pass_getter_with_set_pass(self):
        """Test getting password when it's set."""
        warren = Warren(rabbit_pass="testpass")
        assert warren.rabbit_pass == "testpass"

    def test_pass_getter_with_none_defaults_to_guest(self):
        """Test getting password when None defaults to 'guest'."""
        warren = Warren()
        setattr(warren, '_rabbit_pass', None)
        assert warren.rabbit_pass == "guest"

    def test_pass_setter_with_valid_pass(self):
        """Test setting valid password."""
        warren = Warren()
        warren.rabbit_pass = "mypass"
        assert warren.rabbit_pass == "mypass"

    def test_pass_setter_with_empty_string(self):
        """Test setting empty password raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitCredentialsError, match="cannot be empty"):
            warren.rabbit_pass = ""

    def test_pass_setter_with_whitespace_only(self):
        """Test setting whitespace-only password raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitCredentialsError, match="cannot be empty"):
            warren.rabbit_pass = "   "

    def test_pass_setter_with_invalid_type(self):
        """Test setting password with invalid type raises error."""
        warren = Warren()
        
        with pytest.raises(RabbitCredentialsError, match="must be a string"):
            setattr(warren, 'rabbit_pass', 12345)  # type: ignore

    def test_pass_setter_resets_url(self):
        """Test that setting password resets the cached URL."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        _ = warren.url  # Generate URL
        assert getattr(warren, '_url') is not None
        
        warren.rabbit_pass = "newpass"
        assert getattr(warren, '_url') is None


class TestWarrenUrlProperty:
    """Test URL generation."""

    def test_url_generation_with_all_params(self):
        """Test URL generation with all parameters."""
        warren = Warren(
            rabbit_host="localhost",
            rabbit_port=5672,
            rabbit_vhost="/test",
            rabbit_user="myuser",
            rabbit_pass="mypass"
        )
        
        expected_url = "amqp://myuser:mypass@localhost:5672//test"
        assert warren.url == expected_url

    def test_url_generation_with_defaults(self):
        """Test URL generation with default values."""
        warren = Warren(rabbit_host="localhost")
        
        # Access properties to trigger defaults
        _ = warren.rabbit_user  # This will set default 'guest'
        _ = warren.rabbit_pass  # This will set default 'guest'
        
        expected_url = "amqp://guest:guest@localhost:5672//"
        assert warren.url == expected_url

    def test_url_caching(self):
        """Test that URL is cached after first generation."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        
        # First call should generate URL
        url1 = warren.url
        assert getattr(warren, '_url') is not None
        
        # Second call should return cached URL
        url2 = warren.url
        assert url1 == url2

    def test_url_reset_on_property_change(self):
        """Test that URL cache is reset when properties change."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        
        # Generate initial URL
        initial_url = warren.url
        assert getattr(warren, '_url') is not None
        
        # Change a property - URL should be reset and regenerated
        warren.rabbit_port = 5673
        new_url = warren.url
        
        assert initial_url != new_url
        assert "5673" in new_url

    def test_url_with_special_characters_in_vhost(self):
        """Test URL generation with special characters in vhost."""
        warren = Warren(
            rabbit_host="localhost",
            rabbit_vhost="/my-vhost",
            rabbit_user="user",
            rabbit_pass="pass"
        )
        
        expected_url = "amqp://user:pass@localhost:5672//my-vhost"
        assert warren.url == expected_url


class TestWarrenLogging:
    """Test logging functionality."""

    @patch('bunnystream.warren.get_bunny_logger')
    def test_debug_logging_on_initialization(self, mock_get_logger):
        """Test that debug logging occurs during initialization."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        Warren(rabbit_host="localhost", rabbit_port=5673, rabbit_vhost="/test")
        
        # Check that debug was called with initialization message
        mock_logger.debug.assert_called_with(
            "Warren initialized with port=%s, vhost=%s, host=%s",
            5673, "/test", "localhost"
        )

    @patch('bunnystream.warren.get_bunny_logger')
    def test_debug_logging_on_property_changes(self, mock_get_logger):
        """Test that debug logging occurs when properties change."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        warren = Warren()
        warren.logger = mock_logger  # Replace with mock
        
        # Reset mock to clear initialization calls
        mock_logger.reset_mock()
        
        # Test property changes
        warren.rabbit_port = 5674
        warren.rabbit_host = "newhost.com"
        warren.rabbit_vhost = "/newvhost"
        warren.rabbit_user = "newuser"
        warren.rabbit_pass = "newpass"
        
        # Verify debug calls
        debug_calls = mock_logger.debug.call_args_list
        assert len(debug_calls) >= 5  # At least one for each property change
        
        # Check some specific calls
        assert any("Setting rabbit port to:" in str(call) for call in debug_calls)
        assert any("Setting rabbit host to:" in str(call) for call in debug_calls)

    def test_logging_integration_with_real_logger(self):
        """Test actual logging integration (not mocked)."""
        with patch('bunnystream.logger.logging.StreamHandler'):
            warren = Warren(rabbit_host="localhost")
            
            # Verify logger is properly set up
            assert warren.logger.name == "bunnystream.warren"
            assert hasattr(warren.logger, 'debug')
            assert hasattr(warren.logger, 'info')


class TestWarrenEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_port_type_in_getter(self):
        """Test invalid port type in internal state."""
        warren = Warren()
        setattr(warren, '_rabbit_port', [])  # Invalid type
        
        with pytest.raises(RabbitPortError, match="must be an integer"):
            _ = warren.rabbit_port

    def test_multiple_url_resets(self):
        """Test multiple URL resets work correctly."""
        warren = Warren(rabbit_host="localhost", rabbit_user="test", rabbit_pass="test")
        
        # Generate URL multiple times with changes
        url1 = warren.url
        warren.rabbit_port = 5673
        url2 = warren.url
        warren.rabbit_host = "newhost"
        url3 = warren.url
        
        # All should be different
        assert len({url1, url2, url3}) == 3

    def test_property_validation_order(self):
        """Test that property validation works regardless of order."""
        warren = Warren()
        
        # Set properties in different order
        warren.rabbit_user = "testuser"
        warren.rabbit_pass = "testpass"
        warren.rabbit_host = "localhost"
        warren.rabbit_vhost = "/test"
        warren.rabbit_port = 5673
        
        # All should be set correctly
        assert warren.rabbit_user == "testuser"
        assert warren.rabbit_pass == "testpass"
        assert warren.rabbit_host == "localhost"
        assert warren.rabbit_vhost == "/test"
        assert warren.rabbit_port == 5673

    def test_string_port_conversion_edge_cases(self):
        """Test edge cases in string to port conversion."""
        warren = Warren()
        
        # Valid string numbers
        warren.rabbit_port = "8080"
        assert warren.rabbit_port == 8080
        
        # Valid string with leading/trailing spaces handled by int()
        warren.rabbit_port = "9090"
        assert warren.rabbit_port == 9090


class TestWarrenIntegration:
    """Integration tests for Warren class."""

    def test_complete_configuration_flow(self):
        """Test complete configuration from initialization to URL generation."""
        # Start with minimal config
        warren = Warren()
        
        # Configure step by step
        warren.rabbit_host = "prod.rabbitmq.com"
        warren.rabbit_port = 5671
        warren.rabbit_vhost = "/production"
        warren.rabbit_user = "prod_user"
        warren.rabbit_pass = "secure_password"
        
        # Generate final URL
        url = warren.url
        expected = "amqp://prod_user:secure_password@prod.rabbitmq.com:5671//production"
        assert url == expected

    def test_configuration_with_partial_updates(self):
        """Test configuration with partial updates."""
        warren = Warren(
            rabbit_host="localhost",
            rabbit_user="initial_user",
            rabbit_pass="initial_pass"
        )
        
        # Get initial URL
        initial_url = warren.url
        
        # Update only user
        warren.rabbit_user = "updated_user"
        updated_url = warren.url
        
        # URLs should be different
        assert initial_url != updated_url
        assert "updated_user" in updated_url
        assert "initial_user" not in updated_url

    def test_error_recovery(self):
        """Test that Warren can recover from errors."""
        warren = Warren(rabbit_host="localhost")
        
        # Cause an error
        with pytest.raises(RabbitPortError):
            warren.rabbit_port = -1
        
        # Verify Warren is still functional
        warren.rabbit_port = 5672
        assert warren.rabbit_port == 5672
        
        # URL generation should still work
        url = warren.url
        assert "5672" in url
