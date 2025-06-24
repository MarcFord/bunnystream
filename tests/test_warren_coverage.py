import pytest

from bunnystream.warren import Warren
from bunnystream.exceptions import RabbitPortError, RabbitVHostError, RabbitCredentialsError


class TestWarrenPropertyEdgeCases:
    """Test edge cases and error conditions that need coverage."""

    def test_port_getter_non_integer_type_error(self):
        """Test port getter when _rabbit_port is set to invalid type."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to bypass type checking and set invalid type
        setattr(warren, '_rabbit_port', 12.5)  # float instead of int
        
        with pytest.raises(RabbitPortError, match="Rabbit port must be an integer"):
            _ = warren.rabbit_port

    def test_port_getter_zero_value_error(self):
        """Test port getter when _rabbit_port is exactly 0."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to bypass type checking and set to 0
        setattr(warren, '_rabbit_port', 0)
        
        with pytest.raises(RabbitPortError, match="Rabbit port must be a positive integer"):
            _ = warren.rabbit_port

    def test_port_getter_invalid_string_conversion(self):
        """Test port getter when _rabbit_port is set to unconvertible string."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to set an invalid string that can't be converted to int
        setattr(warren, '_rabbit_port', "invalid_port")
        
        with pytest.raises(RabbitPortError, match="Rabbit port must be a string that can be converted to an integer"):
            _ = warren.rabbit_port
    
    def test_port_getter_valid_string_conversion(self):
        """Test port getter when _rabbit_port is set to valid string that can be converted."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to set a valid string that can be converted to int
        setattr(warren, '_rabbit_port', "8080")
        
        # This should successfully convert the string to int and return it
        assert warren.rabbit_port == 8080
        # After conversion, _rabbit_port should now be an int
        assert isinstance(getattr(warren, '_rabbit_port'), int)  # pylint: disable=protected-access

    def test_port_getter_when_none_returns_default(self):
        """Test port getter when _rabbit_port is None returns default 5672."""
        warren = Warren(rabbit_host="localhost")
        # Ensure _rabbit_port is None by setting it explicitly
        setattr(warren, '_rabbit_port', None)
        
        # Should return default port 5672 and log info message
        assert warren.rabbit_port == 5672

    def test_vhost_getter_invalid_type_error(self):
        """Test vhost getter when _rabbit_vhost is set to invalid type."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to bypass type checking and set invalid type
        setattr(warren, '_rabbit_vhost', 123)  # int instead of str
        
        with pytest.raises(RabbitVHostError, match="Rabbit vhost must be a string"):
            _ = warren.rabbit_vhost

    def test_vhost_getter_empty_string_error(self):
        """Test vhost getter when _rabbit_vhost is empty string."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to set whitespace-only string
        setattr(warren, '_rabbit_vhost', "   ")  # whitespace only
        
        with pytest.raises(RabbitVHostError, match="Rabbit vhost cannot be empty"):
            _ = warren.rabbit_vhost

    def test_user_getter_invalid_type_error(self):
        """Test user getter when _rabbit_user is set to invalid type."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to bypass type checking and set invalid type
        setattr(warren, '_rabbit_user', 123)  # int instead of str
        
        with pytest.raises(RabbitCredentialsError, match="Rabbit user must be a string"):
            _ = warren.rabbit_user

    def test_user_getter_empty_string_error(self):
        """Test user getter when _rabbit_user is empty string."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to set whitespace-only string
        setattr(warren, '_rabbit_user', "   ")  # whitespace only
        
        with pytest.raises(RabbitCredentialsError, match="Rabbit user cannot be empty"):
            _ = warren.rabbit_user

    def test_pass_getter_invalid_type_error(self):
        """Test pass getter when _rabbit_pass is set to invalid type."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to bypass type checking and set invalid type
        setattr(warren, '_rabbit_pass', 123)  # int instead of str
        
        with pytest.raises(RabbitCredentialsError, match="Rabbit password must be a string"):
            _ = warren.rabbit_pass

    def test_pass_getter_empty_string_error(self):
        """Test pass getter when _rabbit_pass is empty string."""
        warren = Warren(rabbit_host="localhost")
        # Use setattr to set whitespace-only string
        setattr(warren, '_rabbit_pass', "   ")  # whitespace only
        
        with pytest.raises(RabbitCredentialsError, match="Rabbit password cannot be empty"):
            _ = warren.rabbit_pass