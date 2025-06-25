#!/usr/bin/env python3
"""
Example demonstrating BaseReceivedEvent for message consumption.

This example shows how to:
1. Use BaseReceivedEvent for convenient message handling
2. Handle different message formats gracefully
3. Access nested data with attribute and dictionary syntax
4. Process real-world event messages with metadata
"""

import json
import threading
import time

from pika.exchange_type import ExchangeType

from bunnystream.config import BunnyStreamConfig
from bunnystream.events import BaseEvent, BaseReceivedEvent
from bunnystream.subscription import Subscription
from bunnystream.warren import Warren


class OrderCreatedEvent(BaseEvent):
    """Event published when an order is created."""

    TOPIC = "order.created"
    EXCHANGE = "ecommerce"
    EXCHANGE_TYPE = ExchangeType.topic


class UserRegisteredEvent(BaseEvent):
    """Event published when a user registers."""

    TOPIC = "user.registered"
    EXCHANGE = "ecommerce"
    EXCHANGE_TYPE = ExchangeType.topic


def create_sample_events(warren: Warren) -> None:
    """Create and publish sample events with various data structures."""

    print("📤 Publishing sample events...")

    # Order event with nested customer data
    order_event = OrderCreatedEvent(
        warren,
        order_id="ORD-12345",
        customer={
            "id": "CUST-67890",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
            },
        },
        items=[
            {
                "product_id": "PROD-001",
                "name": "Wireless Headphones",
                "quantity": 1,
                "price": 99.99,
            },
            {
                "product_id": "PROD-002",
                "name": "Phone Case",
                "quantity": 2,
                "price": 19.99,
            },
        ],
        total=139.97,
        currency="USD",
        status="pending",
    )
    order_event.fire()

    # User registration event
    user_event = UserRegisteredEvent(
        warren,
        user_id="USER-54321",
        email="john@example.com",
        profile={
            "first_name": "John",
            "last_name": "Smith",
            "age": 30,
            "preferences": {
                "newsletter": True,
                "notifications": {"email": True, "sms": False, "push": True},
            },
        },
        registration_source="web",
    )
    user_event.fire()

    print("✅ Sample events published successfully!")


def handle_order_events(ch, method, _properties, body):
    """Handle order-related events."""
    try:
        print("\n🛒 Processing Order Event")
        print("=" * 40)

        # Use BaseReceivedEvent for convenient access
        event = BaseReceivedEvent(body.decode("utf-8"))

        # Basic order information
        print(f"Order ID: {event.order_id}")
        print(f"Total: {event.currency} {event.total}")
        print(f"Status: {event.status}")

        # Customer information (nested object access)
        customer = event.customer
        print("\nCustomer:")
        print(f"  Name: {customer.name}")
        print(f"  Email: {customer.email}")
        print(f"  ID: {customer.id}")

        # Nested address information
        address = customer.address
        address_str = f"{address.street}, {address.city}, {address.state} {address.zip}"
        print(f"  Address: {address_str}")

        # Items array (remains as list, access with indexing)
        print(f"\nItems ({len(event.items)} total):")
        for i, item in enumerate(event.items):
            print(f"  {i+1}. {item['name']} x{item['quantity']} - ${item['price']}")

        # Access metadata if present (check safely)
        if event.data and isinstance(event.data, dict) and "_meta_" in event.data:
            # Use dictionary access to avoid protected member warnings
            meta_data = event.data["_meta_"]
            print("\nEvent Metadata:")
            print(f"  Timestamp: {meta_data.get('timestamp', 'N/A')}")
            print(f"  Source Host: {meta_data.get('hostname', 'N/A')}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except (KeyError, TypeError, AttributeError) as e:
        print(f"❌ Error processing order event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def handle_user_events(ch, method, _properties, body):
    """Handle user-related events."""
    try:
        print("\n👤 Processing User Event")
        print("=" * 40)

        event = BaseReceivedEvent(body.decode("utf-8"))

        # User information
        print(f"User ID: {event.user_id}")
        print(f"Email: {event.email}")
        print(f"Registration Source: {event.registration_source}")

        # Profile information (nested)
        profile = event.profile
        print("\nProfile:")
        print(f"  Name: {profile.first_name} {profile.last_name}")
        print(f"  Age: {profile.age}")

        # Deeply nested preferences
        preferences = profile.preferences
        print("\nPreferences:")
        print(f"  Newsletter: {preferences.newsletter}")

        notifications = preferences.notifications
        print("  Notifications:")
        print(f"    Email: {notifications.email}")
        print(f"    SMS: {notifications.sms}")
        print(f"    Push: {notifications.push}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except (KeyError, TypeError, AttributeError) as e:
        print(f"❌ Error processing user event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def demonstrate_edge_cases():
    """Demonstrate how BaseReceivedEvent handles edge cases."""
    print("\n🧪 Demonstrating Edge Cases")
    print("=" * 40)

    # Valid JSON dictionary
    print("1. Valid JSON dictionary:")
    event1 = BaseReceivedEvent('{"name": "John", "age": 30}')
    print(f"   Name: {event1.name}, Age: {event1.age}")

    # Valid JSON but not a dictionary
    print("\n2. Valid JSON array:")
    event2 = BaseReceivedEvent('["apple", "banana", "cherry"]')
    print(f"   Data type: {type(event2.data)}")
    print(f"   Data: {event2.data}")
    try:
        # This will fail because data is not a dict
        _ = event2.name
    except TypeError as e:
        print(f"   ❌ Expected error: {e}")

    # Invalid JSON
    print("\n3. Invalid JSON:")
    event3 = BaseReceivedEvent("invalid json string")
    print(f"   Parsed data: {event3.data}")
    # Access raw data through the data attribute to avoid protected member access
    print(f"   Has raw data: {hasattr(event3, '_raw_data')}")
    try:
        _ = event3.name
    except TypeError as e:
        print(f"   ❌ Expected error: {e}")

    # Empty dictionary
    print("\n4. Empty dictionary:")
    event4 = BaseReceivedEvent("{}")
    print(f"   Data: {event4.data}")
    try:
        _ = event4.missing_key
    except KeyError as e:
        print(f"   ❌ Expected error: {e}")

    # Nested structure
    print("\n5. Complex nested structure:")
    complex_data = {"level1": {"level2": {"level3": {"value": "deep nested value"}}}}
    event5 = BaseReceivedEvent(json.dumps(complex_data))
    print(f"   Deep value: {event5.level1.level2.level3.value}")


def setup_consumer() -> Warren:
    """Set up consumer Warren instance."""
    config = BunnyStreamConfig(mode="consumer", exchange_name="ecommerce")

    # Add subscriptions for different event types
    subscriptions = [
        Subscription(exchange_name="ecommerce", topic="order.*"),
        Subscription(exchange_name="ecommerce", topic="user.*"),
    ]

    for subscription in subscriptions:
        config.add_subscription(subscription)

    consumer = Warren(config)
    return consumer


def setup_producer() -> Warren:
    """Set up producer Warren instance."""
    config = BunnyStreamConfig(mode="producer", exchange_name="ecommerce")
    producer = Warren(config)
    return producer


def main():
    """Main demonstration function."""
    print("🐰 BunnyStream BaseReceivedEvent Demo")
    print("=" * 50)

    # Demonstrate edge cases first
    demonstrate_edge_cases()

    producer = None
    consumer = None

    try:
        # Set up producer
        print("\n📡 Setting up producer...")
        producer = setup_producer()
        producer.connect()

        # Set up consumer
        print("📺 Setting up consumer...")
        consumer = setup_consumer()
        consumer.connect()

        # Start consuming in a separate thread
        def start_consuming():
            def unified_handler(ch, method, properties, body):
                routing_key = method.routing_key

                if routing_key.startswith("order."):
                    handle_order_events(ch, method, properties, body)
                elif routing_key.startswith("user."):
                    handle_user_events(ch, method, properties, body)
                else:
                    print(f"⚠️  Unknown event type: {routing_key}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            consumer.start_consuming(unified_handler)

        consumer_thread = threading.Thread(target=start_consuming, daemon=True)
        consumer_thread.start()

        # Give consumer time to start
        time.sleep(1)

        # Publish sample events
        create_sample_events(producer)

        # Wait for messages to be processed
        print("\n⏳ Processing messages (waiting 3 seconds)...")
        time.sleep(3)

        print("\n✅ Demo completed successfully!")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except (ConnectionError, OSError) as e:
        print(f"\n❌ Connection error: {e}")
        print("Make sure RabbitMQ is running and accessible.")
    finally:
        # Clean up
        if consumer:
            try:
                consumer.stop_consuming()
                consumer.disconnect()
            except (ConnectionError, OSError):
                pass

        if producer:
            try:
                producer.disconnect()
            except (ConnectionError, OSError):
                pass


if __name__ == "__main__":
    main()
