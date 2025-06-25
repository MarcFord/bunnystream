#!/usr/bin/env python3
"""
Multi-Topic Warren Demo

This example demonstrates how to:
1. Set up a Warren consumer that listens to multiple topics (events)
2. Set up a Warren producer that publishes events to multiple topics
3. Handle different event types with specific routing

The demo simulates a simple e-commerce system with:
- Order events (order.created, order.updated, order.cancelled)
- User events (user.registered, user.updated)
- Product events (product.created, product.updated)
"""

import json
import time

from bunnystream.config import BunnyStreamConfig
from bunnystream.events import BaseEvent
from bunnystream.exceptions import WarrenNotConnected
from bunnystream.subscription import Subscription
from bunnystream.warren import Warren


# Define custom event classes for different business domains
class OrderCreatedEvent(BaseEvent):
    """Event for order creation."""

    TOPIC = "order.created"
    EXCHANGE = "ecommerce_events"

    def __init__(self, warren: Warren, order_id: str, customer_id: str, **kwargs):
        super().__init__(warren, **kwargs)
        # Add order-specific data to the event data
        self.data.update(
            {
                "event_type": "order.created",
                "order_id": order_id,
                "customer_id": customer_id,
            }
        )


class OrderUpdatedEvent(BaseEvent):
    """Event for order updates."""

    TOPIC = "order.updated"
    EXCHANGE = "ecommerce_events"

    def __init__(self, warren: Warren, order_id: str, customer_id: str, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update(
            {
                "event_type": "order.updated",
                "order_id": order_id,
                "customer_id": customer_id,
            }
        )


class OrderCancelledEvent(BaseEvent):
    """Event for order cancellation."""

    TOPIC = "order.cancelled"
    EXCHANGE = "ecommerce_events"

    def __init__(self, warren: Warren, order_id: str, customer_id: str, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update(
            {
                "event_type": "order.cancelled",
                "order_id": order_id,
                "customer_id": customer_id,
            }
        )


class UserRegisteredEvent(BaseEvent):
    """Event for user registration."""

    TOPIC = "user.registered"
    EXCHANGE = "ecommerce_events"

    def __init__(self, warren: Warren, user_id: str, email: str, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update({"event_type": "user.registered", "user_id": user_id, "email": email})


class UserUpdatedEvent(BaseEvent):
    """Event for user updates."""

    TOPIC = "user.updated"
    EXCHANGE = "ecommerce_events"

    def __init__(self, warren: Warren, user_id: str, email: str, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update({"event_type": "user.updated", "user_id": user_id, "email": email})


class ProductCreatedEvent(BaseEvent):
    """Event for product creation."""

    TOPIC = "product.created"
    EXCHANGE = "ecommerce_events"

    def __init__(self, warren: Warren, product_id: str, name: str, price: float, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update(
            {
                "event_type": "product.created",
                "product_id": product_id,
                "name": name,
                "price": price,
            }
        )


class ProductUpdatedEvent(BaseEvent):
    """Event for product updates."""

    TOPIC = "product.updated"
    EXCHANGE = "ecommerce_events"

    def __init__(self, warren: Warren, product_id: str, name: str, price: float, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update(
            {
                "event_type": "product.updated",
                "product_id": product_id,
                "name": name,
                "price": price,
            }
        )


def message_handler(ch, method, _properties, body):
    """
    Handle incoming messages from multiple topics.

    This handler processes different event types and demonstrates
    how to handle multiple topics in a single consumer.
    """
    try:
        message = json.loads(body.decode("utf-8"))
        event_type = message.get("event_type", "unknown")
        routing_key = method.routing_key

        print("\n📨 Received message:")
        print(f"   Topic (routing key): {routing_key}")
        print(f"   Event type: {event_type}")
        print(f"   Timestamp: {message.get('timestamp', 'N/A')}")

        # Handle different event types
        if routing_key.startswith("order."):
            print(f"   Order ID: {message.get('order_id', 'N/A')}")
            print(f"   Customer ID: {message.get('customer_id', 'N/A')}")

            if event_type == "order.created":
                print("   🎉 Processing new order creation...")
            elif event_type == "order.updated":
                print("   📝 Processing order update...")
            elif event_type == "order.cancelled":
                print("   ❌ Processing order cancellation...")

        elif routing_key.startswith("user."):
            print(f"   User ID: {message.get('user_id', 'N/A')}")
            print(f"   Email: {message.get('email', 'N/A')}")

            if event_type == "user.registered":
                print("   👋 Processing new user registration...")
            elif event_type == "user.updated":
                print("   📝 Processing user profile update...")

        elif routing_key.startswith("product."):
            print(f"   Product ID: {message.get('product_id', 'N/A')}")
            print(f"   Product Name: {message.get('name', 'N/A')}")
            print(f"   Price: ${message.get('price', 'N/A')}")

            if event_type == "product.created":
                print("   📦 Processing new product creation...")
            elif event_type == "product.updated":
                print("   📝 Processing product update...")

        print("   ✅ Message processed successfully")

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(f"   ❌ Error processing message: {e}")
        # Reject the message and don't requeue it
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def setup_consumer():
    """Set up a Warren consumer that listens to multiple topics."""
    print("🔧 Setting up multi-topic consumer...")

    # Create consumer config
    consumer_config = BunnyStreamConfig(
        mode="consumer",
        rabbit_host="localhost",
        rabbit_port=5672,
        exchange_name="ecommerce_events",
    )

    # Add subscriptions for multiple topics
    subscriptions = [
        Subscription(exchange_name="ecommerce_events", topic="order.*"),
        Subscription(exchange_name="ecommerce_events", topic="user.*"),
        Subscription(exchange_name="ecommerce_events", topic="product.*"),
    ]

    for subscription in subscriptions:
        consumer_config.add_subscription(subscription)

    consumer = Warren(consumer_config)

    try:
        print("📡 Connecting consumer to RabbitMQ...")
        consumer.connect()

        print("🎯 Setting up subscriptions for multiple topics:")
        print("   - order.* (order events)")
        print("   - user.* (user events)")
        print("   - product.* (product events)")

        print("👂 Starting to consume messages...")
        print("   Press Ctrl+C to stop consuming")

        # Start consuming with the message handler
        consumer.start_consuming(message_handler)

    except KeyboardInterrupt:
        print("\n🛑 Stopping consumer...")
        consumer.stop_consuming()
        consumer.disconnect()
        print("✅ Consumer stopped successfully")
    except (ConnectionError, OSError, ValueError, WarrenNotConnected) as e:
        print(f"❌ Consumer error: {e}")
        print("\n💡 Note: This error is expected if RabbitMQ is not running.")
        print("   To use this demo with real RabbitMQ:")
        print("   1. Install and start RabbitMQ server")
        print("   2. Ensure it's accessible on localhost:5672")
        print("   3. Run this script again")
        print("\n📋 Consumer Configuration Summary:")
        print(f"   Mode: {consumer.bunny_mode}")
        print(f"   Exchange: {consumer_config.exchange_name}")
        print("   Subscribed Topics:")
        for sub in consumer_config.subscriptions:
            print(f"     - {sub.topic} (exchange: {sub.exchange_name})")
        # Try to cleanly disconnect if possible
        try:
            consumer.disconnect()
        except AttributeError:
            pass  # Consumer might not have been initialized


def setup_producer_and_publish():
    """Set up a Warren producer and publish events to multiple topics."""
    print("🔧 Setting up multi-topic producer...")

    # Create producer config
    producer_config = BunnyStreamConfig(
        mode="producer",
        rabbit_host="localhost",
        rabbit_port=5672,
        exchange_name="ecommerce_events",
    )

    producer = Warren(producer_config)

    try:
        print("📡 Connecting producer to RabbitMQ...")
        producer.connect()

        print("📤 Publishing events to multiple topics...")

        # Create and publish order events
        print("\n📦 Publishing order events...")

        order_created = OrderCreatedEvent(
            warren=producer,
            order_id="ORD-12345",
            customer_id="CUST-67890",
            total=99.99,
            items_count=3,
        )
        order_created.fire()
        print("   ✅ Published: order.created")

        time.sleep(1)  # Small delay for demonstration

        order_updated = OrderUpdatedEvent(
            warren=producer,
            order_id="ORD-12345",
            customer_id="CUST-67890",
            total=89.99,
            items_count=2,
            discount_applied=10.00,
        )
        order_updated.fire()
        print("   ✅ Published: order.updated")

        time.sleep(1)

        # Create and publish user events
        print("\n👤 Publishing user events...")

        user_registered = UserRegisteredEvent(
            warren=producer,
            user_id="USER-11111",
            email="john.doe@example.com",
            signup_method="email",
            referral_code="FRIEND123",
        )
        user_registered.fire()
        print("   ✅ Published: user.registered")

        time.sleep(1)

        user_updated = UserUpdatedEvent(
            warren=producer,
            user_id="USER-11111",
            email="john.doe@example.com",
            updated_fields=["phone", "address"],
        )
        user_updated.fire()
        print("   ✅ Published: user.updated")

        time.sleep(1)

        # Create and publish product events
        print("\n🛍️ Publishing product events...")

        product_created = ProductCreatedEvent(
            warren=producer,
            product_id="PROD-99999",
            name="Wireless Headphones",
            price=129.99,
            category="electronics",
            brand="TechCorp",
        )
        product_created.fire()
        print("   ✅ Published: product.created")

        time.sleep(1)

        product_updated = ProductUpdatedEvent(
            warren=producer,
            product_id="PROD-99999",
            name="Wireless Headphones Pro",  # Updated name
            price=149.99,  # Updated price
            category="electronics",
            brand="TechCorp",
            version="pro",
        )
        product_updated.fire()
        print("   ✅ Published: product.updated")

        # Publish a cancellation event
        print("\n❌ Publishing order cancellation...")
        order_cancelled = OrderCancelledEvent(
            warren=producer,
            order_id="ORD-12345",
            customer_id="CUST-67890",
            cancellation_reason="customer_request",
            refund_amount=89.99,
        )
        order_cancelled.fire()
        print("   ✅ Published: order.cancelled")

        print("\n🎉 Successfully published events to multiple topics!")
        print("   Topics used:")
        print("   - order.created, order.updated, order.cancelled")
        print("   - user.registered, user.updated")
        print("   - product.created, product.updated")

    except (ConnectionError, OSError, ValueError, WarrenNotConnected) as e:
        print(f"❌ Producer error: {e}")
        print("\n💡 Note: This error is expected if RabbitMQ is not running.")
        print("   To use this demo with real RabbitMQ:")
        print("   1. Install and start RabbitMQ server")
        print("   2. Ensure it's accessible on localhost:5672")
        print("   3. Run this script again")

        # Show what the events would look like
        print("\n📝 Here's what the events would look like:")

        order_created = OrderCreatedEvent(
            warren=producer,
            order_id="ORD-12345",
            customer_id="CUST-67890",
            total=99.99,
            items_count=3,
        )
        print(f"\n📦 Order Created Event JSON:\n{order_created.json}")

        user_registered = UserRegisteredEvent(
            warren=producer,
            user_id="USER-11111",
            email="john.doe@example.com",
            signup_method="email",
            referral_code="FRIEND123",
        )
        print(f"\n👤 User Registered Event JSON:\n{user_registered.json}")

        product_created = ProductCreatedEvent(
            warren=producer,
            product_id="PROD-99999",
            name="Wireless Headphones",
            price=129.99,
            category="electronics",
            brand="TechCorp",
        )
        print(f"\n🛍️ Product Created Event JSON:\n{product_created.json}")

    finally:
        producer.disconnect()
        print("✅ Producer disconnected")


def main():
    """Main function to demonstrate multi-topic functionality."""
    print("🐰 BunnyStream Multi-Topic Warren Demo")
    print("=" * 50)

    choice = input(
        """
Choose an option:
1. Start Consumer (listens to multiple topics)
2. Run Producer (publishes to multiple topics)
3. Run Both (producer first, then consumer)

Enter your choice (1, 2, or 3): """
    ).strip()

    if choice == "1":
        setup_consumer()
    elif choice == "2":
        setup_producer_and_publish()
    elif choice == "3":
        print("\n📤 Running producer first...")
        setup_producer_and_publish()
        print("\n" + "=" * 50)
        print("📨 Now starting consumer...")
        input("Press Enter to start the consumer (make sure RabbitMQ is running)...")
        setup_consumer()
    else:
        print("❌ Invalid choice. Please run the script again and choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
