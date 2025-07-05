"""
BunnyStream Comprehensive API Documentation and Examples.

This module provides detailed documentation and examples for all BunnyStream
components. Use help() on any component to see detailed information.

For interactive help, try:
    >>> import bunnystream
    >>> help(bunnystream)
    >>> help(bunnystream.Warren)
    >>> help(bunnystream.BunnyStreamConfig)
    >>> help(bunnystream.BaseEvent)
"""


def show_examples():
    """
    Display comprehensive examples for BunnyStream usage.

    This function demonstrates common patterns and use cases for BunnyStream,
    including setup, configuration, publishing, consuming, and monitoring.
    """

    print("""
=== BunnyStream Comprehensive Examples ===

1. BASIC SETUP AND CONNECTION
    
    # Simple producer setup
    from bunnystream import Warren, BunnyStreamConfig
    
    config = BunnyStreamConfig(mode="producer")
    warren = Warren(config)
    warren.connect()
    
    # Check connection status
    print(f"Connected: {warren.is_connected}")
    print(f"Status: {warren.connection_status}")

2. PUBLISHING MESSAGES

    # Simple message publishing
    warren.publish(
        message='{"event": "user_login", "user_id": 123}',
        exchange="user_events",
        topic="user.login"
    )
    
    # Type-safe event publishing
    from bunnystream import BaseEvent
    from pika.exchange_type import ExchangeType
    
    class UserLoginEvent(BaseEvent):
        EXCHANGE = "user_events"
        TOPIC = "user.login"
        EXCHANGE_TYPE = ExchangeType.topic
    
    event = UserLoginEvent({
        "user_id": 123,
        "timestamp": "2025-01-01T12:00:00Z",
        "ip_address": "192.168.1.1"
    })
    event.fire(warren)

3. CONSUMING MESSAGES

    # Simple message consumption
    def message_handler(channel, method, properties, body):
        print(f"Received: {body.decode()}")
        # Message is automatically acknowledged
    
    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)
    warren.connect()
    warren.start_consuming(message_handler)
    warren.start_io_loop()  # Blocking call
    
    # Type-safe event consumption
    from bunnystream import BaseReceivedEvent
    
    def typed_message_handler(channel, method, properties, body):
        event = BaseReceivedEvent(body)
        print(f"User {event.user_id} logged in at {event.timestamp}")
        print(f"From IP: {event.ip_address}")

4. CUSTOM SUBSCRIPTIONS
    
    from bunnystream import Subscription
    from pika.exchange_type import ExchangeType
    
    # Create custom subscription
    subscription = Subscription(
        exchange_name="orders",
        exchange_type=ExchangeType.topic,
        topic="order.created"
    )
    
    config = BunnyStreamConfig(
        mode="consumer",
        subscriptions=[subscription]
    )
    warren = Warren(config)

5. ENVIRONMENT CONFIGURATION

    # Set environment variables
    import os
    os.environ['RABBITMQ_URL'] = 'amqp://user:pass@rabbit.example.com:5672/prod'
    os.environ['RABBIT_PREFETCH_COUNT'] = '10'
    
    # Auto-configure from environment
    config = BunnyStreamConfig()
    print(f"Host: {config.rabbit_host}")
    print(f"Prefetch: {config.prefetch_count}")

6. SSL/TLS CONNECTIONS

    import ssl
    
    config = BunnyStreamConfig(
        rabbit_host="secure.rabbit.example.com",
        rabbit_port=5671,
        ssl=True,
        ssl_options={
            'cert_reqs': ssl.CERT_REQUIRED,
            'ca_certs': '/path/to/ca_bundle.crt',
            'certfile': '/path/to/client.crt',
            'keyfile': '/path/to/client.key'
        }
    )

7. CONNECTION MONITORING

    # Basic monitoring
    warren = Warren(config)
    if warren.is_connected:
        print("✅ Connected to RabbitMQ")
    else:
        print(f"❌ Status: {warren.connection_status}")
    
    # Detailed monitoring
    info = warren.get_connection_info()
    print(f"Host: {info['host']}:{info['port']}")
    print(f"Virtual Host: {info['virtual_host']}")
    print(f"Mode: {info['mode']}")
    print(f"Has Channel: {info['has_channel']}")
    
    # Monitoring loop
    import time
    def monitor_connection():
        while True:
            status = warren.connection_status
            if status == "connected":
                print("✅ RabbitMQ connection healthy")
            elif status == "disconnected":
                print("❌ Connection lost - attempting reconnect")
                warren.connect()
            else:
                print("⏳ Connection not initialized")
            time.sleep(30)

8. ERROR HANDLING

    from bunnystream import (
        WarrenNotConnected,
        BunnyStreamConfigurationError,
        RabbitHostError
    )
    
    try:
        warren.publish("message", "exchange", "topic")
    except WarrenNotConnected:
        print("Not connected - attempting to connect")
        warren.connect()
    except BunnyStreamConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

9. ADVANCED EVENT PATTERNS

    # Event with metadata
    class OrderEvent(BaseEvent):
        EXCHANGE = "orders"
        TOPIC = "order.created"
        
        def __init__(self, order_data):
            super().__init__(order_data)
            self["timestamp"] = self.get_current_timestamp()
            self["host"] = self.get_host_ip_address()
    
    order = OrderEvent({
        "order_id": "ORD-123",
        "customer_id": 456,
        "amount": 99.99
    })
    order.fire(warren)
    
    # Event consumption with data object
    from bunnystream import DataObject
    
    def process_order(channel, method, properties, body):
        event = BaseReceivedEvent(body)
        order_data = DataObject(event.data)
        
        print(f"Order {order_data.order_id}")
        print(f"Customer: {order_data.customer_id}")
        print(f"Amount: ${order_data.amount}")

10. LIFECYCLE MANAGEMENT

    # Proper startup
    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)
    
    try:
        warren.connect()
        warren.start_consuming(message_handler)
        warren.start_io_loop()  # Blocking
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        warren.stop_consuming()
        warren.stop_io_loop()
        warren.disconnect()

11. MULTIPLE SUBSCRIPTIONS

    subscriptions = [
        Subscription("users", ExchangeType.topic, "user.*"),
        Subscription("orders", ExchangeType.topic, "order.*"),
        Subscription("notifications", ExchangeType.direct, "email")
    ]
    
    config = BunnyStreamConfig(
        mode="consumer",
        subscriptions=subscriptions
    )

12. LOGGING CONFIGURATION

    from bunnystream import configure_bunny_logger, get_bunny_logger
    
    # Configure package-wide logging
    configure_bunny_logger(level="DEBUG", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Get component-specific logger
    logger = get_bunny_logger("my_app")
    logger.info("Application started")
    logger.debug("Debug information")

=== COMMON PATTERNS ===

Pattern 1: Request-Response with RPC
    # Publisher
    import uuid
    correlation_id = str(uuid.uuid4())
    warren.publish(
        message='{"action": "get_user", "user_id": 123}',
        exchange="rpc_requests",
        topic="user.get",
        properties=pika.BasicProperties(
            correlation_id=correlation_id,
            reply_to="rpc_responses"
        )
    )

Pattern 2: Dead Letter Queue Setup
    subscription = Subscription(
        exchange_name="orders",
        topic="order.process",
        queue_arguments={
            'x-queue-type': 'quorum',
            'x-dead-letter-exchange': 'orders.dlx',
            'x-dead-letter-routing-key': 'failed'
        }
    )

Pattern 3: Message TTL
    warren.publish(
        message="Temporary message",
        exchange="temp",
        topic="temp.message",
        properties=pika.BasicProperties(expiration="60000")  # 60 seconds
    )

For more examples and detailed API documentation, use:
    help(bunnystream.Warren)
    help(bunnystream.BunnyStreamConfig)
    help(bunnystream.BaseEvent)
    help(bunnystream.BaseReceivedEvent)
""")


def show_troubleshooting():
    """Show common troubleshooting tips and solutions."""

    print("""
=== BUNNYSTREAM TROUBLESHOOTING GUIDE ===

COMMON ISSUES AND SOLUTIONS:

1. Connection Refused
   Problem: warren.is_connected returns False
   Solutions:
   - Check if RabbitMQ is running: systemctl status rabbitmq-server
   - Verify host and port: warren.get_connection_info()
   - Check firewall settings
   - Verify credentials

2. Permission Denied
   Problem: 403 errors when declaring queues/exchanges
   Solutions:
   - Check user permissions in RabbitMQ management
   - Verify virtual host access
   - Use rabbitmqctl set_permissions command

3. Messages Not Received
   Problem: Consumer not receiving messages
   Solutions:
   - Check queue bindings: binding key matches routing key
   - Verify exchange type (topic vs direct)
   - Check prefetch_count setting
   - Ensure consumer is running: warren.start_consuming()

4. SSL Connection Issues
   Problem: SSL/TLS connection fails
   Solutions:
   - Verify SSL certificates and paths
   - Check SSL port (usually 5671)
   - Validate certificate chain
   - Check SSL options configuration

5. Memory/Performance Issues
   Problem: High memory usage or slow performance
   Solutions:
   - Tune prefetch_count for consumers
   - Monitor queue depths
   - Use appropriate exchange types
   - Consider connection pooling

DEBUGGING COMMANDS:

# Enable debug logging
from bunnystream import configure_bunny_logger
configure_bunny_logger(level="DEBUG")

# Check connection info
info = warren.get_connection_info()
print(f"Connection details: {info}")

# Monitor connection status
import time
while True:
    print(f"Status: {warren.connection_status}")
    time.sleep(5)

# Test basic connectivity
try:
    warren.connect()
    print("✅ Connection successful")
except Exception as e:
    print(f"❌ Connection failed: {e}")

ENVIRONMENT VARIABLE DEBUGGING:

import os
print("RABBITMQ_URL:", os.getenv('RABBITMQ_URL', 'Not set'))
print("RABBIT_HOST:", os.getenv('RABBIT_HOST', 'Not set'))
print("RABBIT_PORT:", os.getenv('RABBIT_PORT', 'Not set'))
print("RABBIT_USER:", os.getenv('RABBIT_USER', 'Not set'))

PERFORMANCE MONITORING:

# Monitor queue status (requires management plugin)
# Access http://localhost:15672 for RabbitMQ management interface

# Check consumer lag
def check_consumer_performance():
    info = warren.get_connection_info()
    if info['has_channel']:
        print("✅ Channel available")
    else:
        print("❌ No channel - check connection")

For more help:
- Check RabbitMQ logs: /var/log/rabbitmq/
- Use RabbitMQ management interface
- Enable BunnyStream debug logging
- Check network connectivity with telnet
""")


if __name__ == "__main__":
    print("BunnyStream Documentation and Examples")
    print("=====================================")
    print()
    print("Available functions:")
    print("- show_examples(): Comprehensive usage examples")
    print("- show_troubleshooting(): Common issues and solutions")
    print()
    print("For interactive help:")
    print(">>> import bunnystream")
    print(">>> help(bunnystream)")
    print(">>> help(bunnystream.Warren)")
    print()
    print("To see examples:")
    print(">>> from bunnystream.docs import show_examples")
    print(">>> show_examples()")
