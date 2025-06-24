# BunnyStream

A robust Python library for emitting/consuming events using RabbitMQ as a message broker, compatible with Python 3.9+.

## Features

- **Simple API**: Easy-to-use interface for RabbitMQ connection management
- **Environment Variable Support**: Automatic parsing of `RABBITMQ_URL` environment variable
- **Robust Error Handling**: Comprehensive validation and custom exceptions
- **Logging Integration**: Built-in logging for debugging and monitoring
- **Type Safety**: Full type hints for better development experience
- **High Test Coverage**: >90% test coverage with comprehensive test suite

## Installation

```bash
pip install bunnystream
```

Or with uv:

```bash
uv add bunnystream
```

## Quick Start

### Basic Usage

```python
from bunnystream import Warren

# Create a Warren instance with explicit parameters
warren = Warren(
    rabbit_host="localhost",
    rabbit_port=5672,
    rabbit_vhost="/",
    rabbit_user="guest",
    rabbit_pass="guest"
)

# Get the AMQP connection URL
print(warren.url)  # amqp://guest:guest@localhost:5672//
```

### Environment Variable Configuration

BunnyStream supports automatic configuration via the `RABBITMQ_URL` environment variable:

```bash
export RABBITMQ_URL="amqp://myuser:mypass@rabbit.example.com:5673/myvhost"
```

```python
from bunnystream import Warren

# Warren will automatically parse RABBITMQ_URL
warren = Warren()

print(warren.rabbit_host)  # rabbit.example.com
print(warren.rabbit_port)  # 5673
print(warren.rabbit_user)  # myuser
print(warren.rabbit_pass)  # mypass
print(warren.rabbit_vhost) # /myvhost
```

### Constructor Parameters Override Environment

You can override specific parameters while using others from the environment:

```python
import os

os.environ['RABBITMQ_URL'] = "amqp://envuser:envpass@env.example.com:5672/envvhost"

# Override only the host, keep other values from environment
warren = Warren(rabbit_host="override.example.com")

print(warren.rabbit_host)  # override.example.com (overridden)
print(warren.rabbit_user)  # envuser (from environment)
print(warren.rabbit_pass)  # envpass (from environment)
print(warren.rabbit_vhost) # /envvhost (from environment)
```

### URL-Encoded Special Characters

BunnyStream automatically handles URL-encoded special characters in credentials:

```bash
export RABBITMQ_URL="amqp://user%40domain:p%40ssw0rd@host.com:5672/"
```

```python
warren = Warren()
print(warren.rabbit_user)  # user@domain (automatically decoded)
print(warren.rabbit_pass)  # p@ssw0rd (automatically decoded)
```

## RABBITMQ_URL Format

The `RABBITMQ_URL` environment variable should follow this format:

```
amqp[s]://[username[:password]]@host[:port][/vhost]
```

Examples:
- `amqp://guest:guest@localhost:5672/`
- `amqps://user:pass@secure.example.com:5671/production`
- `amqp://myuser@rabbit.local:5672/app`

Supported schemes:
- `amqp` - Standard AMQP connection
- `amqps` - Secure AMQP connection over TLS

## API Reference

### Warren Class

The main class for managing RabbitMQ connection parameters.

#### Constructor

```python
Warren(
    rabbit_port: int = 5672,
    rabbit_vhost: str = "/",
    rabbit_host: Optional[str] = None,
    rabbit_user: Optional[str] = None,
    rabbit_pass: Optional[str] = None
)
```

**Parameters:**
- `rabbit_port`: RabbitMQ server port (default: 5672)
- `rabbit_vhost`: Virtual host (default: "/")
- `rabbit_host`: RabbitMQ server hostname
- `rabbit_user`: Username for authentication
- `rabbit_pass`: Password for authentication

#### Properties

- `rabbit_host`: Get/set the RabbitMQ hostname
- `rabbit_port`: Get/set the RabbitMQ port
- `rabbit_vhost`: Get/set the virtual host
- `rabbit_user`: Get/set the username
- `rabbit_pass`: Get/set the password
- `url`: Get the complete AMQP connection URL (read-only)

#### Example

```python
warren = Warren()
warren.rabbit_host = "localhost"
warren.rabbit_port = 5672
warren.rabbit_user = "admin"
warren.rabbit_pass = "secret"

print(warren.url)  # amqp://admin:secret@localhost:5672//
```

## Error Handling

BunnyStream provides custom exceptions for different error scenarios:

```python
from bunnystream import Warren
from bunnystream.exceptions import (
    RabbitPortError,
    RabbitHostError,
    RabbitVHostError,
    RabbitCredentialsError
)

try:
    warren = Warren(rabbit_port=-1)  # Invalid port
except RabbitPortError as e:
    print(f"Port error: {e}")

try:
    warren = Warren()
    warren.rabbit_host = ""  # Empty host
except RabbitHostError as e:
    print(f"Host error: {e}")
```

## Logging

BunnyStream includes built-in logging for debugging and monitoring:

```python
import logging
from bunnystream import Warren

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

warren = Warren(rabbit_host="localhost")
# [2024-01-01 12:00:00,000] bunnystream.warren - DEBUG - Warren initialized with port=5672, vhost=/, host=localhost
```

## Development

### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=bunnystream --cov-report=term-missing
```

### Releasing

BunnyStream uses automated version management and releases. To create a new release:

```bash
# Interactive release (recommended)
./release.sh

# Or use Makefile commands
make release-patch   # For bug fixes (x.y.Z)
make release-minor   # For new features (x.Y.0)
make release-major   # For breaking changes (X.0.0)

# Or use the Python script directly
python scripts/bump_version.py patch --dry-run  # Preview changes
python scripts/bump_version.py minor            # Create minor release
```

The release process automatically:
- Runs all tests and quality checks
- Calculates the new version number
- Creates and pushes a git tag
- Triggers GitHub Actions to build and publish to PyPI
- Creates a GitHub release

For detailed release documentation, see [RELEASE.md](RELEASE.md).

### Development Commands

```bash
make help           # Show all available commands
make test           # Run tests with coverage
make lint           # Run code quality checks
make build          # Build the package
make clean          # Clean build artifacts
make pre-release    # Run all checks before release
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.