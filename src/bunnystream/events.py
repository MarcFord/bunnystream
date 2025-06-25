"""
bunnystream.events
------------------

This module defines the `BaseEvent` class, which provides a framework for creating
and publishing events within the bunnystream system. Events are serializable objects
that can be published to a message broker using a configured `Warren` instance. The
module handles event metadata enrichment, serialization (including UUID handling), and
publishing logic, with support for dynamic topic and exchange configuration.

Classes:
    BaseEvent: Base class for defining publishable events with metadata and
        serialization support.

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
from typing import TYPE_CHECKING
from uuid import UUID

from pika.exchange_type import ExchangeType  # type: ignore

from bunnystream import __version__ as bunnystream_version
from bunnystream.exceptions import WarrenNotConfigured

if TYPE_CHECKING:
    from bunnystream.warren import Warren


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

    def __init__(self, warren: "Warren", **data) -> None:
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

        def uuid_convert(o) -> str:
            if isinstance(o, UUID):
                return o.hex
            return o

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

        if self.EXCHANGE is None or not isinstance(self.EXCHANGE_TYPE, ExchangeType):
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

    def __getitem__(self, item) -> object:
        return self.data[item]

    def __setitem__(self, key, value) -> None:
        if value is not None and not isinstance(value, (list, dict, tuple, str, float, int, bool)):
            value = str(value)

        self.data[key] = value

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
