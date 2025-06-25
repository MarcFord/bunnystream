"""
Tests for the Warren class.

This module contains unit tests for the Warren class functionality
including connection management, publishing, and consuming.
"""

from unittest.mock import Mock, patch

import pika
import pytest
from pika.exchange_type import ExchangeType

from bunnystream.config import BunnyStreamConfig
from bunnystream.exceptions import (
    BunnyStreamConfigurationError,
    WarrenNotConnected,
)
from bunnystream.subscription import Subscription
from bunnystream.warren import Warren


class TestWarren:
    """Test cases for the Warren class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = BunnyStreamConfig(mode="producer")
        self.warren = Warren(self.config)

    def test_warren_initialization(self):
        """Test Warren initialization with config."""
        assert self.warren._rabbit_connection is None
        assert self.warren._config == self.config
        assert self.warren._channel is None
        assert self.warren._consumer_tag is None
        assert self.warren._consumer_callback is None
        assert self.warren.logger is not None

    def test_config_property_getter(self):
        """Test config property getter."""
        assert self.warren.config == self.config

    def test_config_property_setter_valid(self):
        """Test config property setter with valid config."""
        new_config = BunnyStreamConfig(mode="consumer")
        self.warren.config = new_config
        assert self.warren.config == new_config

    def test_config_property_setter_invalid(self):
        """Test config property setter with invalid config."""
        with pytest.raises(BunnyStreamConfigurationError):
            self.warren.config = "invalid_config"

    def test_bunny_mode_property(self):
        """Test bunny_mode property getter and setter."""
        assert self.warren.bunny_mode == "producer"

        self.warren.bunny_mode = "consumer"
        assert self.warren.bunny_mode == "consumer"

    def test_rabbit_connection_property(self):
        """Test rabbit_connection property."""
        assert self.warren.rabbit_connection is None

        # Mock connection
        mock_connection = Mock()
        self.warren._rabbit_connection = mock_connection
        assert self.warren.rabbit_connection == mock_connection

    @patch("pika.ConnectionParameters")
    def test_connection_parameters(self, mock_conn_params):
        """Test connection_parameters property."""
        mock_conn_params.return_value = Mock()

        # Call the property to trigger the connection parameters creation
        self.warren.connection_parameters

        mock_conn_params.assert_called_once_with(
            host=self.config.rabbit_host,
            port=self.config.rabbit_port,
            virtual_host=self.config.rabbit_vhost,
            credentials=pika.PlainCredentials(
                username=self.config.rabbit_user, password=self.config.rabbit_pass
            ),
            channel_max=self.config.channel_max,
            frame_max=self.config.frame_max,
            heartbeat=self.config.heartbeat,
            blocked_connection_timeout=self.config.blocked_connection_timeout,
            ssl_options=self.config.ssl_options,
            retry_delay=self.config.retry_delay,
            connection_attempts=self.config.connection_attempts,
            tcp_options=self.config.tcp_options,
            locale=self.config.locale,
            socket_timeout=self.config.socket_timeout,
            stack_timeout=self.config.stack_timeout,
        )

    @patch("pika.SelectConnection")
    def test_connect(self, mock_select_connection):
        """Test connect method."""
        mock_connection = Mock()
        mock_select_connection.return_value = mock_connection

        self.warren.connect()

        assert self.warren._rabbit_connection == mock_connection
        mock_select_connection.assert_called_once()

    @patch("pika.SelectConnection")
    def test_connect_already_connected(self, mock_select_connection):
        """Test connect method when already connected."""
        self.warren._rabbit_connection = Mock()

        self.warren.connect()

        mock_select_connection.assert_not_called()

    def test_on_connection_open_producer_mode(self):
        """Test on_connection_open callback for producer mode."""
        mock_connection = Mock()
        self.warren._rabbit_connection = mock_connection

        self.warren.on_connection_open(mock_connection)

        mock_connection.channel.assert_called_once_with(
            on_open_callback=self.warren.on_channel_open
        )

    def test_on_connection_open_consumer_mode(self):
        """Test on_connection_open callback for consumer mode."""
        self.config.mode = "consumer"
        mock_connection = Mock()
        self.warren._rabbit_connection = mock_connection

        self.warren.on_connection_open(mock_connection)

        mock_connection.channel.assert_called_once_with(
            on_open_callback=self.warren.on_channel_open
        )

    def test_on_channel_open_producer_mode(self):
        """Test on_channel_open callback for producer mode."""
        mock_channel = Mock()

        with patch.object(self.warren, "_setup_producer") as mock_setup:
            self.warren.on_channel_open(mock_channel)

        assert self.warren._channel == mock_channel
        mock_setup.assert_called_once()

    def test_on_channel_open_consumer_mode(self):
        """Test on_channel_open callback for consumer mode."""
        self.config.mode = "consumer"
        mock_channel = Mock()

        with patch.object(self.warren, "_setup_consumer") as mock_setup:
            self.warren.on_channel_open(mock_channel)

        assert self.warren._channel == mock_channel
        mock_setup.assert_called_once()

    def test_setup_producer(self):
        """Test _setup_producer method."""
        mock_channel = Mock()
        self.warren._channel = mock_channel

        # Add a subscription for testing
        subscription = Subscription(exchange_name="test_exchange")
        self.config._subscriptions = [subscription]

        self.warren._setup_producer()

        mock_channel.exchange_declare.assert_called_once_with(
            exchange="test_exchange", exchange_type=ExchangeType.topic, durable=True
        )

    def test_setup_producer_no_channel(self):
        """Test _setup_producer when channel is None."""
        # Force channel to be None
        self.warren._channel = None

        with pytest.raises(WarrenNotConnected, match="Channel not available"):
            self.warren._setup_producer()

    def test_setup_consumer(self):
        """Test _setup_consumer method."""
        mock_channel = Mock()
        self.warren._channel = mock_channel
        self.config.mode = "consumer"

        # Add a subscription for testing
        subscription = Subscription(exchange_name="test_exchange", topic="test.topic")
        self.config._subscriptions = [subscription]

        with patch.object(self.warren, "_declare_consumer_resources") as mock_declare:
            self.warren._setup_consumer()

        mock_channel.basic_qos.assert_called_once_with(prefetch_count=self.config.prefetch_count)
        mock_declare.assert_called_once_with(subscription)

    def test_setup_consumer_no_channel(self):
        """Test _setup_consumer when channel is None."""
        # Force channel to be None
        self.warren._channel = None

        with pytest.raises(WarrenNotConnected, match="Channel not available"):
            self.warren._setup_consumer()

    def test_declare_consumer_resources(self):
        """Test _declare_consumer_resources method."""
        mock_channel = Mock()
        self.warren._channel = mock_channel

        subscription = Subscription(exchange_name="test_exchange", topic="test.topic")

        self.warren._declare_consumer_resources(subscription)

        # Check exchange declaration
        mock_channel.exchange_declare.assert_called_once_with(
            exchange="test_exchange", exchange_type=ExchangeType.topic, durable=True
        )

        # Check queue declaration
        expected_queue_name = "test_exchange.test.topic"
        mock_channel.queue_declare.assert_called_once_with(queue=expected_queue_name, durable=True)

        # Check queue binding
        mock_channel.queue_bind.assert_called_once_with(
            exchange="test_exchange",
            queue=expected_queue_name,
            routing_key="test.topic",
        )

    def test_declare_consumer_resources_no_channel(self):
        """Test _declare_consumer_resources when channel is None."""
        # Force channel to be None
        self.warren._channel = None

        subscription = Subscription(
            exchange_name="test_exchange",
            exchange_type=ExchangeType.topic,
            topic="test.topic",
        )

        with pytest.raises(WarrenNotConnected, match="Channel not available"):
            self.warren._declare_consumer_resources(subscription)

    def test_on_connection_error(self):
        """Test on_connection_error callback."""
        mock_connection = Mock()
        error = Exception("Connection failed")

        self.warren.on_connection_error(mock_connection, error)

        assert self.warren._rabbit_connection is None

    def test_on_connection_closed(self):
        """Test on_connection_closed callback."""
        mock_connection = Mock()
        reason = "Connection closed by server"

        self.warren.on_connection_closed(mock_connection, reason)

        assert self.warren._rabbit_connection is None

    def test_publish_success(self):
        """Test successful message publishing."""
        mock_channel = Mock()
        self.warren._channel = mock_channel

        message = '{"test": "data"}'
        exchange = "test_exchange"
        topic = "test.topic"

        self.warren.publish(message, exchange, topic)

        mock_channel.exchange_declare.assert_called_once_with(
            exchange=exchange, exchange_type=ExchangeType.topic, durable=True
        )
        mock_channel.basic_publish.assert_called_once_with(
            exchange=exchange,
            routing_key=topic,
            body=message,
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )

    def test_publish_custom_exchange_type(self):
        """Test publishing with custom exchange type."""
        mock_channel = Mock()
        self.warren._channel = mock_channel

        message = '{"test": "data"}'
        exchange = "test_exchange"
        topic = "test.topic"
        exchange_type = ExchangeType.direct

        self.warren.publish(message, exchange, topic, exchange_type)

        mock_channel.exchange_declare.assert_called_once_with(
            exchange=exchange, exchange_type=exchange_type, durable=True
        )

    def test_publish_no_channel(self):
        """Test publishing when no channel is available."""
        message = '{"test": "data"}'
        exchange = "test_exchange"
        topic = "test.topic"

        with pytest.raises(WarrenNotConnected):
            self.warren.publish(message, exchange, topic)

    def test_start_consuming_success(self):
        """Test successful start consuming."""
        mock_channel = Mock()
        self.warren._channel = mock_channel
        self.config.mode = "consumer"

        # Add subscription
        subscription = Subscription(exchange_name="test_exchange", topic="test.topic")
        self.config._subscriptions = [subscription]

        mock_callback = Mock()
        mock_channel.basic_consume.return_value = "consumer_tag_123"

        self.warren.start_consuming(mock_callback)

        assert self.warren._consumer_callback == mock_callback
        assert self.warren._consumer_tag == "consumer_tag_123"

        mock_channel.basic_consume.assert_called_once_with(
            queue="test_exchange.test.topic",
            on_message_callback=self.warren._on_message,
            auto_ack=False,
        )

    def test_start_consuming_no_channel(self):
        """Test start consuming when no channel is available."""
        mock_callback = Mock()

        with pytest.raises(WarrenNotConnected):
            self.warren.start_consuming(mock_callback)

    def test_start_consuming_wrong_mode(self):
        """Test start consuming in producer mode."""
        mock_channel = Mock()
        self.warren._channel = mock_channel
        mock_callback = Mock()

        with pytest.raises(BunnyStreamConfigurationError):
            self.warren.start_consuming(mock_callback)

    def test_on_message_success(self):
        """Test successful message processing."""
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "delivery_tag_123"
        mock_properties = Mock()
        body = b'{"test": "data"}'

        mock_callback = Mock()
        self.warren._consumer_callback = mock_callback

        self.warren._on_message(mock_channel, mock_method, mock_properties, body)

        mock_callback.assert_called_once_with(mock_channel, mock_method, mock_properties, body)
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_tag_123")

    def test_on_message_callback_exception(self):
        """Test message processing when callback raises exception."""
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "delivery_tag_123"
        mock_properties = Mock()
        body = b'{"test": "data"}'

        mock_callback = Mock(side_effect=Exception("Callback failed"))
        self.warren._consumer_callback = mock_callback

        self.warren._on_message(mock_channel, mock_method, mock_properties, body)

        mock_callback.assert_called_once()
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="delivery_tag_123", requeue=True
        )

    def test_on_message_no_callback(self):
        """Test message processing when no callback is set."""
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "delivery_tag_123"
        mock_properties = Mock()
        body = b'{"test": "data"}'

        self.warren._on_message(mock_channel, mock_method, mock_properties, body)

        mock_channel.basic_ack.assert_called_once_with(delivery_tag="delivery_tag_123")

    def test_stop_consuming(self):
        """Test stop consuming."""
        mock_channel = Mock()
        self.warren._channel = mock_channel
        self.warren._consumer_tag = "consumer_tag_123"

        self.warren.stop_consuming()

        mock_channel.basic_cancel.assert_called_once_with("consumer_tag_123")
        assert self.warren._consumer_tag is None

    def test_stop_consuming_no_channel(self):
        """Test stop consuming when no channel is available."""
        self.warren.stop_consuming()  # Should not raise an exception

    def test_start_io_loop(self):
        """Test start IO loop."""
        mock_connection = Mock()
        mock_ioloop = Mock()
        mock_connection.ioloop = mock_ioloop
        self.warren._rabbit_connection = mock_connection

        self.warren.start_io_loop()

        mock_ioloop.start.assert_called_once()

    def test_start_io_loop_no_connection(self):
        """Test start IO loop when no connection is available."""
        self.warren.start_io_loop()  # Should not raise an exception

    def test_stop_io_loop(self):
        """Test stop IO loop."""
        mock_connection = Mock()
        mock_ioloop = Mock()
        mock_connection.ioloop = mock_ioloop
        self.warren._rabbit_connection = mock_connection

        self.warren.stop_io_loop()

        mock_ioloop.stop.assert_called_once()

    def test_stop_io_loop_no_connection(self):
        """Test stop IO loop when no connection is available."""
        self.warren.stop_io_loop()  # Should not raise an exception

    def test_disconnect(self):
        """Test disconnect method."""
        mock_connection = Mock()
        mock_connection.is_closed = False
        self.warren._rabbit_connection = mock_connection

        self.warren.disconnect()

        mock_connection.close.assert_called_once()

    def test_disconnect_already_closed(self):
        """Test disconnect when connection is already closed."""
        mock_connection = Mock()
        mock_connection.is_closed = True
        self.warren._rabbit_connection = mock_connection

        self.warren.disconnect()

        mock_connection.close.assert_not_called()

    def test_disconnect_no_connection(self):
        """Test disconnect when no connection exists."""
        self.warren.disconnect()  # Should not raise an exception

    def test_on_message_callback_specific_exceptions(self):
        """Test _on_message method with specific exception types."""
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "test_tag"
        mock_method.exchange = "test_exchange"
        mock_method.routing_key = "test.key"
        mock_properties = Mock()
        mock_body = b'{"test": "data"}'

        # Set up consumer callback that raises ValueError
        def callback_with_value_error(channel, method, properties, body):
            raise ValueError("Test value error")

        self.warren._consumer_callback = callback_with_value_error

        # Test ValueError handling
        self.warren._on_message(mock_channel, mock_method, mock_properties, mock_body)

        # Should call basic_nack with requeue=True
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="test_tag", requeue=True)

        # Reset mock
        mock_channel.reset_mock()

        # Test TypeError handling
        def callback_with_type_error(channel, method, properties, body):
            raise TypeError("Test type error")

        self.warren._consumer_callback = callback_with_type_error
        self.warren._on_message(mock_channel, mock_method, mock_properties, mock_body)

        mock_channel.basic_nack.assert_called_once_with(delivery_tag="test_tag", requeue=True)

        # Reset mock
        mock_channel.reset_mock()

        # Test KeyError handling
        def callback_with_key_error(channel, method, properties, body):
            raise KeyError("Test key error")

        self.warren._consumer_callback = callback_with_key_error
        self.warren._on_message(mock_channel, mock_method, mock_properties, mock_body)

        mock_channel.basic_nack.assert_called_once_with(delivery_tag="test_tag", requeue=True)

    def test_on_message_unexpected_exception(self):
        """Test _on_message method with unexpected exception type."""
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = "test_tag"
        mock_method.exchange = "test_exchange"
        mock_method.routing_key = "test.key"
        mock_properties = Mock()
        mock_body = b'{"test": "data"}'

        # Set up consumer callback that raises unexpected exception
        def callback_with_unexpected_error(channel, method, properties, body):
            raise RuntimeError("Unexpected runtime error")

        self.warren._consumer_callback = callback_with_unexpected_error

        # Test unexpected exception handling
        self.warren._on_message(mock_channel, mock_method, mock_properties, mock_body)

        # Should call basic_nack with requeue=True
        mock_channel.basic_nack.assert_called_once_with(delivery_tag="test_tag", requeue=True)
