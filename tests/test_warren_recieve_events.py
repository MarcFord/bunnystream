"""
Tests for Warren.recieve_events method.

This module contains comprehensive tests for the recieve_events functionality,
including unit tests, integration tests, and error condition tests.
"""

from unittest.mock import Mock, call, patch

import pytest
from pika.exchange_type import ExchangeType

from bunnystream import BunnyStreamConfig, Warren
from bunnystream.events import BaseReceivedEvent
from bunnystream.exceptions import (
    BunnyStreamConfigurationError,
    WarrenNotConnected,
)


class MockUserEvent(BaseReceivedEvent):
    """Mock user event for testing."""

    EXCHANGE = "test_user_events"
    TOPIC = "user.action"
    EXCHANGE_TYPE = ExchangeType.topic

    def processes_event(self) -> None:
        """Mock event processing."""
        pass


class MockOrderEvent(BaseReceivedEvent):
    """Mock order event for testing."""

    EXCHANGE = "test_order_events"
    TOPIC = "order.created"
    EXCHANGE_TYPE = ExchangeType.direct

    def processes_event(self) -> None:
        """Mock event processing."""
        pass


class MockInvalidEvent(BaseReceivedEvent):
    """Mock event with missing attributes for testing error conditions."""

    # Inherits None values for EXCHANGE and TOPIC from BaseReceivedEvent

    def processes_event(self) -> None:
        """Mock event processing."""
        pass


class MockEmptyExchangeEvent(BaseReceivedEvent):
    """Mock event with empty exchange for testing error conditions."""

    EXCHANGE = ""
    TOPIC = "test.topic"

    def processes_event(self) -> None:
        """Mock event processing."""
        pass


class TestReceiveEventsBasic:
    """Basic functionality tests for recieve_events method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)
        self.mock_channel = Mock()
        self.warren._channel = self.mock_channel

        # Mock basic_consume to return different consumer tags
        self.mock_channel.basic_consume.side_effect = [
            "consumer_tag_1",
            "consumer_tag_2",
            "consumer_tag_3",
        ]

    def test_single_event_class(self):
        """Test recieve_events with a single event class."""
        event_classes = [MockUserEvent]

        self.warren.recieve_events(event_classes)

        # Verify consumer tag was stored
        assert len(self.warren._consumer_tags) == 1
        assert self.warren._consumer_tags[0] == "consumer_tag_1"

        # Verify exchange declaration
        self.mock_channel.exchange_declare.assert_called_once_with(
            exchange="test_user_events",
            exchange_type=ExchangeType.topic,
            durable=True,
        )

        # Verify queue declaration
        self.mock_channel.queue_declare.assert_called_once_with(
            queue="test_user_events.user.action",
            durable=True,
            arguments={"x-queue-type": "quorum"},
        )

        # Verify queue binding
        self.mock_channel.queue_bind.assert_called_once_with(
            exchange="test_user_events",
            queue="test_user_events.user.action",
            routing_key="user.action",
        )

        # Verify consumer setup
        self.mock_channel.basic_consume.assert_called_once_with(
            queue="test_user_events.user.action",
            on_message_callback=MockUserEvent._on_message,
            auto_ack=False,
        )

    def test_multiple_event_classes(self):
        """Test recieve_events with multiple event classes."""
        event_classes = [MockUserEvent, MockOrderEvent]

        self.warren.recieve_events(event_classes)

        # Verify consumer tags were stored
        assert len(self.warren._consumer_tags) == 2
        assert self.warren._consumer_tags == ["consumer_tag_1", "consumer_tag_2"]

        # Verify all exchanges were declared
        assert self.mock_channel.exchange_declare.call_count == 2
        exchange_calls = self.mock_channel.exchange_declare.call_args_list

        assert exchange_calls[0] == call(
            exchange="test_user_events",
            exchange_type=ExchangeType.topic,
            durable=True,
        )
        assert exchange_calls[1] == call(
            exchange="test_order_events",
            exchange_type=ExchangeType.direct,
            durable=True,
        )

        # Verify all queues were declared
        assert self.mock_channel.queue_declare.call_count == 2
        queue_calls = self.mock_channel.queue_declare.call_args_list

        assert queue_calls[0] == call(
            queue="test_user_events.user.action",
            durable=True,
            arguments={"x-queue-type": "quorum"},
        )
        assert queue_calls[1] == call(
            queue="test_order_events.order.created",
            durable=True,
            arguments={"x-queue-type": "quorum"},
        )

        # Verify all bindings were created
        assert self.mock_channel.queue_bind.call_count == 2
        bind_calls = self.mock_channel.queue_bind.call_args_list

        assert bind_calls[0] == call(
            exchange="test_user_events",
            queue="test_user_events.user.action",
            routing_key="user.action",
        )
        assert bind_calls[1] == call(
            exchange="test_order_events",
            queue="test_order_events.order.created",
            routing_key="order.created",
        )

        # Verify all consumers were set up
        assert self.mock_channel.basic_consume.call_count == 2
        consume_calls = self.mock_channel.basic_consume.call_args_list

        assert consume_calls[0] == call(
            queue="test_user_events.user.action",
            on_message_callback=MockUserEvent._on_message,
            auto_ack=False,
        )
        assert consume_calls[1] == call(
            queue="test_order_events.order.created",
            on_message_callback=MockOrderEvent._on_message,
            auto_ack=False,
        )

    def test_empty_event_list(self):
        """Test recieve_events with empty event list."""
        self.warren.recieve_events([])

        # Verify no operations were performed
        assert len(self.warren._consumer_tags) == 0
        self.mock_channel.exchange_declare.assert_not_called()
        self.mock_channel.queue_declare.assert_not_called()
        self.mock_channel.queue_bind.assert_not_called()
        self.mock_channel.basic_consume.assert_not_called()

    def test_default_exchange_type(self):
        """Test that default exchange type is used when not specified."""

        class DefaultExchangeEvent(BaseReceivedEvent):
            EXCHANGE = "test_default"
            TOPIC = "test.topic"

            def processes_event(self) -> None:
                pass

        self.warren.recieve_events([DefaultExchangeEvent])

        # Should use default topic exchange type
        self.mock_channel.exchange_declare.assert_called_once_with(
            exchange="test_default",
            exchange_type=ExchangeType.topic,
            durable=True,
        )


class TestReceiveEventsErrorConditions:
    """Error condition tests for recieve_events method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)

    def test_no_channel_available(self):
        """Test error when no channel is available."""
        with pytest.raises(
            WarrenNotConnected, match="Cannot start consuming, channel not available"
        ):
            self.warren.recieve_events([MockUserEvent])

    def test_producer_mode_error(self):
        """Test error when Warren is in producer mode."""
        self.config.mode = "producer"
        self.warren._channel = Mock()

        with pytest.raises(
            BunnyStreamConfigurationError,
            match="Warren must be in 'consumer' mode to start consuming messages",
        ):
            self.warren.recieve_events([MockUserEvent])

    def test_missing_exchange_attribute(self):
        """Test error when event class has None/empty EXCHANGE attribute."""
        self.warren._channel = Mock()

        with pytest.raises(
            ValueError,
            match="Event class MockInvalidEvent must have non-empty EXCHANGE and TOPIC",
        ):
            self.warren.recieve_events([MockInvalidEvent])

    def test_empty_exchange_value(self):
        """Test error when event class has empty EXCHANGE value."""
        self.warren._channel = Mock()

        with pytest.raises(
            ValueError,
            match="Event class MockEmptyExchangeEvent must have non-empty EXCHANGE and TOPIC",
        ):
            self.warren.recieve_events([MockEmptyExchangeEvent])

    def test_none_exchange_value(self):
        """Test error when event class has None EXCHANGE value."""

        class NoneExchangeEvent(BaseReceivedEvent):
            EXCHANGE = None
            TOPIC = "test.topic"

            def processes_event(self) -> None:
                pass

        self.warren._channel = Mock()

        with pytest.raises(
            ValueError,
            match="Event class NoneExchangeEvent must have non-empty EXCHANGE and TOPIC",
        ):
            self.warren.recieve_events([NoneExchangeEvent])


class TestReceiveEventsConsumerManagement:
    """Tests for consumer tag management in recieve_events."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)
        self.mock_channel = Mock()
        self.warren._channel = self.mock_channel

    def test_consumer_tags_tracking(self):
        """Test that consumer tags are properly tracked."""
        consumer_tags = ["tag1", "tag2", "tag3"]
        self.mock_channel.basic_consume.side_effect = consumer_tags

        event_classes = [MockUserEvent, MockOrderEvent]
        self.warren.recieve_events(event_classes)

        # Should have stored first two consumer tags
        assert self.warren._consumer_tags == ["tag1", "tag2"]

    def test_get_consumer_count_with_recieve_events(self):
        """Test get_consumer_count method with recieve_events consumers."""
        self.mock_channel.basic_consume.side_effect = ["tag1", "tag2"]

        # Initially no consumers
        assert self.warren.get_consumer_count() == 0

        # Add event-based consumers
        self.warren.recieve_events([MockUserEvent, MockOrderEvent])
        assert self.warren.get_consumer_count() == 2

        # Add single consumer
        self.warren._consumer_tag = "single_tag"
        assert self.warren.get_consumer_count() == 3

    def test_stop_consuming_with_recieve_events(self):
        """Test stop_consuming method with event-based consumers."""
        consumer_tags = ["tag1", "tag2"]
        self.mock_channel.basic_consume.side_effect = consumer_tags

        # Set up consumers
        self.warren.recieve_events([MockUserEvent, MockOrderEvent])
        self.warren._consumer_tag = "single_tag"

        # Stop consuming
        self.warren.stop_consuming()

        # Verify all consumer tags were cancelled
        cancel_calls = self.mock_channel.basic_cancel.call_args_list
        assert len(cancel_calls) == 3
        assert cancel_calls[0] == call("single_tag")
        assert cancel_calls[1] == call("tag1")
        assert cancel_calls[2] == call("tag2")

        # Verify internal state was cleared
        assert self.warren._consumer_tag is None
        assert len(self.warren._consumer_tags) == 0

    def test_stop_consuming_only_recieve_events(self):
        """Test stop_consuming with only event-based consumers."""
        consumer_tags = ["tag1", "tag2"]
        self.mock_channel.basic_consume.side_effect = consumer_tags

        # Set up only event-based consumers
        self.warren.recieve_events([MockUserEvent, MockOrderEvent])

        # Stop consuming
        self.warren.stop_consuming()

        # Verify only event consumer tags were cancelled
        cancel_calls = self.mock_channel.basic_cancel.call_args_list
        assert len(cancel_calls) == 2
        assert cancel_calls[0] == call("tag1")
        assert cancel_calls[1] == call("tag2")

        # Verify internal state was cleared
        assert len(self.warren._consumer_tags) == 0

    def test_multiple_recieve_events_calls(self):
        """Test multiple calls to recieve_events accumulate consumer tags."""
        consumer_tags = ["tag1", "tag2", "tag3", "tag4"]
        self.mock_channel.basic_consume.side_effect = consumer_tags

        # First call
        self.warren.recieve_events([MockUserEvent])
        assert len(self.warren._consumer_tags) == 1
        assert self.warren._consumer_tags == ["tag1"]

        # Second call
        self.warren.recieve_events([MockOrderEvent])
        assert len(self.warren._consumer_tags) == 2
        assert self.warren._consumer_tags == ["tag1", "tag2"]


class TestReceiveEventsIntegration:
    """Integration tests for recieve_events with real scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)

    @patch("bunnystream.warren.pika.SelectConnection")
    def test_full_lifecycle_simulation(self, mock_connection_class):
        """Test full lifecycle of recieve_events with mocked connection."""
        # Mock the connection and channel
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection_class.return_value = mock_connection

        # Set up the warren
        self.warren.connect()
        self.warren._channel = mock_channel
        mock_channel.basic_consume.side_effect = ["tag1", "tag2"]

        # Test the full flow
        event_classes = [MockUserEvent, MockOrderEvent]
        self.warren.recieve_events(event_classes)

        # Verify setup
        assert len(self.warren._consumer_tags) == 2
        assert self.warren.get_consumer_count() == 2

        # Stop consuming
        self.warren.stop_consuming()
        assert len(self.warren._consumer_tags) == 0
        assert self.warren.get_consumer_count() == 0

    def test_event_class_validation_comprehensive(self):
        """Comprehensive test of event class validation."""
        self.warren._channel = Mock()

        # Valid event classes
        class ValidEvent1(BaseReceivedEvent):
            EXCHANGE = "valid_exchange"
            TOPIC = "valid.topic"

            def processes_event(self) -> None:
                pass

        class ValidEvent2(BaseReceivedEvent):
            EXCHANGE = "another_exchange"
            TOPIC = "another.topic"
            EXCHANGE_TYPE = ExchangeType.fanout

            def processes_event(self) -> None:
                pass

        # Should work fine
        self.warren.recieve_events([ValidEvent1, ValidEvent2])

        # Invalid event classes
        invalid_classes = []

        # Missing EXCHANGE
        class NoExchangeEvent(BaseReceivedEvent):
            TOPIC = "test.topic"

            def processes_event(self) -> None:
                pass

        invalid_classes.append(NoExchangeEvent)

        # Missing TOPIC
        class NoTopicEvent(BaseReceivedEvent):
            EXCHANGE = "test_exchange"

            def processes_event(self) -> None:
                pass

        invalid_classes.append(NoTopicEvent)

        # Test each invalid class
        for invalid_class in invalid_classes:
            with pytest.raises(ValueError):
                self.warren.recieve_events([invalid_class])


class TestReceiveEventsDocumentation:
    """Tests to verify documentation examples work correctly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)
        self.mock_channel = Mock()
        self.warren._channel = self.mock_channel

    def test_documentation_example(self):
        """Test the example from the method documentation."""

        class UserLoginEvent(BaseReceivedEvent):
            EXCHANGE = "user_events"
            TOPIC = "user.login"

            def processes_event(self) -> None:
                print(f"User {self.user_id} logged in")

        class UserLogoutEvent(BaseReceivedEvent):
            EXCHANGE = "user_events"
            TOPIC = "user.logout"

            def processes_event(self) -> None:
                print(f"User {self.user_id} logged out")

        # This should work as documented
        self.mock_channel.basic_consume.side_effect = ["tag1", "tag2"]
        self.warren.recieve_events([UserLoginEvent, UserLogoutEvent])

        # Verify the setup matches documentation expectations
        assert len(self.warren._consumer_tags) == 2
        assert self.mock_channel.exchange_declare.call_count == 2
        assert self.mock_channel.queue_declare.call_count == 2
        assert self.mock_channel.queue_bind.call_count == 2
        assert self.mock_channel.basic_consume.call_count == 2


def test_warren_recieve_events_method_exists():
    """Test that the recieve_events method exists and is callable."""
    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)

    assert hasattr(warren, "recieve_events")
    assert callable(getattr(warren, "recieve_events"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
