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
from bunnystream.events import BaseEvent, BaseReceivedEvent, DataObject
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


class TestBaseReceivedEvent:
    """Test suite for BaseReceivedEvent class."""

    def test_init_with_dict_data(self):
        """Test BaseReceivedEvent initialization with dictionary data."""
        test_data = {"key": "value", "number": 42}
        event = BaseReceivedEvent(test_data)

        assert event.data == test_data
        assert event._raw_data == json.dumps(test_data)
        assert event.EXCHANGE is None
        assert event.EXCHANGE_TYPE == ExchangeType.topic

    def test_init_with_valid_json_string(self):
        """Test BaseReceivedEvent initialization with valid JSON string."""
        test_data = {"key": "value", "number": 42}
        json_string = json.dumps(test_data)
        event = BaseReceivedEvent(json_string)

        assert event.data == test_data
        assert event._raw_data == json_string

    def test_init_with_invalid_json_string(self):
        """Test BaseReceivedEvent initialization with invalid JSON string."""
        invalid_json = "invalid json string"
        event = BaseReceivedEvent(invalid_json)

        assert event.data is None
        assert event._raw_data == invalid_json

    def test_init_with_empty_json_string(self):
        """Test BaseReceivedEvent initialization with empty JSON string."""
        empty_json = "{}"
        event = BaseReceivedEvent(empty_json)

        assert event.data == {}
        assert event._raw_data == empty_json

    def test_init_with_invalid_data_type(self):
        """Test BaseReceivedEvent initialization with invalid data type."""
        with pytest.raises(TypeError, match="Data must be a dictionary or a JSON string."):
            BaseReceivedEvent(123)  # type: ignore

        with pytest.raises(TypeError, match="Data must be a dictionary or a JSON string."):
            BaseReceivedEvent([1, 2, 3])  # type: ignore

        with pytest.raises(TypeError, match="Data must be a dictionary or a JSON string."):
            BaseReceivedEvent(None)  # type: ignore

    def test_getitem_with_valid_key(self):
        """Test __getitem__ with valid keys."""
        test_data = {"key1": "value1", "key2": 42, "key3": True}
        event = BaseReceivedEvent(test_data)

        assert event["key1"] == "value1"
        assert event["key2"] == 42
        assert event["key3"] is True

    def test_getitem_with_invalid_key(self):
        """Test __getitem__ with invalid keys."""
        test_data = {"key": "value"}
        event = BaseReceivedEvent(test_data)

        with pytest.raises(KeyError, match="Key 'nonexistent' not found in event data."):
            event["nonexistent"]

    def test_getitem_with_nested_dict(self):
        """Test __getitem__ returns DataObject for nested dictionaries."""
        test_data = {
            "user": {
                "name": "John",
                "age": 30,
                "address": {"street": "123 Main St", "city": "Anytown"},
            }
        }
        event = BaseReceivedEvent(test_data)

        user_obj = event["user"]
        assert isinstance(user_obj, DataObject)
        assert user_obj["name"] == "John"
        assert user_obj["age"] == 30

        address_obj = user_obj["address"]
        assert isinstance(address_obj, DataObject)
        assert address_obj["street"] == "123 Main St"
        assert address_obj["city"] == "Anytown"

    def test_getitem_with_no_data(self):
        """Test __getitem__ when data is None or empty."""
        event = BaseReceivedEvent("invalid json")

        with pytest.raises(TypeError, match="Event data is not a dictionary or is empty."):
            event["any_key"]

    def test_getattr_access(self):
        """Test attribute-like access to event data."""
        test_data = {"username": "john_doe", "email": "john@example.com"}
        event = BaseReceivedEvent(test_data)

        assert event.username == "john_doe"
        assert event.email == "john@example.com"

    def test_getattr_with_nested_data(self):
        """Test attribute-like access with nested data."""
        test_data = {"user": {"profile": {"name": "John Doe"}}}
        event = BaseReceivedEvent(test_data)

        assert isinstance(event.user, DataObject)
        assert isinstance(event.user.profile, DataObject)
        assert event.user.profile.name == "John Doe"

    def test_complex_json_parsing(self):
        """Test complex JSON data parsing."""
        complex_data = {
            "id": "12345",
            "timestamp": "2023-12-01T10:30:00Z",
            "event_type": "user_action",
            "payload": {
                "action": "login",
                "user_id": 67890,
                "metadata": {
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0",
                    "session_id": "abc123",
                },
            },
            "tags": ["important", "security"],
        }
        json_string = json.dumps(complex_data)
        event = BaseReceivedEvent(json_string)

        assert event.id == "12345"
        assert event.event_type == "user_action"
        assert event.tags == ["important", "security"]

        payload = event.payload
        assert isinstance(payload, DataObject)
        assert payload.action == "login"
        assert payload.user_id == 67890

        metadata = payload.metadata
        assert isinstance(metadata, DataObject)
        assert metadata.ip_address == "192.168.1.1"
        assert metadata.user_agent == "Mozilla/5.0"

    def test_json_with_special_characters(self):
        """Test JSON parsing with special characters."""
        test_data = {
            "message": "Hello, 世界! 🌍",
            "unicode": "café résumé naïve",
            "symbols": "!@#$%^&*()_+{}|:<>?",
        }
        json_string = json.dumps(test_data)
        event = BaseReceivedEvent(json_string)

        assert event.message == "Hello, 世界! 🌍"
        assert event.unicode == "café résumé naïve"
        assert event.symbols == "!@#$%^&*()_+{}|:<>?"

    def test_empty_dict_data(self):
        """Test with empty dictionary."""
        event = BaseReceivedEvent({})

        with pytest.raises(KeyError):
            event["any_key"]

    def test_inheritance_and_custom_attributes(self):
        """Test that BaseReceivedEvent can be inherited and customized."""

        class CustomReceivedEvent(BaseReceivedEvent):
            EXCHANGE = "custom_exchange"
            EXCHANGE_TYPE = ExchangeType.direct

        event = CustomReceivedEvent({"key": "value"})

        assert event.EXCHANGE == "custom_exchange"
        assert event.EXCHANGE_TYPE == ExchangeType.direct
        assert event["key"] == "value"


class TestDataObject:
    """Test suite for DataObject class."""

    def test_init_with_dict(self):
        """Test DataObject initialization with dictionary."""
        test_data = {"key": "value", "number": 42}
        obj = DataObject(test_data)

        assert obj._data == test_data

    def test_init_with_invalid_data(self):
        """Test DataObject initialization with invalid data."""
        with pytest.raises(TypeError, match="Data must be a dictionary."):
            DataObject("not a dict")  # type: ignore

        with pytest.raises(TypeError, match="Data must be a dictionary."):
            DataObject(123)  # type: ignore

        with pytest.raises(TypeError, match="Data must be a dictionary."):
            DataObject([1, 2, 3])  # type: ignore

    def test_getitem_with_valid_key(self):
        """Test __getitem__ with valid keys."""
        test_data = {"name": "John", "age": 30, "active": True}
        obj = DataObject(test_data)

        assert obj["name"] == "John"
        assert obj["age"] == 30
        assert obj["active"] is True

    def test_getitem_with_invalid_key(self):
        """Test __getitem__ with invalid key."""
        test_data = {"key": "value"}
        obj = DataObject(test_data)

        with pytest.raises(KeyError, match="Key 'missing' not found in event data."):
            obj["missing"]

    def test_getitem_with_nested_dict(self):
        """Test __getitem__ returns nested DataObject for dictionary values."""
        test_data = {"user": {"name": "John", "details": {"email": "john@example.com"}}}
        obj = DataObject(test_data)

        user_obj = obj["user"]
        assert isinstance(user_obj, DataObject)
        assert user_obj["name"] == "John"

        details_obj = user_obj["details"]
        assert isinstance(details_obj, DataObject)
        assert details_obj["email"] == "john@example.com"

    def test_getitem_with_empty_dict(self):
        """Test __getitem__ with empty dictionary."""
        obj = DataObject({})

        with pytest.raises(KeyError):
            obj["any_key"]

    def test_getattr_access(self):
        """Test attribute-like access."""
        test_data = {"username": "johndoe", "score": 95.5}
        obj = DataObject(test_data)

        assert obj.username == "johndoe"
        assert obj.score == 95.5

    def test_getattr_with_nested_access(self):
        """Test nested attribute access."""
        test_data = {"config": {"database": {"host": "localhost", "port": 5432}}}
        obj = DataObject(test_data)

        assert isinstance(obj.config, DataObject)
        assert isinstance(obj.config.database, DataObject)
        assert obj.config.database.host == "localhost"
        assert obj.config.database.port == 5432

    def test_mixed_data_types(self):
        """Test DataObject with various data types."""
        test_data = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"inner": "value"},
        }
        obj = DataObject(test_data)

        assert obj.string == "hello"
        assert obj.integer == 42
        assert obj.float == 3.14
        assert obj.boolean is True
        assert obj.null is None
        assert obj.list == [1, 2, 3]
        assert isinstance(obj.nested, DataObject)
        assert obj.nested.inner == "value"

    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases."""
        # Test with None data (should fail at init)
        with pytest.raises(TypeError):
            DataObject(None)  # type: ignore

        # Test accessing non-existent attribute
        obj = DataObject({"existing": "value"})
        with pytest.raises(KeyError):
            obj.nonexistent


class TestBaseReceivedEventIntegration:
    """Integration tests for BaseReceivedEvent with real-world scenarios."""

    def test_real_world_event_message(self):
        """Test with a realistic event message."""
        event_message = {
            "_meta_": {
                "hostname": "web-server-01",
                "timestamp": "2023-12-01 15:30:45",
                "host_ip_address": "10.0.1.100",
                "host_os_in": {
                    "system": "Linux",
                    "release": "5.4.0",
                    "version": "#1 SMP",
                    "machine": "x86_64",
                    "processor": "x86_64",
                },
                "bunnystream_version": "1.0.0",
            },
            "event_type": "order_created",
            "order_id": "ORD-12345",
            "customer": {
                "id": 67890,
                "email": "customer@example.com",
                "name": "Jane Doe",
            },
            "items": [
                {"product_id": "PROD-001", "quantity": 2, "price": 29.99},
                {"product_id": "PROD-002", "quantity": 1, "price": 19.99},
            ],
            "total_amount": 79.97,
            "currency": "USD",
        }

        # Test with JSON string
        json_message = json.dumps(event_message)
        event = BaseReceivedEvent(json_message)

        # Verify metadata access
        meta = event._meta_
        assert isinstance(meta, DataObject)
        assert meta.hostname == "web-server-01"
        assert meta.bunnystream_version == "1.0.0"

        host_os = meta.host_os_in
        assert isinstance(host_os, DataObject)
        assert host_os.system == "Linux"

        # Verify main event data
        assert event.event_type == "order_created"
        assert event.order_id == "ORD-12345"
        assert event.total_amount == 79.97

        # Verify nested customer data
        customer = event.customer
        assert isinstance(customer, DataObject)
        assert customer.id == 67890
        assert customer.email == "customer@example.com"

        # Verify list data (should remain as list)
        assert isinstance(event.items, list)
        assert len(event.items) == 2
        assert event.items[0]["product_id"] == "PROD-001"

    def test_malformed_json_handling(self):
        """Test handling of various malformed JSON scenarios."""
        # Actually malformed JSON
        malformed_jsons = [
            '{"key": "value"',  # Missing closing brace
            '{"key": value}',  # Unquoted value
            '{"key": "value",}',  # Trailing comma
            '{key: "value"}',  # Unquoted key
            "",  # Empty string
        ]

        for malformed_json in malformed_jsons:
            event = BaseReceivedEvent(malformed_json)
            assert event.data is None
            assert event._raw_data == malformed_json

            # Should raise TypeError when trying to access data
            with pytest.raises(TypeError, match="Event data is not a dictionary or is empty."):
                event["any_key"]

        # Valid JSON but not dictionaries - these parse successfully
        valid_non_dict_jsons = [
            ("null", None),
            ("true", True),
            ("123", 123),
            ('"string"', "string"),
            ("[1,2,3]", [1, 2, 3]),
        ]

        for json_str, expected_value in valid_non_dict_jsons:
            event = BaseReceivedEvent(json_str)
            assert event.data == expected_value
            assert event._raw_data == json_str

            # Should raise TypeError when trying to access as dict
            with pytest.raises(TypeError, match="Event data is not a dictionary or is empty."):
                event["any_key"]
