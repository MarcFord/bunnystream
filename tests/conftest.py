"""
Pytest configuration for bunnystream tests.
"""

import logging

import pytest


@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests."""
    # Disable logging during tests to reduce noise
    logging.disable(logging.CRITICAL)
    yield
    # Re-enable logging after tests
    logging.disable(logging.NOTSET)


@pytest.fixture
def warren_with_host():
    """Fixture for Warren instance with host configured."""
    from bunnystream.warren import Warren

    return Warren(rabbit_host="localhost")


@pytest.fixture
def warren_full_config():
    """Fixture for Warren instance with full configuration."""
    from bunnystream.warren import Warren

    return Warren(
        rabbit_host="localhost",
        rabbit_port=5672,
        rabbit_vhost="/test",
        rabbit_user="testuser",
        rabbit_pass="testpass",
    )
