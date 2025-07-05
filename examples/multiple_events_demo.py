#!/usr/bin/env python3
"""
Multiple Events Demo - Demonstrates the new recieve_events method

This demo shows how to use the Warren.recieve_events() method to consume
multiple event types with individual consumer tags for each event class.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path so we can import bunnystream
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bunnystream import BunnyStreamConfig, Warren
from bunnystream.events import BaseReceivedEvent
from bunnystream.logger import get_bunny_logger

# Set up logging
logger = get_bunny_logger("demo")


class UserLoginEvent(BaseReceivedEvent):
    """Event for user login actions."""

    EXCHANGE = "user_events"
    TOPIC = "user.login"

    def processes_event(self) -> None:
        """Process the user login event."""
        try:
            user_id = self.data.get("user_id", "unknown")
            username = self.data.get("username", "unknown")
            logger.info(f"🟢 User login: {username} (ID: {user_id})")
        except Exception as e:
            logger.error(f"Error processing login event: {e}")


class UserLogoutEvent(BaseReceivedEvent):
    """Event for user logout actions."""

    EXCHANGE = "user_events"
    TOPIC = "user.logout"

    def processes_event(self) -> None:
        """Process the user logout event."""
        try:
            user_id = self.data.get("user_id", "unknown")
            username = self.data.get("username", "unknown")
            logger.info(f"🔴 User logout: {username} (ID: {user_id})")
        except Exception as e:
            logger.error(f"Error processing logout event: {e}")


class OrderCreatedEvent(BaseReceivedEvent):
    """Event for order creation."""

    EXCHANGE = "order_events"
    TOPIC = "order.created"

    def processes_event(self) -> None:
        """Process the order created event."""
        try:
            order_id = self.data.get("order_id", "unknown")
            customer_id = self.data.get("customer_id", "unknown")
            total = self.data.get("total", 0)
            logger.info(
                f"📦 Order created: {order_id} for customer {customer_id}, total: ${total}"
            )
        except Exception as e:
            logger.error(f"Error processing order event: {e}")


def demo_multiple_events():
    """Demonstrate consumption of multiple event types."""

    print("=== Multiple Events Demo ===")
    print("This demo shows how Warren.recieve_events() sets up individual")
    print("consumer tags for each event class.\n")

    try:
        # Create Warren configuration for consumer mode
        config = BunnyStreamConfig(mode="consumer")
        warren = Warren(config)

        print("1. Connecting to RabbitMQ...")
        warren.connect()

        # Give connection time to establish
        time.sleep(2)

        if not warren.is_connected:
            print("❌ Failed to connect to RabbitMQ")
            print("Make sure RabbitMQ is running on localhost:5672")
            return

        print("✅ Connected to RabbitMQ")

        print("\n2. Setting up consumption for multiple event types...")

        # Set up consumption for multiple event classes
        # Each will get its own consumer tag
        event_classes = [UserLoginEvent, UserLogoutEvent, OrderCreatedEvent]
        warren.recieve_events(event_classes)

        print("✅ Set up consumption for:")
        for event_class in event_classes:
            print(
                f"   - {event_class.__name__}: {event_class.EXCHANGE}.{event_class.TOPIC}"
            )

        print(f"\n3. Warren now has {len(warren._consumer_tags)} consumer tags:")
        for i, tag in enumerate(warren._consumer_tags, 1):
            print(f"   Consumer {i}: {tag}")

        print("\n4. Starting IO loop to consume messages...")
        print("   Send messages to the exchanges/topics to see them processed")
        print("   Press Ctrl+C to stop\n")

        # Start the IO loop (this will block)
        warren.start_io_loop()

    except KeyboardInterrupt:
        print("\n\n🛑 Stopping demo...")
        warren.stop_consuming()
        warren.stop_io_loop()
        warren.disconnect()
        print("✅ Demo stopped cleanly")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Demo error: {e}")


def demo_publisher():
    """Demonstrate publishing test messages."""

    print("=== Publisher Demo ===")
    print("Publishing test messages to demonstrate the consumer\n")

    try:
        # Create Warren configuration for producer mode
        config = BunnyStreamConfig(mode="producer")
        warren = Warren(config)

        print("1. Connecting to RabbitMQ...")
        warren.connect()

        # Give connection time to establish
        time.sleep(2)

        if not warren.is_connected:
            print("❌ Failed to connect to RabbitMQ")
            return

        print("✅ Connected to RabbitMQ")

        print("\n2. Publishing test messages...")

        # Publish some test messages
        messages = [
            {
                "exchange": "user_events",
                "topic": "user.login",
                "message": '{"user_id": 123, "username": "alice", "timestamp": "2025-01-01T10:00:00Z"}',
            },
            {
                "exchange": "user_events",
                "topic": "user.logout",
                "message": '{"user_id": 123, "username": "alice", "timestamp": "2025-01-01T10:30:00Z"}',
            },
            {
                "exchange": "order_events",
                "topic": "order.created",
                "message": '{"order_id": "ORD-456", "customer_id": 789, "total": 99.99, "items": 3}',
            },
        ]

        for msg in messages:
            warren.publish(
                message=msg["message"], exchange=msg["exchange"], topic=msg["topic"]
            )
            print(f"✅ Published to {msg['exchange']}.{msg['topic']}")
            time.sleep(0.5)

        print("\n✅ All messages published")

        # Start IO loop briefly to ensure messages are sent
        warren.start_io_loop()

    except KeyboardInterrupt:
        print("\n🛑 Stopping publisher...")
        warren.stop_io_loop()
        warren.disconnect()
        print("✅ Publisher stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Publisher error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "publish":
        demo_publisher()
    else:
        demo_multiple_events()
