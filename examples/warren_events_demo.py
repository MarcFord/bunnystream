#!/usr/bin/env python3
"""
Example script demonstrating BunnyStream publishing and consuming functionality.

This example shows how to:
1. Create a Warren instance for publishing events
2. Create and publish custom events
3. Set up a Warren instance for consuming messages
4. Define a message handler for received messages
"""

import json

from pika.exchange_type import ExchangeType

from bunnystream.config import BunnyStreamConfig
from bunnystream.events import BaseEvent
from bunnystream.subscription import Subscription
from bunnystream.warren import Warren


class OrderEvent(BaseEvent):
    """Custom event for order processing."""

    TOPIC = "order.created"
    EXCHANGE = "orders"
    EXCHANGE_TYPE = ExchangeType.topic


class NotificationEvent(BaseEvent):
    """Custom event for notifications."""

    TOPIC = "notification.sent"
    EXCHANGE = "notifications"
    EXCHANGE_TYPE = ExchangeType.fanout


def message_handler(channel, method, properties, body):
    """
    Handle incoming messages.

    Args:
        channel: The channel object
        method: Delivery method
        properties: Message properties
        body: The message body
    """
    try:
        message = json.loads(body.decode("utf-8"))
        print(f"Received message: {message}")
        print(f"Exchange: {method.exchange}")
        print(f"Routing key: {method.routing_key}")
        print(f"Content type: {properties.content_type}")
        print("-" * 50)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error processing message: {e}")


def demo_producer():
    """Demonstrate publishing events."""
    print("=== PRODUCER DEMO ===")

    # Create producer configuration
    config = BunnyStreamConfig(mode="producer")

    # Add custom subscriptions for different exchanges
    config.add_subscription(
        Subscription(exchange_name="orders", exchange_type=ExchangeType.topic, topic="order.*")
    )

    config.add_subscription(
        Subscription(exchange_name="notifications", exchange_type=ExchangeType.fanout, topic="")
    )

    # Create Warren instance
    warren = Warren(config)

    # Create and fire events
    order_event = OrderEvent(
        warren=warren, order_id=12345, customer_id=67890, amount=99.99, currency="USD"
    )

    notification_event = NotificationEvent(
        warren=warren,
        user_id=67890,
        message="Your order has been confirmed!",
        channel="email",
    )

    print("Publishing events...")

    # Note: In a real application, you would call connect() and start_io_loop()
    # Here we just demonstrate the event creation and serialization

    print("Order event JSON:")
    print(order_event.json)
    print()

    print("Notification event JSON:")
    print(notification_event.json)
    print()

    # In a real scenario, you would do:
    # warren.connect()
    # order_event.fire()
    # notification_event.fire()
    # warren.start_io_loop()


def demo_consumer():
    """Demonstrate consuming messages."""
    print("=== CONSUMER DEMO ===")

    # Create consumer configuration
    config = BunnyStreamConfig(mode="consumer")
    config.prefetch_count = 5  # Process up to 5 messages at a time

    # Add subscriptions for exchanges we want to consume from
    config.add_subscription(
        Subscription(
            exchange_name="orders",
            exchange_type=ExchangeType.topic,
            topic="order.*",  # Listen to all order events
        )
    )

    config.add_subscription(
        Subscription(
            exchange_name="notifications",
            exchange_type=ExchangeType.fanout,
            topic="",  # Fanout doesn't use routing keys
        )
    )

    # Create Warren instance
    warren = Warren(config)

    print(f"Consumer mode: {warren.bunny_mode}")
    print(f"Prefetch count: {config.prefetch_count}")
    print("Subscriptions:")
    for sub in config.subscriptions:
        print(f"  - Exchange: {sub.exchange_name}, Type: {sub.exchange_type}, Topic: {sub.topic}")

    # In a real scenario, you would do:
    # warren.connect()
    # warren.start_consuming(message_handler)
    # warren.start_io_loop()  # This blocks until stopped

    print("\nTo actually consume messages, you would:")
    print("1. warren.connect()")
    print("2. warren.start_consuming(message_handler)")
    print("3. warren.start_io_loop()  # Blocks until stopped")


def demo_configuration():
    """Demonstrate different configuration options."""
    print("=== CONFIGURATION DEMO ===")

    # Create config with custom RabbitMQ settings
    config = BunnyStreamConfig(
        mode="producer",
        rabbit_host="localhost",
        rabbit_port=5672,
        rabbit_vhost="/test",
        rabbit_user="test_user",
        rabbit_pass="test_pass",
        exchange_name="my_app",
    )

    # Set advanced options
    config.prefetch_count = 10
    config.heartbeat = 60
    config.connection_attempts = 3

    print(f"RabbitMQ URL: {config.url}")
    print(f"Exchange: {config.exchange_name}")
    print(f"Mode: {config.mode}")
    print(f"Prefetch count: {config.prefetch_count}")
    print(f"Heartbeat: {config.heartbeat}")
    print(f"Connection attempts: {config.connection_attempts}")

    # Show subscription mappings
    print("\nSubscription mappings:")
    for exchange, mapping in config.subscription_mappings.items():
        print(f"  {exchange}: {mapping}")


if __name__ == "__main__":
    print("BunnyStream Warren and Events Demo")
    print("=" * 40)
    print()

    demo_producer()
    print()

    demo_consumer()
    print()

    demo_configuration()
    print()

    print("Demo completed!")
    print("\nNote: This demo shows the API without actual RabbitMQ connections.")
    print("To use with real RabbitMQ, ensure RabbitMQ server is running and")
    print("call warren.connect() and warren.start_io_loop() methods.")
