"""
Tests for the BaseEvent class.

This module contains unit tests for the BaseEvent class functionality
including serialization, publishing, and event firing.
"""

import json
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from pika.exchange_type import ExchangeType

from bunnystream.config import BunnyStreamConfig
from bunnystream.events import BaseEvent
from bunnystream.exceptions import WarrenNotConfigured
from bunnystream.warren import Warren


class EventForTesting(BaseEvent):
    """Event class for testing BaseEvent functionality."""

    TOPIC = "test.topic"
    EXCHANGE = "test_exchange"
    EXCHANGE_TYPE = ExchangeType.direct


class EventWithoutConfigForTesting(BaseEvent):
    """Event class without predefined configuration for testing."""

    pass


class EventForTestingWithBadTopic(BaseEvent):
    """Event class for testing BaseEvent functionality."""

    TOPIC = 1
    EXCHANGE = "test_exchange"
    EXCHANGE_TYPE = ExchangeType.direct


class EventForTestingWithBadExchangeType(BaseEvent):
    """Event class for testing BaseEvent functionality."""

    TOPIC = "test.topic"
    EXCHANGE = "test_exchange"
    EXCHANGE_TYPE = "invalid_exchange_type"  # type: ignore


class TestBaseEvent:
    """Test cases for the BaseEvent class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = BunnyStreamConfig(mode="producer")
        self.warren = Mock(spec=Warren)
        self.warren.config = self.config

    def test_event_initialization(self):
        """Test event initialization with warren and data."""
        data = {"key1": "value1", "key2": 42}
        event = EventForTesting(warren=self.warren, **data)

        assert event._warren == self.warren
        assert event.data == data

    def test_event_initialization_no_data(self):
        """Test event initialization with warren but no data."""
        event = EventForTesting(warren=self.warren)

        assert event._warren == self.warren
        assert event.data == {}

    def test_json_property(self):
        """Test json property returns serialized data."""
        event = EventForTesting(warren=self.warren, test_key="test_value")

        with patch.object(event, "serialize", return_value='{"test": "data"}') as mock_serialize:
            result = event.json

            mock_serialize.assert_called_once()
            assert result == '{"test": "data"}'

    @patch("bunnystream.events.platform.node")
    @patch("bunnystream.events.datetime")
    def test_serialize_with_metadata(self, mock_datetime, mock_platform_node):
        """Test serialize method adds metadata."""
        # Setup mocks
        mock_datetime.now.return_value.strftime.return_value = "2023-06-01 12:00:00"
        mock_platform_node.return_value = "test_hostname"

        event = EventForTesting(warren=self.warren, test_key="test_value")

        with (
            patch.object(event, "_get_host_ip_address", return_value="192.168.1.1"),
            patch.object(event, "_get_os_info", return_value={"system": "Linux"}),
        ):
            result = event.serialize()

            # Parse the JSON to verify structure
            data = json.loads(result)

            assert data["test_key"] == "test_value"
            assert "_meta_" in data
            assert data["_meta_"]["hostname"] == "test_hostname"
            assert data["_meta_"]["timestamp"] == "2023-06-01 12:00:00"
            assert data["_meta_"]["host_ip_address"] == "192.168.1.1"
            assert data["_meta_"]["host_os_in"] == {"system": "Linux"}
            assert "bunnystream_version" in data["_meta_"]

    def test_serialize_with_uuid(self):
        """Test serialize method handles UUID objects."""
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        event = EventForTesting(warren=self.warren, uuid_field=test_uuid)

        with patch.object(event, "__setitem__"):  # Skip metadata setting
            result = event.serialize()

            data = json.loads(result)
            assert data["uuid_field"] == test_uuid.hex

    def test_serialize_runtime_error_handling(self):
        """Test serialize method handles RuntimeError gracefully."""
        event = EventForTesting(warren=self.warren, test_key="test_value")

        with patch(
            "bunnystream.events.platform.node",
            side_effect=RuntimeError("Platform error"),
        ):
            result = event.serialize()

            # Should still return valid JSON without metadata
            data = json.loads(result)
            assert data["test_key"] == "test_value"
            assert "_meta_" not in data

    def test_fire_with_predefined_config(self):
        """Test fire method with predefined TOPIC and EXCHANGE."""
        event = EventForTesting(warren=self.warren, test_key="test_value")

        with patch.object(event, "serialize", return_value='{"test": "data"}'):
            event.fire()

            self.warren.publish.assert_called_once_with(
                topic="test.topic",
                message='{"test": "data"}',
                exchange="test_exchange",
                exchange_type=ExchangeType.direct,
            )

    def test_fire_with_predefined_bad_topic_config(self):
        """Test fire method with predefined TOPIC and EXCHANGE."""
        event = EventForTestingWithBadTopic(warren=self.warren, test_key="test_value")

        with patch.object(event, "serialize", return_value='{"test": "data"}'):
            with pytest.raises(ValueError, match="TOPIC must be a string"):
                event.fire()

    def test_fire_with_predefined_bad_exchange_type_config(self):
        """Test fire method with predefined TOPIC and EXCHANGE."""
        # Setup warren config with subscription mappings
        self.config._subscription_mappings = {
            "bunnystream": {"topic": "dynamic.topic", "type": ExchangeType.topic}
        }

        event = EventForTestingWithBadExchangeType(warren=self.warren, test_key="test_value")

        with patch.object(event, "serialize", return_value='{"test": "data"}'):
            event.fire()
            self.warren.publish.assert_called_once_with(
                topic="dynamic.topic",
                message='{"test": "data"}',
                exchange="bunnystream",
                exchange_type=ExchangeType.topic,
            )

    def test_fire_with_config_from_warren(self):
        """Test fire method gets config from warren when not predefined."""
        # Setup warren config with subscription mappings
        self.config._subscription_mappings = {
            "bunnystream": {"topic": "dynamic.topic", "type": ExchangeType.fanout}
        }

        event = EventWithoutConfigForTesting(warren=self.warren, test_key="test_value")

        with patch.object(event, "serialize", return_value='{"test": "data"}'):
            event.fire()

            # Should use config from warren
            assert event.TOPIC == "dynamic.topic"
            assert event.EXCHANGE == "bunnystream"
            assert event.EXCHANGE_TYPE == ExchangeType.fanout

            self.warren.publish.assert_called_once_with(
                topic="dynamic.topic",
                message='{"test": "data"}',
                exchange="bunnystream",
                exchange_type=ExchangeType.fanout,
            )

    def test_fire_no_warren(self):
        """Test fire method raises exception when warren is None."""
        # Create event with None warren (we need to bypass type checking)
        event = EventForTesting.__new__(EventForTesting)
        event._warren = None  # type: ignore
        event.data = {"test_key": "test_value"}

        with pytest.raises(WarrenNotConfigured):
            event.fire()

    def test_fire_no_config_and_no_subscription(self):
        """Test fire method raises exception when no config available."""
        # Setup warren without subscription mappings and subscriptions
        self.config._subscription_mappings = {}
        self.config._subscriptions = []

        event = EventWithoutConfigForTesting(warren=self.warren, test_key="test_value")

        with pytest.raises(WarrenNotConfigured) as exc_info:
            event.fire()

        assert "No topic is set" in str(exc_info.value)

    def test_getitem(self):
        """Test __getitem__ method."""
        event = EventForTesting(warren=self.warren, test_key="test_value")
        assert event["test_key"] == "test_value"

    def test_setitem_valid_types(self):
        """Test __setitem__ method with valid types."""
        event = EventForTesting(warren=self.warren)

        # Test valid types
        event["string"] = "test"
        event["int"] = 42
        event["float"] = 3.14
        event["bool"] = True
        event["list"] = [1, 2, 3]
        event["dict"] = {"key": "value"}
        event["tuple"] = (1, 2, 3)

        assert event.data["string"] == "test"
        assert event.data["int"] == 42
        assert event.data["float"] == 3.14
        assert event.data["bool"] is True
        assert event.data["list"] == [1, 2, 3]
        assert event.data["dict"] == {"key": "value"}
        assert event.data["tuple"] == (1, 2, 3)

    def test_setitem_invalid_type_converted_to_string(self):
        """Test __setitem__ method converts invalid types to string."""
        event = EventForTesting(warren=self.warren)

        class CustomObject:
            def __str__(self):
                return "custom_object_string"

        custom_obj = CustomObject()
        event["custom"] = custom_obj

        assert event.data["custom"] == "custom_object_string"

    def test_setitem_none_value(self):
        """Test __setitem__ method with None value."""
        event = EventForTesting(warren=self.warren)
        event["none_key"] = None

        assert event.data["none_key"] is None

    @patch("socket.gethostname")
    @patch("socket.gethostbyname")
    def test_get_host_ip_address_success(self, mock_gethostbyname, mock_gethostname):
        """Test _get_host_ip_address method success case."""
        mock_gethostname.return_value = "test_hostname"
        mock_gethostbyname.return_value = "192.168.1.100"

        event = EventForTesting(warren=self.warren)
        result = event._get_host_ip_address()

        assert result == "192.168.1.100"
        mock_gethostname.assert_called_once()
        mock_gethostbyname.assert_called_once_with("test_hostname")

    @patch("socket.gethostname", side_effect=Exception("Network error"))
    def test_get_host_ip_address_exception(self, mock_gethostname):
        """Test _get_host_ip_address method exception handling."""
        event = EventForTesting(warren=self.warren)
        result = event._get_host_ip_address()

        assert result == "127.0.0.1"

    @patch("bunnystream.events.platform.system")
    @patch("bunnystream.events.platform.release")
    @patch("bunnystream.events.platform.version")
    @patch("bunnystream.events.platform.machine")
    @patch("bunnystream.events.platform.processor")
    def test_get_os_info(
        self, mock_processor, mock_machine, mock_version, mock_release, mock_system
    ):
        """Test _get_os_info method."""
        mock_system.return_value = "Linux"
        mock_release.return_value = "5.4.0"
        mock_version.return_value = "#1 SMP"
        mock_machine.return_value = "x86_64"
        mock_processor.return_value = "x86_64"

        event = EventForTesting(warren=self.warren)
        result = event._get_os_info()

        expected = {
            "system": "Linux",
            "release": "5.4.0",
            "version": "#1 SMP",
            "machine": "x86_64",
            "processor": "x86_64",
        }

        assert result == expected

    def test_event_inheritance(self):
        """Test that event classes can be properly inherited."""

        class MyCustomEvent(BaseEvent):
            TOPIC = "custom.topic"
            EXCHANGE = "custom_exchange"

        event = MyCustomEvent(warren=self.warren, custom_data="test")

        assert event.TOPIC == "custom.topic"
        assert event.EXCHANGE == "custom_exchange"
        assert event.data["custom_data"] == "test"

    def test_class_attributes_default_values(self):
        """Test default values of class attributes."""
        assert BaseEvent.TOPIC is None
        assert BaseEvent.EXCHANGE is None
        assert BaseEvent.EXCHANGE_TYPE == ExchangeType.topic

    def test_multiple_events_independent_data(self):
        """Test that multiple event instances have independent data."""
        event1 = EventForTesting(warren=self.warren, key="value1")
        event2 = EventForTesting(warren=self.warren, key="value2")

        assert event1.data["key"] == "value1"
        assert event2.data["key"] == "value2"

        event1["new_key"] = "new_value1"
        assert "new_key" not in event2.data
