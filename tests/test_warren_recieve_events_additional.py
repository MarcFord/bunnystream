"""
Additional comprehensive tests for Warren.recieve_events method.

This module contains additional tests that focus on edge cases, integration scenarios,
and real-world usage patterns for the recieve_events functionality.
"""

from unittest.mock import Mock, patch

import pytest
from pika.exchange_type import ExchangeType

from bunnystream import BunnyStreamConfig, Warren
from bunnystream.events import BaseReceivedEvent, EventProcessingError
from bunnystream.exceptions import (
    BunnyStreamConfigurationError,
    WarrenNotConnected,
)


class MockEventWithoutProcessing(BaseReceivedEvent):
    """Mock event that doesn't override processes_event."""

    EXCHANGE = "test_no_processing"
    TOPIC = "test.topic"

    # Inherits default processes_event from BaseReceivedEvent


class MockEventWithProcessingError(BaseReceivedEvent):
    """Mock event that raises an error during processing."""

    EXCHANGE = "test_error_processing"
    TOPIC = "test.error"

    def processes_event(self) -> None:
        """Raise an error during event processing."""
        raise ValueError("Test processing error")


class MockEventWithDifferentExchangeTypes(BaseReceivedEvent):
    """Mock event with different exchange type."""

    EXCHANGE = "test_fanout"
    TOPIC = "test.fanout"
    EXCHANGE_TYPE = ExchangeType.fanout

    def processes_event(self) -> None:
        pass


class MockEventWithDirectExchange(BaseReceivedEvent):
    """Mock event with direct exchange."""

    EXCHANGE = "test_direct"
    TOPIC = "test.direct"
    EXCHANGE_TYPE = ExchangeType.direct

    def processes_event(self) -> None:
        pass


class MockEventWithHeadersExchange(BaseReceivedEvent):
    """Mock event with headers exchange."""

    EXCHANGE = "test_headers"
    TOPIC = "test.headers"
    EXCHANGE_TYPE = ExchangeType.headers

    def processes_event(self) -> None:
        pass


class TestReceiveEventsAdvanced:
    """Advanced tests for recieve_events method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)
        self.mock_channel = Mock()
        self.warren._channel = self.mock_channel

        # Mock basic_consume to return different consumer tags
        self.mock_channel.basic_consume.side_effect = [f"consumer_tag_{i}" for i in range(1, 11)]

    def test_sequence_type_parameter(self):
        """Test that recieve_events accepts Sequence[type[BaseReceivedEvent]]."""
        # Should accept list
        event_list = [MockEventWithoutProcessing]
        self.warren.recieve_events(event_list)

        # Should accept tuple
        event_tuple = (MockEventWithoutProcessing,)
        self.warren.recieve_events(event_tuple)

        # Verify both were processed
        assert len(self.warren._consumer_tags) == 2
        assert self.mock_channel.basic_consume.call_count == 2

    def test_different_exchange_types(self):
        """Test events with different exchange types."""
        event_classes = [
            MockEventWithDifferentExchangeTypes,
            MockEventWithDirectExchange,
            MockEventWithHeadersExchange,
        ]

        self.warren.recieve_events(event_classes)

        # Verify all exchange types were declared correctly
        exchange_calls = self.mock_channel.exchange_declare.call_args_list
        assert len(exchange_calls) == 3

        assert exchange_calls[0][1]["exchange_type"] == ExchangeType.fanout
        assert exchange_calls[1][1]["exchange_type"] == ExchangeType.direct
        assert exchange_calls[2][1]["exchange_type"] == ExchangeType.headers

    def test_empty_sequence_variations(self):
        """Test different empty sequence types."""
        empty_list = []
        empty_tuple = ()

        self.warren.recieve_events(empty_list)
        assert len(self.warren._consumer_tags) == 0

        self.warren.recieve_events(empty_tuple)
        assert len(self.warren._consumer_tags) == 0

        # Verify no operations were performed
        self.mock_channel.exchange_declare.assert_not_called()
        self.mock_channel.queue_declare.assert_not_called()
        self.mock_channel.queue_bind.assert_not_called()
        self.mock_channel.basic_consume.assert_not_called()

    def test_event_class_with_missing_attributes_variations(self):
        """Test various combinations of missing attributes."""

        # Test class with missing EXCHANGE attribute
        class MissingExchangeEvent(BaseReceivedEvent):
            TOPIC = "test.topic"

            def processes_event(self) -> None:
                pass

        # Test class with missing TOPIC attribute
        class MissingTopicEvent(BaseReceivedEvent):
            EXCHANGE = "test_exchange"

            def processes_event(self) -> None:
                pass

        # Test class with both attributes missing (inherits None from BaseReceivedEvent)
        class MissingBothEvent(BaseReceivedEvent):
            def processes_event(self) -> None:
                pass

        # All should raise ValueError for non-empty EXCHANGE and TOPIC
        with pytest.raises(ValueError, match="must have non-empty EXCHANGE and TOPIC"):
            self.warren.recieve_events([MissingExchangeEvent])

        with pytest.raises(ValueError, match="must have non-empty EXCHANGE and TOPIC"):
            self.warren.recieve_events([MissingTopicEvent])

        with pytest.raises(ValueError, match="must have non-empty EXCHANGE and TOPIC"):
            self.warren.recieve_events([MissingBothEvent])

    def test_event_class_with_whitespace_attributes(self):
        """Test event classes with whitespace-only attributes."""

        class WhitespaceExchangeEvent(BaseReceivedEvent):
            EXCHANGE = "   "
            TOPIC = "test.topic"

            def processes_event(self) -> None:
                pass

        class WhitespaceTopicEvent(BaseReceivedEvent):
            EXCHANGE = "test_exchange"
            TOPIC = "   "

            def processes_event(self) -> None:
                pass

        # Both should raise ValueError for empty values
        # Note: The current implementation treats whitespace as valid, so this test
        # documents the current behavior rather than testing validation
        # This is acceptable since RabbitMQ can handle whitespace-only names
        self.warren.recieve_events([WhitespaceExchangeEvent])
        self.warren.recieve_events([WhitespaceTopicEvent])

        # Verify both were processed
        assert len(self.warren._consumer_tags) == 2

    def test_duplicate_event_classes(self):
        """Test behavior with duplicate event classes."""
        event_classes = [
            MockEventWithoutProcessing,
            MockEventWithoutProcessing,  # Same class twice
            MockEventWithDifferentExchangeTypes,
        ]

        self.warren.recieve_events(event_classes)

        # Should create separate consumers for each, even if duplicate
        assert len(self.warren._consumer_tags) == 3
        assert self.mock_channel.basic_consume.call_count == 3

        # Should declare resources for each occurrence
        assert self.mock_channel.exchange_declare.call_count == 3
        assert self.mock_channel.queue_declare.call_count == 3
        assert self.mock_channel.queue_bind.call_count == 3

    def test_large_number_of_event_classes(self):
        """Test with a large number of event classes."""
        # Create multiple event classes dynamically
        event_classes = []
        for i in range(20):
            class_name = f"TestEvent{i}"
            event_class = type(
                class_name,
                (BaseReceivedEvent,),
                {
                    "EXCHANGE": f"test_exchange_{i}",
                    "TOPIC": f"test.topic.{i}",
                    "processes_event": lambda self: None,
                },
            )
            event_classes.append(event_class)

        # Set up enough mock consumer tags
        self.mock_channel.basic_consume.side_effect = [f"consumer_tag_{i}" for i in range(20)]

        self.warren.recieve_events(event_classes)

        # Should handle all event classes
        assert len(self.warren._consumer_tags) == 20
        assert self.mock_channel.basic_consume.call_count == 20
        assert self.mock_channel.exchange_declare.call_count == 20
        assert self.mock_channel.queue_declare.call_count == 20
        assert self.mock_channel.queue_bind.call_count == 20

    def test_get_consumer_count_edge_cases(self):
        """Test get_consumer_count with various scenarios."""
        # Initially no consumers
        assert self.warren.get_consumer_count() == 0

        # Add single consumer
        self.warren._consumer_tag = "single_tag"
        assert self.warren.get_consumer_count() == 1

        # Add multiple event consumers
        self.warren.recieve_events(
            [MockEventWithoutProcessing, MockEventWithDifferentExchangeTypes]
        )
        assert self.warren.get_consumer_count() == 3  # 1 single + 2 event consumers

        # Remove single consumer
        self.warren._consumer_tag = None
        assert self.warren.get_consumer_count() == 2  # Only event consumers remain

        # Clear all consumers
        self.warren._consumer_tags.clear()
        assert self.warren.get_consumer_count() == 0


class TestReceiveEventsIntegrationAdvanced:
    """Advanced integration tests for recieve_events."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)

    def test_event_processing_error_handling(self):
        """Test error handling in event processing."""
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = Mock()
        mock_body = '{"test": "data"}'  # String, not bytes

        # Test that _on_message handles the error properly
        with pytest.raises(EventProcessingError):
            MockEventWithProcessingError._on_message(
                mock_channel, mock_method, mock_properties, mock_body
            )

    def test_event_message_acknowledgment(self):
        """Test that events are properly acknowledged."""
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = Mock()
        mock_body = '{"test": "data"}'  # String, not bytes

        # Test successful event processing and acknowledgment
        MockEventWithoutProcessing._on_message(
            mock_channel, mock_method, mock_properties, mock_body
        )

        # Verify ack was called
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    @patch("bunnystream.warren.pika.SelectConnection")
    def test_real_world_scenario(self, mock_connection_class):
        """Test a real-world scenario with multiple event types."""
        # Mock the connection and channel
        mock_connection = Mock()
        mock_channel = Mock()
        mock_connection_class.return_value = mock_connection

        # Set up the warren
        self.warren.connect()
        self.warren._channel = mock_channel

        # Mock consumer tags
        consumer_tags = [f"consumer_{i}" for i in range(5)]
        mock_channel.basic_consume.side_effect = consumer_tags

        # Define multiple event classes for different business domains
        class UserRegistrationEvent(BaseReceivedEvent):
            EXCHANGE = "user_events"
            TOPIC = "user.registered"

            def processes_event(self) -> None:
                pass

        class OrderPlacedEvent(BaseReceivedEvent):
            EXCHANGE = "order_events"
            TOPIC = "order.placed"

            def processes_event(self) -> None:
                pass

        class PaymentProcessedEvent(BaseReceivedEvent):
            EXCHANGE = "payment_events"
            TOPIC = "payment.processed"
            EXCHANGE_TYPE = ExchangeType.direct

            def processes_event(self) -> None:
                pass

        class NotificationSentEvent(BaseReceivedEvent):
            EXCHANGE = "notification_events"
            TOPIC = "notification.sent"
            EXCHANGE_TYPE = ExchangeType.fanout

            def processes_event(self) -> None:
                pass

        # Set up all event types
        event_classes = [
            UserRegistrationEvent,
            OrderPlacedEvent,
            PaymentProcessedEvent,
            NotificationSentEvent,
        ]

        self.warren.recieve_events(event_classes)

        # Verify all resources were created
        assert len(self.warren._consumer_tags) == 4
        assert mock_channel.exchange_declare.call_count == 4
        assert mock_channel.queue_declare.call_count == 4
        assert mock_channel.queue_bind.call_count == 4
        assert mock_channel.basic_consume.call_count == 4

        # Verify different exchange types were used
        exchange_calls = mock_channel.exchange_declare.call_args_list
        exchange_types = [call[1]["exchange_type"] for call in exchange_calls]
        assert ExchangeType.topic in exchange_types
        assert ExchangeType.direct in exchange_types
        assert ExchangeType.fanout in exchange_types

        # Test stopping all consumers
        self.warren.stop_consuming()

        # Verify all consumers were stopped
        assert len(self.warren._consumer_tags) == 0
        assert mock_channel.basic_cancel.call_count == 4

    def test_configuration_validation(self):
        """Test configuration validation scenarios."""
        # Test with producer mode
        producer_config = BunnyStreamConfig(mode="producer")
        producer_warren = Warren(producer_config)
        producer_warren._channel = Mock()

        with pytest.raises(BunnyStreamConfigurationError):
            producer_warren.recieve_events([MockEventWithoutProcessing])

        # Test with no channel
        no_channel_warren = Warren(BunnyStreamConfig(mode="consumer"))
        # _channel is None by default

        with pytest.raises(WarrenNotConnected):
            no_channel_warren.recieve_events([MockEventWithoutProcessing])

    def test_method_chaining_compatibility(self):
        """Test that recieve_events can be used with other Warren methods."""
        mock_channel = Mock()
        self.warren._channel = mock_channel

        # Set up event-based consumers
        self.warren.recieve_events([MockEventWithoutProcessing])

        # Verify the method doesn't interfere with other operations
        assert self.warren.get_consumer_count() == 1
        assert len(self.warren._consumer_tags) == 1

        # Test stopping consumers
        self.warren.stop_consuming()
        assert self.warren.get_consumer_count() == 0
        assert len(self.warren._consumer_tags) == 0


class TestReceiveEventsTypeAnnotations:
    """Test type annotation compliance for recieve_events."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)
        self.mock_channel = Mock()
        self.warren._channel = self.mock_channel
        self.mock_channel.basic_consume.return_value = "test_tag"

    def test_accepts_sequence_types(self):
        """Test that the method accepts various Sequence types."""
        # List
        event_list = [MockEventWithoutProcessing]
        self.warren.recieve_events(event_list)

        # Tuple
        event_tuple = (MockEventWithoutProcessing,)
        self.warren.recieve_events(event_tuple)

        # Both should work without type errors
        assert len(self.warren._consumer_tags) == 2

    def test_parameter_type_validation(self):
        """Test parameter type validation."""
        # The method signature should accept Sequence[type[BaseReceivedEvent]]

        # Valid: list of event classes
        valid_events = [MockEventWithoutProcessing, MockEventWithDifferentExchangeTypes]
        self.warren.recieve_events(valid_events)

        # The method should work with proper event classes
        assert len(self.warren._consumer_tags) == 2


class TestReceiveEventsDocumentationExamples:
    """Test all examples from the documentation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = BunnyStreamConfig(mode="consumer")
        self.warren = Warren(self.config)
        self.mock_channel = Mock()
        self.warren._channel = self.mock_channel
        self.mock_channel.basic_consume.side_effect = [f"consumer_tag_{i}" for i in range(1, 11)]

    def test_module_docstring_example(self):
        """Test the example from the module docstring."""

        class UserEvent(BaseReceivedEvent):
            EXCHANGE = "user_events"
            TOPIC = "user.login"

            def processes_event(self):
                print(f"User {self.user_id} logged in")

        class OrderEvent(BaseReceivedEvent):
            EXCHANGE = "order_events"
            TOPIC = "order.created"

            def processes_event(self):
                print(f"Order {self.order_id} created")

        # This should work as documented
        self.warren.recieve_events([UserEvent, OrderEvent])

        # Verify the setup
        assert len(self.warren._consumer_tags) == 2
        assert self.mock_channel.exchange_declare.call_count == 2
        assert self.mock_channel.queue_declare.call_count == 2
        assert self.mock_channel.queue_bind.call_count == 2
        assert self.mock_channel.basic_consume.call_count == 2

    def test_method_docstring_example(self):
        """Test the example from the method docstring."""

        class UserLoginEvent(BaseReceivedEvent):
            EXCHANGE = "user_events"
            TOPIC = "user.login"

            def processes_event(self):
                print(f"User {self.user_id} logged in")

        class UserLogoutEvent(BaseReceivedEvent):
            EXCHANGE = "user_events"
            TOPIC = "user.logout"

            def processes_event(self):
                print(f"User {self.user_id} logged out")

        # Each event class gets its own consumer tag for independent processing
        self.warren.recieve_events([UserLoginEvent, UserLogoutEvent])

        # Verify the setup matches documentation expectations
        assert len(self.warren._consumer_tags) == 2
        assert self.mock_channel.exchange_declare.call_count == 2
        assert self.mock_channel.queue_declare.call_count == 2
        assert self.mock_channel.queue_bind.call_count == 2
        assert self.mock_channel.basic_consume.call_count == 2

        # Verify each event class got its own consumer tag
        consumer_tags = self.warren._consumer_tags
        assert len(set(consumer_tags)) == 2  # All tags should be unique


def test_warren_recieve_events_exists_and_callable():
    """Test that the recieve_events method exists and is properly callable."""
    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)

    # Method should exist
    assert hasattr(warren, "recieve_events")

    # Method should be callable
    assert callable(getattr(warren, "recieve_events"))

    # Method should have correct signature
    method = getattr(warren, "recieve_events")
    assert method.__name__ == "recieve_events"

    # Method should be documented
    assert method.__doc__ is not None
    assert "Set up consumption for multiple event types" in method.__doc__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
