#!/usr/bin/env python3
"""
Simple demonstration of BaseReceivedEvent functionality.

This standalone example shows how BaseReceivedEvent works without requiring
a running RabbitMQ instance. It demonstrates:

1. JSON parsing and convenient data access
2. Nested object handling with DataObject
3. Different access patterns (dictionary vs attribute)
4. Error handling for various edge cases
"""

import json

from bunnystream.events import BaseReceivedEvent


def demonstrate_basic_usage():
    """Show basic BaseReceivedEvent usage patterns."""
    print("📚 Basic BaseReceivedEvent Usage")
    print("=" * 40)

    # Simple event data
    simple_data = {
        "event_type": "user_login",
        "user_id": "12345",
        "timestamp": "2025-06-25T14:00:00Z",
        "ip_address": "192.168.1.100",
    }

    # Create event from dictionary
    event1 = BaseReceivedEvent(simple_data)
    print("1. From dictionary:")
    print(f"   Event type: {event1.event_type}")
    print(f"   User ID: {event1['user_id']}")  # Dictionary access
    print(f"   Timestamp: {event1.timestamp}")  # Attribute access

    # Create event from JSON string
    json_string = json.dumps(simple_data)
    event2 = BaseReceivedEvent(json_string)
    print("\n2. From JSON string:")
    print(f"   Same data: {event2.event_type == event1.event_type}")
    print(f"   IP Address: {event2.ip_address}")


def demonstrate_nested_access():
    """Show nested data handling with DataObject."""
    print("\n🏗️  Nested Data Access")
    print("=" * 40)

    # Complex nested event
    order_data = {
        "order_id": "ORD-789",
        "customer": {
            "id": "CUST-456",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "address": {
                "street": "456 Oak Ave",
                "city": "Springfield",
                "state": "IL",
                "postal_code": "62701",
                "country": "USA",
            },
        },
        "items": [
            {"name": "Laptop", "price": 999.99, "quantity": 1},
            {"name": "Mouse", "price": 29.99, "quantity": 2},
        ],
        "payment": {
            "method": "credit_card",
            "card": {"last_four": "1234", "type": "visa"},
        },
        "total": 1059.97,
    }

    event = BaseReceivedEvent(order_data)

    print("1. Direct access:")
    print(f"   Order ID: {event.order_id}")
    print(f"   Total: ${event.total}")

    print("\n2. Nested customer data:")
    customer = event.customer  # Returns DataObject
    print(f"   Customer: {customer.name} ({customer.email})")
    print(f"   Customer ID: {customer.id}")

    print("\n3. Deeply nested address:")
    address = customer.address  # Nested DataObject
    full_address = (
        f"{address.street}, {address.city}, {address.state} {address.postal_code}"
    )
    print(f"   Address: {full_address}")
    print(f"   Country: {address.country}")

    print("\n4. Payment information:")
    payment = event.payment
    print(f"   Method: {payment.method}")
    card = payment.card
    print(f"   Card: {card.type.title()} ending in {card.last_four}")

    print("\n5. Items list (remains as list):")
    for i, item in enumerate(event.items):
        print(f"   {i+1}. {item['name']} x{item['quantity']} - ${item['price']}")


def demonstrate_edge_cases():
    """Show how BaseReceivedEvent handles various edge cases."""
    print("\n🧪 Edge Cases & Error Handling")
    print("=" * 40)

    # Valid JSON dictionary
    print("1. ✅ Valid JSON dictionary:")
    event1 = BaseReceivedEvent('{"name": "John", "age": 30, "active": true}')
    print(f"   Name: {event1.name} (age {event1.age})")
    print(f"   Active: {event1.active}")

    # Valid JSON but not a dictionary
    print("\n2. ⚠️  Valid JSON but not a dictionary:")
    event2 = BaseReceivedEvent('["apple", "banana", "cherry"]')
    print(f"   Data type: {type(event2.data).__name__}")
    print(f"   Contents: {event2.data}")
    try:
        _ = event2.name
        print("   Unexpectedly succeeded!")
    except TypeError as e:
        print(f"   Expected error: {e}")

    # Valid JSON primitives
    print("\n3. ⚠️  Valid JSON primitives:")
    cases = [("null", "null"), ("true", True), ("42", 42), ('"hello"', "hello")]

    for json_str, _ in cases:
        event = BaseReceivedEvent(json_str)
        print(f"   {json_str} -> {event.data} ({type(event.data).__name__})")

    # Invalid JSON
    print("\n4. ❌ Invalid JSON:")
    invalid_cases = [
        "invalid json",
        '{"missing": quote}',
        '{"trailing": "comma",}',
        "",
        "{incomplete",
    ]

    for invalid_json in invalid_cases:
        event = BaseReceivedEvent(invalid_json)
        print(f"   '{invalid_json}' -> data is None: {event.data is None}")

    # Empty dictionary
    print("\n5. 📭 Empty dictionary:")
    event_empty = BaseReceivedEvent("{}")
    print(f"   Data: {event_empty.data}")
    print(f"   Is dict: {isinstance(event_empty.data, dict)}")
    try:
        _ = event_empty.missing_key
    except KeyError as e:
        print(f"   Missing key error: {e}")

    # Mixed data types in nested structure
    print("\n6. 🔄 Mixed data types:")
    mixed_data = {
        "string": "text",
        "number": 42,
        "float": 3.14159,
        "boolean": True,
        "null_value": None,
        "array": [1, 2, 3],
        "nested": {"inner_string": "nested text", "inner_number": 100},
    }

    event_mixed = BaseReceivedEvent(mixed_data)
    print(f"   String: {event_mixed.string}")
    print(f"   Number: {event_mixed.number}")
    print(f"   Float: {event_mixed.float}")
    print(f"   Boolean: {event_mixed.boolean}")
    print(f"   Null: {event_mixed.null_value}")
    print(f"   Array: {event_mixed.array}")
    print(f"   Nested string: {event_mixed.nested.inner_string}")
    print(f"   Nested number: {event_mixed.nested.inner_number}")


def demonstrate_real_world_event():
    """Show a realistic event message from a microservices system."""
    print("\n🌍 Real-World Event Example")
    print("=" * 40)

    # Realistic event with metadata (like BunnyStream generates)
    real_event = {
        "_meta_": {
            "hostname": "order-service-01",
            "timestamp": "2025-06-25 14:03:45",
            "host_ip_address": "10.0.1.50",
            "host_os_info": {
                "system": "Linux",
                "release": "5.4.0",
                "machine": "x86_64",
            },
            "bunnystream_version": "1.0.0",
        },
        "event_type": "order.created",
        "order_id": "ORD-2025-001234",
        "customer_id": "CUST-789012",
        "created_at": "2025-06-25T14:03:45.123Z",
        "order_details": {
            "currency": "USD",
            "subtotal": 149.98,
            "tax": 12.00,
            "shipping": 9.99,
            "total": 171.97,
            "discount": {"code": "SAVE10", "amount": 15.00},
        },
        "shipping_address": {
            "recipient": "Jane Doe",
            "street": "123 Main Street",
            "city": "Anytown",
            "state": "CA",
            "zip": "90210",
            "country": "USA",
        },
        "items": [
            {
                "sku": "BOOK-001",
                "name": "Python Programming Guide",
                "category": "books",
                "price": 49.99,
                "quantity": 1,
            },
            {
                "sku": "TECH-002",
                "name": "Wireless Earbuds",
                "category": "electronics",
                "price": 99.99,
                "quantity": 1,
            },
        ],
        "status": "pending_payment",
    }

    # Process the event
    event = BaseReceivedEvent(real_event)

    print("📋 Order Summary:")
    print(f"   Order ID: {event.order_id}")
    print(f"   Customer: {event.customer_id}")
    print(f"   Status: {event.status}")
    print(f"   Created: {event.created_at}")

    # Order details
    details = event.order_details
    print("\n💰 Financial Details:")
    print(f"   Subtotal: {details.currency} {details.subtotal}")
    print(f"   Tax: {details.currency} {details.tax}")
    print(f"   Shipping: {details.currency} {details.shipping}")

    # Discount handling
    if hasattr(details, "discount"):
        discount = details.discount
        print(f"   Discount ({discount.code}): -{details.currency} {discount.amount}")

    print(f"   Total: {details.currency} {details.total}")

    # Shipping
    shipping = event.shipping_address
    print("\n🚚 Shipping to:")
    print(f"   {shipping.recipient}")
    print(f"   {shipping.street}")
    print(f"   {shipping.city}, {shipping.state} {shipping.zip}")
    print(f"   {shipping.country}")

    # Items
    print(f"\n📦 Items ({len(event.items)} total):")
    for item in event.items:
        print(f"   • {item['name']} ({item['sku']})")
        print(f"     {details.currency} {item['price']} x{item['quantity']}")

    # Metadata (using dictionary access to avoid protected member warning)
    if event.data and "_meta_" in event.data:
        meta_data = event.data["_meta_"]
        print("\n🔍 Event Metadata:")
        print(f"   Generated by: {meta_data['hostname']}")
        print(f"   Timestamp: {meta_data['timestamp']}")
        print(f"   BunnyStream v{meta_data['bunnystream_version']}")

        os_info = meta_data["host_os_info"]
        print(f"   OS: {os_info['system']} {os_info['release']} ({os_info['machine']})")


def main():
    """Run all demonstrations."""
    print("🐰 BunnyStream BaseReceivedEvent Standalone Demo")
    print("=" * 60)
    print("This demo shows BaseReceivedEvent functionality without")
    print("requiring a running RabbitMQ instance.\n")

    demonstrate_basic_usage()
    demonstrate_nested_access()
    demonstrate_edge_cases()
    demonstrate_real_world_event()

    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\nKey takeaways:")
    print("• Use event.field_name for clean attribute access")
    print("• Use event['field_name'] for dictionary-style access")
    print("• Nested dicts become DataObject instances automatically")
    print("• Invalid JSON is handled gracefully (data becomes None)")
    print("• Arrays and primitives remain as their original types")
    print("\nFor a full producer/consumer demo, see received_events_demo.py")
    print("(requires running RabbitMQ instance)")


if __name__ == "__main__":
    main()
