"""
bunnystream.events
------------------

This module defines event classes for publishing and consuming messages within the
bunnystream system. Events are serializable objects that can be published to a message
broker using a configured `Warren` instance. The module handles event metadata enrichment,
serialization (including UUID handling), publishing logic, and convenient message
consumption with automatic JSON parsing.

Classes:
    BaseEvent: Base class for defining publishable events with metadata and
        serialization support.
    BaseReceivedEvent: Base class for consuming and parsing incoming messages with
        convenient access patterns and automatic JSON handling.
    DataObject: Utility class for nested dictionary access with both dictionary
        and attribute syntax.

Exceptions:
    WarrenNotConfigured: Raised when the event's warren or topic/exchange
        configuration is missing.

Dependencies:
    - platform
    - socket
    - datetime
    - uuid
    - json
    - pika.exchange_type.ExchangeType
    - bunnystream.warren.Warren
    - bunnystream.exceptions.WarrenNotConfigured
    - bunnystream.__version__
"""

import json
import platform
import socket
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Union
from uuid import UUID

from pika.exchange_type import ExchangeType  # type: ignore

from bunnystream.exceptions import WarrenNotConfigured

if TYPE_CHECKING:
    from bunnystream.warren import Warren

# Get version directly to avoid circular import
try:
    from importlib.metadata import PackageNotFoundError, version

    bunnystream_version = version("bunnystream")
except ImportError:
    # Python < 3.8
    try:
        from importlib_metadata import PackageNotFoundError, version  # type: ignore

        bunnystream_version = version("bunnystream")
    except ImportError:
        bunnystream_version = "0.0.1-dev"
except (PackageNotFoundError, Exception):  # pylint: disable=broad-exception-caught
    # Fallback for development mode or package not installed
    bunnystream_version = "0.0.1-dev"


class BaseEvent:
    """
    A publishable event.

    Example usage:
        class MyEvent(Event):
            TOPIC = "mytopic"

        event = MyEvent(x=1)
        event.fire()

    The sends a message with a message of '{"x":1}'.

    Some additional attributes are included in the message under the
    "_attributes" key.
    """

    TOPIC = None
    EXCHANGE = None
    EXCHANGE_TYPE = ExchangeType.topic

    def __init__(self, warren: "Warren", **data: Any) -> None:
        self._warren = warren
        self.data = data

    @property
    def json(self) -> str:
        """
        Returns a JSON-serializable representation of the object.

        This method calls the `serialize()` method to obtain a representation of the
        object that can be converted to JSON format.

        Returns:
            dict: A dictionary representation of the object suitable for JSON
                serialization.
        """
        return self.serialize()

    def serialize(self) -> str:
        """
        Serializes the event object to a JSON-formatted string.
        This method updates the event's metadata with information such as hostname,
        timestamp, host IP address, operating system info, and the current version
        of bunnystream. If a RuntimeError occurs during metadata collection, it is
        silently ignored.
        UUID objects within the event data are converted to their hexadecimal string
        representation for JSON serialization.
        Returns:
            str: A JSON-formatted string representing the event data.
        """

        self.set_metadata()

        def uuid_convert(o: Any) -> str:
            if isinstance(o, UUID):
                return o.hex
            return str(o)

        return json.dumps(self.data, default=uuid_convert)

    def fire(self) -> None:
        """
        Publishes the event to the configured message broker.
        Raises:
            WarrenNotConfigured: If the event's warren is not set, or if no
                exchange/topic configuration is found.
        Returns:
            The result of the publish operation from the warren instance.
        """
        if self._warren is None:
            raise WarrenNotConfigured()

        if self.EXCHANGE is None or not isinstance(self.EXCHANGE_TYPE, ExchangeType):  # type: ignore[unreachable]
            exchange_name = self._warren.config.exchange_name
            subscription = self._warren.config.subscription_mappings.get(exchange_name)
            if subscription is None:
                raise WarrenNotConfigured(
                    "No topic is set for this event and no subscription mapping is found."
                )
            self.TOPIC = subscription["topic"]
            self.EXCHANGE = exchange_name
            self.EXCHANGE_TYPE = subscription.get("type", ExchangeType.topic)

        # Ensure we have valid values
        topic = self.TOPIC
        if not isinstance(topic, str):
            raise ValueError("TOPIC must be a string")

        # At this point, EXCHANGE_TYPE is guaranteed to be valid due to the
        # fallback logic above
        assert isinstance(
            self.EXCHANGE_TYPE, ExchangeType
        ), "EXCHANGE_TYPE should be valid"  # nosec B101

        return self._warren.publish(
            topic=topic,
            message=self.json,
            exchange=self.EXCHANGE,
            exchange_type=self.EXCHANGE_TYPE,
        )

    def __getitem__(self, item: Any) -> Any:
        return self.data[item]

    def __setitem__(self, key: Any, value: Any) -> None:
        if value is not None and not isinstance(value, (list, dict, tuple, str, float, int, bool)):
            value = str(value)

        self.data[key] = value

    def set_metadata(self) -> None:
        """
        Sets metadata information for the current instance, including hostname, timestamp,
        host IP address, OS information, and the bunnystream version.
        The metadata is stored under the "_meta_" key. If a RuntimeError occurs during
        the process, it is silently ignored.
        """
        try:
            self["_meta_"] = {
                "hostname": str(platform.node()),
                "timestamp": str(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
                "host_ip_address": str(self._get_host_ip_address()),
                "host_os_in": self._get_os_info(),
                "bunnystream_version": bunnystream_version,
            }
        except RuntimeError:
            pass

    def _get_host_ip_address(self) -> str:
        """
        Get the host IP address.
        This is a placeholder for the actual implementation.
        """
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except (OSError, socket.gaierror, Exception):  # pylint: disable=broad-except
            # Handle socket errors and other network-related exceptions
            ip_address = "127.0.0.1"
        return ip_address

    def _get_os_info(self) -> dict[str, str]:
        """
        Get the operating system information.
        This is a placeholder for the actual implementation.
        """
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }


class BaseReceivedEvent:
    """
    BaseReceivedEvent represents a base class for events received from a message broker.

    Attributes:
        EXCHANGE (str or None): The exchange to use for the event. Defaults to None
                                (default exchange).
        EXCHANGE_TYPE (ExchangeType): The type of exchange to use. Defaults to
                                ExchangeType.topic.

    Args:
        data (Union[dict, str]): The event data, either as a dictionary or a JSON string.

    Raises:
        TypeError: If the provided data is not a dictionary or a JSON string.

    Methods:
        __getitem__(item):
            Allows dictionary-like access to the event data.
            Raises KeyError if the item is not found in the data.
            Raises TypeError if the event data is not a dictionary or is empty.
    """

    EXCHANGE = None  # use the default exchange
    EXCHANGE_TYPE = ExchangeType.topic  # use the default topic

    def __init__(self, data: Union[dict, str]) -> None:
        if isinstance(data, str):
            self._raw_data = data
            # Attempt to parse the string as JSON
            try:
                self.data = json.loads(data)
            except json.JSONDecodeError:
                self.data = None
        elif isinstance(data, dict):
            self._raw_data = json.dumps(data)
            self.data = data
        else:
            raise TypeError("Data must be a dictionary or a JSON string.")

    def __getitem__(self, item: Any) -> Any:
        if self.data is not None and isinstance(self.data, dict):
            if item not in self.data:
                raise KeyError(f"Key '{item}' not found in event data.")
            if isinstance(self.data[item], dict):
                return DataObject(self.data[item])
            return self.data[item]
        raise TypeError("Event data is not a dictionary or is empty.")

    def __getattr__(self, item: Any) -> Any:
        """
        Allows attribute-like access to the event data.
        """
        return self.__getitem__(item)


class DataObject:
    """
    DataObject is a simple class that allows for dynamic attribute assignment.
    It can be used to create objects with attributes that can be set and accessed
    like a dictionary.

    Example:
        obj = DataObject()
        obj.name = "example"
        print(obj.name)  # Output: example
    """

    def __init__(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary.")
        self._data = data

    def __getitem__(self, item: Any) -> Any:
        if self._data is not None and isinstance(self._data, dict):
            if item not in self._data:
                raise KeyError(f"Key '{item}' not found in event data.")
            if isinstance(self._data[item], dict):
                return DataObject(self._data[item])
            return self._data[item]
        raise TypeError("Event data is not a dictionary or is empty.")

    def __getattr__(self, item: Any) -> Any:
        """
        Allows attribute-like access to the event data.
        """
        return self.__getitem__(item)
