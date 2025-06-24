"""
Test suite for RABBITMQ_URL environment variable functionality in Warren class.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from bunnystream.warren import Warren


class TestWarrenEnvironmentVariable:
    """Test Warren class RABBITMQ_URL environment variable parsing."""

    def setup_method(self):
        """Clean up environment before each test."""
        if 'RABBITMQ_URL' in os.environ:
            del os.environ['RABBITMQ_URL']

    def teardown_method(self):
        """Clean up environment after each test.""" 
        if 'RABBITMQ_URL' in os.environ:
            del os.environ['RABBITMQ_URL']

    def test_no_environment_variable_uses_defaults(self):
        """Test that initialization works normally when no RABBITMQ_URL is set."""
        warren = Warren(rabbit_host="localhost")
        
        assert warren.rabbit_host == "localhost"
        assert warren.rabbit_port == 5672
        assert warren.rabbit_vhost == "/"
        assert warren.rabbit_user == "guest"
        assert warren.rabbit_pass == "guest"

    def test_full_rabbitmq_url_parsing(self):
        """Test parsing a complete RABBITMQ_URL."""
        os.environ['RABBITMQ_URL'] = 'amqp://testuser:testpass@example.com:5673/testvhost'
        
        warren = Warren()
        
        assert warren.rabbit_host == "example.com"
        assert warren.rabbit_port == 5673
        assert warren.rabbit_user == "testuser"
        assert warren.rabbit_pass == "testpass"
        assert warren.rabbit_vhost == "/testvhost"

    def test_amqps_scheme_parsing(self):
        """Test parsing RABBITMQ_URL with amqps scheme."""
        os.environ['RABBITMQ_URL'] = 'amqps://secureuser:securepass@secure.example.com:5671/securevhost'
        
        warren = Warren()
        
        assert warren.rabbit_host == "secure.example.com"
        assert warren.rabbit_port == 5671
        assert warren.rabbit_user == "secureuser"
        assert warren.rabbit_pass == "securepass"
        assert warren.rabbit_vhost == "/securevhost"

    def test_minimal_rabbitmq_url_parsing(self):
        """Test parsing minimal RABBITMQ_URL with only host."""
        os.environ['RABBITMQ_URL'] = 'amqp://localhost'
        
        warren = Warren()
        
        assert warren.rabbit_host == "localhost"
        assert warren.rabbit_port == 5672  # Should use default
        assert warren.rabbit_vhost == "/"   # Should use default
        assert warren.rabbit_user == "guest"   # Should use default
        assert warren.rabbit_pass == "guest"   # Should use default

    def test_url_with_default_vhost(self):
        """Test parsing URL with default vhost (just /)."""
        os.environ['RABBITMQ_URL'] = 'amqp://user:pass@host.com:5672/'
        
        warren = Warren()
        
        assert warren.rabbit_host == "host.com"
        assert warren.rabbit_port == 5672
        assert warren.rabbit_user == "user"
        assert warren.rabbit_pass == "pass"
        assert warren.rabbit_vhost == "/"

    def test_constructor_parameters_override_environment(self):
        """Test that constructor parameters take precedence over environment variables."""
        os.environ['RABBITMQ_URL'] = 'amqp://envuser:envpass@envhost.com:5673/envvhost'
        
        warren = Warren(
            rabbit_host="constructorhost.com",
            rabbit_port=1234,
            rabbit_vhost="/constructorvhost",
            rabbit_user="constructoruser",
            rabbit_pass="constructorpass"
        )
        
        # Constructor parameters should override environment
        assert warren.rabbit_host == "constructorhost.com"
        assert warren.rabbit_port == 1234
        assert warren.rabbit_user == "constructoruser"
        assert warren.rabbit_pass == "constructorpass"
        assert warren.rabbit_vhost == "/constructorvhost"

    def test_partial_constructor_override(self):
        """Test that only specified constructor parameters override environment."""
        os.environ['RABBITMQ_URL'] = 'amqp://envuser:envpass@envhost.com:5673/envvhost'
        
        # Only override host and port
        warren = Warren(rabbit_host="overridehost.com", rabbit_port=9999)
        
        assert warren.rabbit_host == "overridehost.com"  # Overridden
        assert warren.rabbit_port == 9999                # Overridden
        assert warren.rabbit_user == "envuser"           # From environment
        assert warren.rabbit_pass == "envpass"           # From environment
        assert warren.rabbit_vhost == "/envvhost"        # From environment

    def test_invalid_url_scheme_raises_error(self):
        """Test that invalid URL scheme raises ValueError."""
        os.environ['RABBITMQ_URL'] = 'http://user:pass@host.com:5672/'
        
        with pytest.raises(ValueError, match="Invalid URL scheme 'http'"):
            Warren()

    def test_malformed_url_raises_error(self):
        """Test that malformed URL raises ValueError."""
        os.environ['RABBITMQ_URL'] = 'not-a-valid-url'
        
        with pytest.raises(ValueError, match="Invalid RABBITMQ_URL format"):
            Warren()

    def test_url_without_credentials(self):
        """Test parsing URL without username/password."""
        os.environ['RABBITMQ_URL'] = 'amqp://example.com:5672/myvhost'
        
        warren = Warren()
        
        assert warren.rabbit_host == "example.com"
        assert warren.rabbit_port == 5672
        assert warren.rabbit_vhost == "/myvhost"
        assert warren.rabbit_user == "guest"  # Should use default
        assert warren.rabbit_pass == "guest"  # Should use default

    def test_url_with_only_username(self):
        """Test parsing URL with only username, no password."""
        os.environ['RABBITMQ_URL'] = 'amqp://onlyuser@example.com:5672/'
        
        warren = Warren()
        
        assert warren.rabbit_host == "example.com"
        assert warren.rabbit_port == 5672
        assert warren.rabbit_user == "onlyuser"
        assert warren.rabbit_pass == "guest"  # Should use default

    def test_url_without_port_uses_default(self):
        """Test parsing URL without port uses default."""
        os.environ['RABBITMQ_URL'] = 'amqp://user:pass@example.com/vhost'
        
        warren = Warren()
        
        assert warren.rabbit_host == "example.com"
        assert warren.rabbit_port == 5672  # Should use default
        assert warren.rabbit_user == "user"
        assert warren.rabbit_pass == "pass"
        assert warren.rabbit_vhost == "/vhost"

    def test_complex_vhost_path(self):
        """Test parsing complex vhost paths."""
        os.environ['RABBITMQ_URL'] = 'amqp://user:pass@host.com:5672/app/production'
        
        warren = Warren()
        
        assert warren.rabbit_vhost == "/app/production"

    def test_url_with_special_characters_in_credentials(self):
        """Test parsing URL with special characters in username/password."""
        # URL encode special characters
        os.environ['RABBITMQ_URL'] = 'amqp://user%40domain:p%40ssw0rd@host.com:5672/'
        
        warren = Warren()
        
        assert warren.rabbit_user == "user@domain"
        assert warren.rabbit_pass == "p@ssw0rd"

    @patch('bunnystream.warren.get_bunny_logger')
    def test_environment_parsing_logging(self, mock_get_logger):
        """Test that environment variable parsing is properly logged."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        os.environ['RABBITMQ_URL'] = 'amqp://user:pass@host.com:5672/vhost'
        
        Warren()
        
        # Check that appropriate debug messages were logged
        debug_calls = mock_logger.debug.call_args_list
        debug_messages = [str(call) for call in debug_calls]
        
        assert any("Found RABBITMQ_URL environment variable" in msg for msg in debug_messages)
        assert any("Parsed RABBITMQ_URL components" in msg for msg in debug_messages)

    @patch('bunnystream.warren.get_bunny_logger')
    def test_invalid_url_error_logging(self, mock_get_logger):
        """Test that invalid URL errors are properly logged."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        os.environ['RABBITMQ_URL'] = 'invalid-url'
        
        with pytest.raises(ValueError):
            Warren()
        
        # Check that error was logged
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args_list[0]
        assert "Failed to parse RABBITMQ_URL" in str(error_call)

    def test_url_parsing_preserves_original_behavior(self):
        """Test that URL parsing doesn't interfere with original Warren behavior."""
        os.environ['RABBITMQ_URL'] = 'amqp://envuser:envpass@envhost.com:5673/envvhost'
        
        warren = Warren(rabbit_host="localhost")
        
        # Test that Warren still works as expected
        assert warren.rabbit_host == "localhost"
        
        # Test URL generation
        url = warren.url
        assert "localhost" in url
        
        # Test property changes
        warren.rabbit_port = 9999
        new_url = warren.url
        assert new_url != url
        assert "9999" in new_url

    def test_empty_rabbitmq_url_environment_variable(self):
        """Test behavior when RABBITMQ_URL is set but empty."""
        os.environ['RABBITMQ_URL'] = ''
        
        # Empty string should be falsy, so environment parsing should be skipped
        warren = Warren(rabbit_host="localhost")
        
        assert warren.rabbit_host == "localhost"
        assert warren.rabbit_port == 5672
        assert warren.rabbit_vhost == "/"


class TestWarrenUrlParsingMethod:
    """Test the _parse_rabbitmq_url method directly.
    
    Note: We're testing the protected method directly to ensure proper URL parsing
    functionality. This is acceptable in unit tests for thorough coverage.
    """

    def test_parse_complete_url(self):
        """Test parsing a complete URL."""
        warren = Warren(rabbit_host="localhost")
        
        result = warren._parse_rabbitmq_url('amqp://user:pass@host.com:5672/vhost')  # pylint: disable=protected-access
        
        expected = {
            'host': 'host.com',
            'port': 5672,
            'user': 'user',
            'pass': 'pass',
            'vhost': '/vhost'
        }
        assert result == expected

    def test_parse_minimal_url(self):
        """Test parsing minimal URL."""
        warren = Warren(rabbit_host="localhost")
        
        result = warren._parse_rabbitmq_url('amqp://host.com')  # pylint: disable=protected-access
        
        expected = {'host': 'host.com'}
        assert result == expected

    def test_parse_url_with_default_vhost(self):
        """Test parsing URL with default vhost."""
        warren = Warren(rabbit_host="localhost")
        
        result = warren._parse_rabbitmq_url('amqp://user:pass@host.com:5672/')  # pylint: disable=protected-access
        
        expected = {
            'host': 'host.com',
            'port': 5672,
            'user': 'user',
            'pass': 'pass'
        }
        assert result == expected

    def test_parse_invalid_scheme(self):
        """Test parsing URL with invalid scheme."""
        warren = Warren(rabbit_host="localhost")
        
        with pytest.raises(ValueError, match="Invalid URL scheme 'https'"):
            warren._parse_rabbitmq_url('https://host.com')  # pylint: disable=protected-access

    def test_parse_malformed_url(self):
        """Test parsing malformed URL."""
        warren = Warren(rabbit_host="localhost")
        
        with pytest.raises(ValueError, match="Invalid RABBITMQ_URL format"):
            warren._parse_rabbitmq_url('not-a-url')  # pylint: disable=protected-access
