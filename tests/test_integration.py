"""
Integration tests for the bunnystream package.
"""
import pytest
import logging

import bunnystream
from bunnystream import Warren, bunny_logger, get_bunny_logger, configure_bunny_logger
from bunnystream.exceptions import RabbitPortError, RabbitHostError, RabbitVHostError, RabbitCredentialsError


class TestPackageIntegration:
    """Test package-level integration."""

    def test_package_imports(self):
        """Test that all main components can be imported."""
        # Test direct imports
        assert hasattr(bunnystream, 'Warren')
        assert hasattr(bunnystream, 'bunny_logger')
        assert hasattr(bunnystream, 'get_bunny_logger')
        assert hasattr(bunnystream, 'configure_bunny_logger')
        assert hasattr(bunnystream, '__version__')

    def test_package_version(self):
        """Test that package version is accessible."""
        version = bunnystream.__version__
        assert isinstance(version, str)
        assert len(version) > 0

    def test_warren_creation_and_usage(self):
        """Test creating and using Warren instance."""
        warren = Warren(
            rabbit_host="localhost",
            rabbit_port=5672,
            rabbit_vhost="/test",
            rabbit_user="testuser",
            rabbit_pass="testpass"
        )
        
        # Test that all properties work
        assert warren.rabbit_host == "localhost"
        assert warren.rabbit_port == 5672
        assert warren.rabbit_vhost == "/test"
        assert warren.rabbit_user == "testuser"
        assert warren.rabbit_pass == "testpass"
        
        # Test URL generation
        url = warren.url
        assert url.startswith("amqp://")
        assert "testuser:testpass" in url
        assert "localhost:5672" in url
        assert "/test" in url

    def test_logger_integration(self):
        """Test logger integration works across components."""
        # Configure logger
        configure_bunny_logger(level=logging.DEBUG)
        
        # Create Warren instance
        warren = Warren(rabbit_host="example.com")
        
        # Test that logger is properly configured
        assert warren.logger.name == "bunnystream.warren"
        assert warren.logger.level <= logging.DEBUG
        
        # Test creating specific loggers
        consumer_logger = get_bunny_logger("consumer")
        producer_logger = get_bunny_logger("producer")
        
        assert consumer_logger.name == "bunnystream.consumer"
        assert producer_logger.name == "bunnystream.producer"

    def test_error_handling_integration(self):
        """Test that errors are properly handled across the package."""
        warren = Warren()
        
        # Test various error conditions
        with pytest.raises(RabbitPortError):
            warren.rabbit_port = -1
            
        with pytest.raises(RabbitHostError):
            warren.rabbit_host = ""
            
        with pytest.raises(RabbitVHostError):
            warren.rabbit_vhost = ""
            
        with pytest.raises(RabbitCredentialsError):
            warren.rabbit_user = ""

    def test_configuration_persistence(self):
        """Test that configuration changes persist correctly."""
        warren = Warren()
        
        # Configure Warren
        warren.rabbit_host = "production.rabbitmq.com"
        warren.rabbit_port = 5671
        warren.rabbit_vhost = "/production"
        warren.rabbit_user = "prod_user"
        warren.rabbit_pass = "secure_password"
        
        # Generate URL to cache it
        initial_url = warren.url
        
        # Verify configuration persists
        assert warren.rabbit_host == "production.rabbitmq.com"
        assert warren.rabbit_port == 5671
        assert warren.rabbit_vhost == "/production"
        assert warren.rabbit_user == "prod_user"
        assert warren.rabbit_pass == "secure_password"
        
        # Verify URL is correct
        assert "prod_user:secure_password" in initial_url
        assert "production.rabbitmq.com:5671" in initial_url
        assert "/production" in initial_url
        
        # Change configuration and verify URL updates
        warren.rabbit_port = 5672
        new_url = warren.url
        assert new_url != initial_url
        assert "5672" in new_url

    def test_default_behavior(self):
        """Test default behavior when minimal configuration is provided."""
        warren = Warren(rabbit_host="localhost")
        
        # Test defaults
        assert warren.rabbit_port == 5672
        assert warren.rabbit_vhost == "/"
        assert warren.rabbit_user == "guest"  # Should default to guest
        assert warren.rabbit_pass == "guest"  # Should default to guest
        
        # Test URL generation with defaults
        url = warren.url
        expected = "amqp://guest:guest@localhost:5672//"
        assert url == expected

    def test_logging_output_format(self):
        """Test that logging output is properly formatted."""
        # This test verifies the logger can be used without errors
        warren = Warren(rabbit_host="test.example.com")
        
        # These should not raise any exceptions
        warren.logger.info("Test info message")
        warren.logger.debug("Test debug message")
        warren.logger.warning("Test warning message")
        
        # Test that bunny_logger works
        bunny_logger.info("Direct bunny_logger message")
        
        # Test that component-specific loggers work
        test_logger = get_bunny_logger("integration_test")
        test_logger.info("Component-specific logger message")

    def test_comprehensive_workflow(self):
        """Test a comprehensive workflow using the package."""
        # Step 1: Configure logging
        configure_bunny_logger(level=logging.INFO)
        
        # Step 2: Create Warren instance
        warren = Warren()
        
        # Step 3: Configure connection parameters
        warren.rabbit_host = "messaging.company.com"
        warren.rabbit_port = 5672
        warren.rabbit_vhost = "/app"
        warren.rabbit_user = "app_user"
        warren.rabbit_pass = "app_password"
        
        # Step 4: Generate connection URL
        connection_url = warren.url
        
        # Step 5: Verify the complete configuration
        assert warren.rabbit_host == "messaging.company.com"
        assert warren.rabbit_port == 5672
        assert warren.rabbit_vhost == "/app"
        assert warren.rabbit_user == "app_user"
        assert warren.rabbit_pass == "app_password"
        assert connection_url == "amqp://app_user:app_password@messaging.company.com:5672//app"
        
        # Step 6: Test that configuration changes work
        warren.rabbit_port = 5671
        new_url = warren.url
        assert new_url != connection_url
        assert "5671" in new_url
        
        # Step 7: Test error recovery
        try:
            warren.rabbit_port = -1
        except RabbitPortError:
            # Recover from error
            warren.rabbit_port = 5672
        
        # Verify recovery worked
        assert warren.rabbit_port == 5672
        recovery_url = warren.url
        assert "5672" in recovery_url
