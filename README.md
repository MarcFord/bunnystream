# BunnyStream

[![Tests](https://github.com/MarcFord/bunnystream/actions/workflows/test.yml/badge.svg)](https://github.com/MarcFord/bunnystream/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/MarcFord/bunnystream)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/bunnystream.svg)](https://badge.fury.io/py/bunnystream)

A robust Python library for event-driven messaging using RabbitMQ as a message broker. BunnyStream provides a simple yet powerful interface for building scalable, event-driven applications with comprehensive support for publishing and consuming messages across multiple topics.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
  - [Basic Producer and Consumer](#basic-producer-and-consumer)
  - [Multi-Topic Event System](#multi-topic-event-system)
  - [Environment Configuration](#environment-configuration)
- [API Reference](#api-reference)
  - [Warren Class](#warren-class)
  - [BunnyStreamConfig Class](#bunnystreamconfig-class)
  - [BaseEvent Class](#baseevent-class)
  - [Subscription Class](#subscription-class)
- [Configuration](#configuration)
- [Event System](#event-system)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Development](#development)
  - [Setting up Development Environment](#setting-up-development-environment)
  - [Running Tests](#running-tests)
  - [Code Quality](#code-quality)
- [Contributing](#contributing)
- [License](#license)
- [Changelog](#changelog)

## Features

- **🚀 Simple API**: Easy-to-use interface for RabbitMQ connection and message management
- **🎯 Event-Driven Architecture**: Built-in support for domain events with automatic serialization
- **🔀 Multi-Topic Support**: Publish and consume across multiple topics with pattern matching
- **🌍 Environment Integration**: Automatic parsing of `RABBITMQ_URL` and other environment variables
- **🛡️ Robust Error Handling**: Comprehensive validation and custom exceptions with detailed error messages
- **📊 Logging Integration**: Built-in structured logging for debugging and monitoring
- **🔒 Type Safety**: Full type hints and mypy compatibility for better development experience
- **✅ High Test Coverage**: 100% test coverage with comprehensive test suite
- **📦 Modern Python**: Compatible with Python 3.9+ using modern Python features

## Installation

### Using pip

```bash
pip install bunnystream
```

### Using uv (recommended)

```bash
uv add bunnystream
```

### From source

```bash
git clone https://github.com/MarcFord/bunnystream.git
cd bunnystream
uv sync
```

## Quick Start

### Basic Producer

```python
from bunnystream import BunnyStreamConfig, Warren
from bunnystream.events import BaseEvent

# Configure as producer
config = BunnyStreamConfig(
    mode="producer",
    exchange_name="my_events",
    rabbit_host="localhost"
)

# Create Warren instance
warren = Warren(config)

# Define custom event
class OrderCreated(BaseEvent):
    TOPIC = "order.created"
    EXCHANGE = "my_events"

# Connect and publish
warren.connect()
event = OrderCreated(warren, order_id="12345", customer_id="67890", total=99.99)
event.fire()
warren.disconnect()
```

### Basic Consumer

```python
import json
from bunnystream import BunnyStreamConfig, Warren
from bunnystream.subscription import Subscription

def message_handler(ch, method, properties, body):
    message = json.loads(body.decode('utf-8'))
    print(f"Received: {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Configure as consumer
config = BunnyStreamConfig(mode="consumer", exchange_name="my_events")
config.add_subscription(
    Subscription(exchange_name="my_events", topic="order.*")
)

# Create Warren instance and start consuming
warren = Warren(config)
warren.connect()
warren.start_consuming(message_handler)
# warren.start_io_loop()  # Blocks until stopped
```

## Usage Examples

### Basic Producer and Consumer

Create a simple producer that publishes order events:

```python
from bunnystream import BunnyStreamConfig, Warren
from bunnystream.events import BaseEvent

class OrderEvent(BaseEvent):
    TOPIC = "order.created"
    EXCHANGE = "ecommerce"

# Producer setup
producer_config = BunnyStreamConfig(mode="producer", exchange_name="ecommerce")
producer = Warren(producer_config)
producer.connect()

# Create and publish event
order = OrderEvent(
    warren=producer,
    order_id="ORD-001",
    customer_id="CUST-123",
    total=49.99,
    items=["product-1", "product-2"]
)
order.fire()
producer.disconnect()
```

Consumer that processes order events:

```python
import json
from bunnystream import BunnyStreamConfig, Warren
from bunnystream.subscription import Subscription

def process_order(ch, method, properties, body):
    try:
        order_data = json.loads(body.decode('utf-8'))
        print(f"Processing order: {order_data['order_id']}")
        print(f"Customer: {order_data['customer_id']}")
        print(f"Total: ${order_data['total']}")
        
        # Process the order...
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing order: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# Consumer setup
consumer_config = BunnyStreamConfig(mode="consumer", exchange_name="ecommerce")
consumer_config.add_subscription(
    Subscription(exchange_name="ecommerce", topic="order.created")
)

consumer = Warren(consumer_config)
consumer.connect()
consumer.start_consuming(process_order)
```

### Multi-Topic Event System

BunnyStream excels at multi-topic event systems. See the complete [Multi-Topic Demo](examples/multi_topic_demo.py) for a comprehensive example.

```python
from bunnystream import BunnyStreamConfig, Warren
from bunnystream.subscription import Subscription
from bunnystream.events import BaseEvent

# Define events for different domains
class UserRegistered(BaseEvent):
    TOPIC = "user.registered"
    EXCHANGE = "app_events"

class OrderCreated(BaseEvent):
    TOPIC = "order.created"
    EXCHANGE = "app_events"

class ProductUpdated(BaseEvent):
    TOPIC = "product.updated"
    EXCHANGE = "app_events"

# Multi-topic consumer setup
config = BunnyStreamConfig(mode="consumer", exchange_name="app_events")

# Subscribe to multiple topic patterns
subscriptions = [
    Subscription(exchange_name="app_events", topic="user.*"),
    Subscription(exchange_name="app_events", topic="order.*"),
    Subscription(exchange_name="app_events", topic="product.*")
]

for subscription in subscriptions:
    config.add_subscription(subscription)

def handle_all_events(ch, method, properties, body):
    message = json.loads(body.decode('utf-8'))
    routing_key = method.routing_key
    
    if routing_key.startswith('user.'):
        print(f"User event: {message}")
    elif routing_key.startswith('order.'):
        print(f"Order event: {message}")
    elif routing_key.startswith('product.'):
        print(f"Product event: {message}")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

consumer = Warren(config)
consumer.connect()
consumer.start_consuming(handle_all_events)
```

### Environment Configuration

BunnyStream supports automatic configuration via environment variables:

```bash
# Set RabbitMQ connection URL
export RABBITMQ_URL="amqp://user:pass@rabbitmq.example.com:5672/production"

# Or set individual components
export RABBITMQ_HOST="rabbitmq.example.com"
export RABBITMQ_PORT="5672"
export RABBITMQ_USER="myuser"
export RABBITMQ_PASS="mypass"
export RABBITMQ_VHOST="/production"
```

```python
from bunnystream import BunnyStreamConfig, Warren

# Configuration automatically uses environment variables
config = BunnyStreamConfig(mode="producer")
warren = Warren(config)

print(f"Connecting to: {config.rabbit_host}:{config.rabbit_port}")
print(f"Using vhost: {config.rabbit_vhost}")
```

## API Reference

### Warren Class

The main class for managing RabbitMQ connections and operations.

```python
class Warren:
    def __init__(self, config: BunnyStreamConfig)
    
    # Connection management
    def connect(self) -> None
    def disconnect(self) -> None
    def start_io_loop(self) -> None
    def stop_io_loop(self) -> None
    
    # Publishing
    def publish(self, message: str, exchange: str, topic: str, 
                exchange_type: ExchangeType = ExchangeType.topic) -> None
    
    # Consuming
    def start_consuming(self, callback: Callable) -> None
    def stop_consuming(self) -> None
    
    # Properties
    @property
    def config(self) -> BunnyStreamConfig
    @property
    def bunny_mode(self) -> str
    @property
    def connection_parameters(self) -> pika.ConnectionParameters
```

### BunnyStreamConfig Class

Configuration class for BunnyStream connections.

```python
class BunnyStreamConfig:
    def __init__(
        self,
        mode: str,  # "producer" or "consumer"
        exchange_name: Optional[str] = None,
        rabbit_host: Optional[str] = None,
        rabbit_port: Optional[Union[int, str]] = None,
        rabbit_vhost: Optional[str] = None,
        rabbit_user: Optional[str] = None,
        rabbit_pass: Optional[str] = None
    )
    
    # Subscription management
    def add_subscription(self, subscription: Subscription) -> None
    def remove_subscription(self, subscription: Subscription) -> None
    
    # Properties for connection parameters
    @property
    def url(self) -> str  # Complete AMQP URL
    @property
    def subscriptions(self) -> List[Subscription]
    @property
    def subscription_mappings(self) -> Dict[str, Dict]
```

### BaseEvent Class

Base class for creating domain events.

```python
class BaseEvent:
    TOPIC: Optional[str] = None
    EXCHANGE: Optional[str] = None
    EXCHANGE_TYPE: ExchangeType = ExchangeType.topic
    
    def __init__(self, warren: Warren, **data)
    
    def fire(self) -> None  # Publish the event
    def serialize(self) -> str  # Get JSON representation
    
    @property
    def json(self) -> str  # JSON-serialized event data
```

### Subscription Class

Represents a subscription to a message exchange.

```python
@dataclass
class Subscription:
    exchange_name: str
    exchange_type: ExchangeType = ExchangeType.topic
    topic: str = ""
```

## Configuration

### RabbitMQ URL Format

The `RABBITMQ_URL` environment variable should follow this format:

```
amqp[s]://[username[:password]]@host[:port][/vhost]
```

Examples:
- `amqp://guest:guest@localhost:5672/`
- `amqps://user:pass@secure.example.com:5671/production`
- `amqp://myuser@rabbit.local:5672/app`

### Advanced Configuration

```python
config = BunnyStreamConfig(mode="consumer")

# Connection settings
config.heartbeat = 600
config.connection_attempts = 3
config.retry_delay = 5.0
config.socket_timeout = 10.0

# Consumer settings
config.prefetch_count = 10

# SSL settings (for amqps://)
config.ssl = True
config.ssl_options = {
    'ca_certs': '/path/to/ca.pem',
    'cert_reqs': ssl.CERT_REQUIRED
}
```

## Event System

BunnyStream provides a powerful event system built on top of RabbitMQ:

### Event Definition

```python
from bunnystream.events import BaseEvent
from pika.exchange_type import ExchangeType

class UserRegistered(BaseEvent):
    TOPIC = "user.registered"
    EXCHANGE = "user_events"
    EXCHANGE_TYPE = ExchangeType.topic
    
    def __init__(self, warren: Warren, user_id: str, email: str, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update({
            'event_type': 'user.registered',
            'user_id': user_id,
            'email': email
        })
```

### Event Metadata

Events automatically include metadata:

```python
event = UserRegistered(warren, user_id="123", email="user@example.com")
print(event.json)
# {
#   "event_type": "user.registered",
#   "user_id": "123", 
#   "email": "user@example.com",
#   "_meta_": {
#     "hostname": "app-server-01",
#     "timestamp": "2025-01-01 12:00:00",
#     "host_ip_address": "10.0.1.5",
#     "host_os_info": {...},
#     "bunnystream_version": "1.0.0"
#   }
# }
```

## Error Handling

BunnyStream provides comprehensive error handling:

```python
from bunnystream.exceptions import (
    BunnyStreamConfigurationError,
    WarrenNotConnected,
    RabbitHostError,
    RabbitPortError,
    SubscriptionsNotSetError
)

try:
    config = BunnyStreamConfig(mode="invalid_mode")
except BunnyStreamConfigurationError as e:
    print(f"Configuration error: {e}")

try:
    warren = Warren(config)
    warren.publish("message", "exchange", "topic")  # Without connecting
except WarrenNotConnected as e:
    print(f"Connection error: {e}")
```

## Examples

BunnyStream includes several comprehensive examples:

- **[Multi-Topic Demo](examples/multi_topic_demo.py)**: Complete multi-topic producer/consumer system
- **[Warren Events Demo](examples/warren_events_demo.py)**: Basic event publishing and consuming  
- **[RabbitMQ URL Demo](examples/rabbitmq_url_demo.py)**: Environment variable configuration

Run any example:

```bash
cd examples
python multi_topic_demo.py
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/MarcFord/bunnystream.git
cd bunnystream

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync --dev

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage report
make test-coverage

# Run specific test file
python -m pytest tests/test_warren.py -v

# Run tests with coverage details
python -m pytest --cov=src/bunnystream --cov-report=term-missing
```

### Code Quality

```bash
# Run all quality checks
make lint

# Run individual tools
make format        # Black + isort formatting
make type-check    # mypy type checking
make lint-check    # pylint code analysis

# Pre-commit checks
make pre-release   # Run all checks before releasing
```

### Available Make Commands

```bash
make help          # Show all available commands
make clean         # Clean build artifacts
make build         # Build the package
make release-patch # Create patch release (x.y.Z)
make release-minor # Create minor release (x.Y.0)  
make release-major # Create major release (X.0.0)
```

## Contributing

We welcome contributions! Here's how to get started:

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/bunnystream.git
cd bunnystream
```

### 2. Set up Development Environment

```bash
uv sync --dev
source .venv/bin/activate
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

- Write your code following the existing style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass: `make test`
- Check code quality: `make lint`

### 5. Submit a Pull Request

- Push your branch to your fork
- Create a pull request with a clear description
- Ensure all CI checks pass

### Development Guidelines

- **Testing**: Maintain 100% test coverage
- **Documentation**: Update docstrings and README for new features
- **Type Hints**: Include type hints for all new code
- **Code Style**: Follow PEP 8, use Black for formatting
- **Commit Messages**: Use clear, descriptive commit messages

### Reporting Issues

- Use the [GitHub issue tracker](https://github.com/MarcFord/bunnystream/issues)
- Include Python version, BunnyStream version, and RabbitMQ version
- Provide a minimal reproducible example
- Check existing issues before creating new ones

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

The GPL v3 ensures that BunnyStream remains free and open source, and that any derivatives or improvements are also shared with the community.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes in each version.

## Support

- **Documentation**: [GitHub README](https://github.com/MarcFord/bunnystream#readme)
- **Issues**: [GitHub Issues](https://github.com/MarcFord/bunnystream/issues)
- **Source Code**: [GitHub Repository](https://github.com/MarcFord/bunnystream)

---

**BunnyStream** - Making event-driven messaging simple and reliable. 🐰✨