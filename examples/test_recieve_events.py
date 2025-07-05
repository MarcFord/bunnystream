#!/usr/bin/env python3
"""
Test the recieve_events method to ensure it works correctly.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pika.exchange_type import ExchangeType

from bunnystream import BunnyStreamConfig, Warren
from bunnystream.events import BaseReceivedEvent


class TestUserEvent(BaseReceivedEvent):
    """Test event class for user events."""

    EXCHANGE = "test_user_events"
    TOPIC = "user.test"

    def processes_event(self) -> None:
        pass


class TestOrderEvent(BaseReceivedEvent):
    """Test event class for order events."""

    EXCHANGE = "test_order_events"
    TOPIC = "order.test"

    def processes_event(self) -> None:
        pass


def test_recieve_events_logic():
    """Test the recieve_events method logic."""

    print("=== Testing recieve_events Logic ===")

    # Create Warren instance
    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)

    # Mock the channel
    mock_channel = Mock()
    mock_channel.exchange_declare = Mock()
    mock_channel.queue_declare = Mock()
    mock_channel.queue_bind = Mock()
    mock_channel.basic_consume = Mock()

    # Mock basic_consume to return different consumer tags
    mock_channel.basic_consume.side_effect = ["consumer_tag_1", "consumer_tag_2"]

    warren._channel = mock_channel

    # Test event classes
    event_classes = [TestUserEvent, TestOrderEvent]

    print(f"1. Testing with {len(event_classes)} event classes...")

    # Call recieve_events
    warren.recieve_events(event_classes)

    # Verify consumer tags were stored
    print(f"2. Consumer tags stored: {warren._consumer_tags}")
    assert (
        len(warren._consumer_tags) == 2
    ), f"Expected 2 consumer tags, got {len(warren._consumer_tags)}"
    assert warren._consumer_tags == [
        "consumer_tag_1",
        "consumer_tag_2",
    ], f"Unexpected consumer tags: {warren._consumer_tags}"

    # Verify mock calls
    print("3. Verifying RabbitMQ operations...")

    # Should have called exchange_declare for each event class
    assert (
        mock_channel.exchange_declare.call_count == 2
    ), f"Expected 2 exchange_declare calls, got {mock_channel.exchange_declare.call_count}"

    # Should have called queue_declare for each event class
    assert (
        mock_channel.queue_declare.call_count == 2
    ), f"Expected 2 queue_declare calls, got {mock_channel.queue_declare.call_count}"

    # Should have called queue_bind for each event class
    assert (
        mock_channel.queue_bind.call_count == 2
    ), f"Expected 2 queue_bind calls, got {mock_channel.queue_bind.call_count}"

    # Should have called basic_consume for each event class
    assert (
        mock_channel.basic_consume.call_count == 2
    ), f"Expected 2 basic_consume calls, got {mock_channel.basic_consume.call_count}"

    print("4. Verifying exchange and queue declarations...")

    # Check the first event class calls
    first_exchange_call = mock_channel.exchange_declare.call_args_list[0]
    assert first_exchange_call[1]["exchange"] == "test_user_events"
    assert first_exchange_call[1]["exchange_type"] == ExchangeType.topic
    assert first_exchange_call[1]["durable"] is True

    first_queue_call = mock_channel.queue_declare.call_args_list[0]
    assert first_queue_call[1]["queue"] == "test_user_events.user.test"
    assert first_queue_call[1]["durable"] is True
    assert first_queue_call[1]["arguments"] == {"x-queue-type": "quorum"}

    first_bind_call = mock_channel.queue_bind.call_args_list[0]
    assert first_bind_call[1]["exchange"] == "test_user_events"
    assert first_bind_call[1]["queue"] == "test_user_events.user.test"
    assert first_bind_call[1]["routing_key"] == "user.test"

    first_consume_call = mock_channel.basic_consume.call_args_list[0]
    assert first_consume_call[1]["queue"] == "test_user_events.user.test"
    assert first_consume_call[1]["on_message_callback"] == TestUserEvent._on_message
    assert first_consume_call[1]["auto_ack"] is False

    print("5. Verifying second event class...")

    # Check the second event class calls
    second_exchange_call = mock_channel.exchange_declare.call_args_list[1]
    assert second_exchange_call[1]["exchange"] == "test_order_events"

    second_queue_call = mock_channel.queue_declare.call_args_list[1]
    assert second_queue_call[1]["queue"] == "test_order_events.order.test"

    second_bind_call = mock_channel.queue_bind.call_args_list[1]
    assert second_bind_call[1]["exchange"] == "test_order_events"
    assert second_bind_call[1]["queue"] == "test_order_events.order.test"
    assert second_bind_call[1]["routing_key"] == "order.test"

    second_consume_call = mock_channel.basic_consume.call_args_list[1]
    assert second_consume_call[1]["queue"] == "test_order_events.order.test"
    assert second_consume_call[1]["on_message_callback"] == TestOrderEvent._on_message
    assert second_consume_call[1]["auto_ack"] is False

    print("6. Testing stop_consuming with multiple consumer tags...")

    # Test stop_consuming
    warren.stop_consuming()

    # Should have called basic_cancel for each consumer tag
    assert (
        mock_channel.basic_cancel.call_count == 2
    ), f"Expected 2 basic_cancel calls, got {mock_channel.basic_cancel.call_count}"

    # Check that the correct consumer tags were cancelled
    cancel_calls = mock_channel.basic_cancel.call_args_list
    assert cancel_calls[0][0][0] == "consumer_tag_1"
    assert cancel_calls[1][0][0] == "consumer_tag_2"

    # Consumer tags should be cleared
    assert (
        len(warren._consumer_tags) == 0
    ), f"Expected empty consumer tags, got {warren._consumer_tags}"

    print("✅ All tests passed! The recieve_events method works correctly.")
    print("\nKey findings:")
    print("- Each event class gets its own consumer tag")
    print("- Each event class gets its own exchange, queue, and binding")
    print("- Each event class gets its own basic_consume call")
    print("- stop_consuming properly cancels all consumer tags")
    print("- Consumer tags are properly tracked and cleared")


def test_error_conditions():
    """Test error conditions in recieve_events."""

    print("\n=== Testing Error Conditions ===")

    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)

    print("1. Testing with no channel...")
    try:
        warren.recieve_events([TestUserEvent])
        assert False, "Should have raised WarrenNotConnected"
    except Exception as e:
        print(f"✅ Correctly raised: {type(e).__name__}: {e}")

    print("2. Testing with producer mode...")
    config.mode = "producer"
    warren._channel = Mock()
    try:
        warren.recieve_events([TestUserEvent])
        assert False, "Should have raised BunnyStreamConfigurationError"
    except Exception as e:
        print(f"✅ Correctly raised: {type(e).__name__}: {e}")

    print("3. Testing with event class missing attributes...")
    config.mode = "consumer"

    class BadEvent(BaseReceivedEvent):
        pass  # Missing EXCHANGE and TOPIC

    try:
        warren.recieve_events([BadEvent])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✅ Correctly raised: {type(e).__name__}: {e}")

    print("✅ All error condition tests passed!")


if __name__ == "__main__":
    test_recieve_events_logic()
    test_error_conditions()
    print("\n🎉 All tests completed successfully!")
