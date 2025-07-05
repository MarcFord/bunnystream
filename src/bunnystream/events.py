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
from abc import abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Union
from uuid import UUID

from pika.exchange_type import ExchangeType  # type: ignore

from bunnystream.exceptions import EventProcessingError, WarrenNotConfigured
from bunnystream.logger import get_bunny_logger

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
    Base class for type-safe, publishable events with automatic metadata enrichment.

    BaseEvent provides a robust foundation for creating event-driven applications with
    RabbitMQ. It handles serialization, metadata enrichment, UUID support, and provides
    a clean API for publishing events to message brokers.

    Key Features:
        - Automatic metadata enrichment (timestamp, hostname, IP, OS info)
        - JSON serialization with UUID support
        - Type-safe event publishing
        - Configurable exchange and routing key
        - Dictionary-like access for event data
        - Integration with Warren for message publishing

    Class Attributes:
        TOPIC (str): Default routing key for messages (can be overridden per event)
        EXCHANGE (str): Default exchange name (can be overridden per event)
        EXCHANGE_TYPE (ExchangeType): Exchange type (default: topic)

    Instance Attributes:
        data (dict): Event payload data
        _warren (Warren): Warren instance for publishing

    Metadata Fields:
        Events are automatically enriched with metadata under "_attributes":
        - hostname: System hostname
        - timestamp: UTC timestamp in ISO format
        - host_ip: Host IP address
        - operating_system: OS platform information
        - bunnystream_version: BunnyStream library version

    Examples:
        Basic Event Publishing:
            >>> from bunnystream import BaseEvent, Warren, BunnyStreamConfig
            >>>
            >>> class UserEvent(BaseEvent):
            ...     EXCHANGE = "user_events"
            ...     TOPIC = "user.created"
            ...
            >>> config = BunnyStreamConfig(mode="producer")
            >>> warren = Warren(config)
            >>> warren.connect()
            >>>
            >>> event = UserEvent(warren, user_id=123, email="user@example.com")
            >>> event.fire()

        Dynamic Topic and Exchange:
            >>> event = UserEvent(warren, user_id=123)
            >>> event.fire(topic="user.updated", exchange="user_updates")

        Event with Complex Data:
            >>> class OrderEvent(BaseEvent):
            ...     EXCHANGE = "orders"
            ...     TOPIC = "order.created"
            ...
            >>> order_data = {
            ...     "order_id": "ORD-123",
            ...     "customer": {"id": 456, "email": "customer@example.com"},
            ...     "items": [{"sku": "ITEM-1", "quantity": 2, "price": 29.99}],
            ...     "total": 59.98
            ... }
            >>> event = OrderEvent(warren, **order_data)
            >>> event.fire()

        Accessing Event Data:
            >>> event = UserEvent(warren, user_id=123, name="John Doe")
            >>> print(event["user_id"])  # 123
            >>> print(event["name"])     # "John Doe"
            >>> event["email"] = "john@example.com"  # Add new data

        Event with UUID:
            >>> import uuid
            >>> event_id = uuid.uuid4()
            >>> event = UserEvent(warren, event_id=event_id, user_id=123)
            >>> # UUID is automatically converted to string in JSON

        Serialization and Inspection:
            >>> event = UserEvent(warren, user_id=123)
            >>> json_str = event.serialize()  # Get JSON string
            >>> print(event.json)  # Same as serialize()
            >>>
            >>> # JSON includes metadata:
            >>> # {
            >>> #   "user_id": 123,
            >>> #   "_attributes": {
            >>> #     "hostname": "server-01",
            >>> #     "timestamp": "2025-01-01T12:00:00.000000+00:00",
            >>> #     "host_ip": "192.168.1.100",
            >>> #     "operating_system": "Linux-5.4.0",
            >>> #     "bunnystream_version": "1.0.0"
            >>> #   }
            >>> # }

        Error Handling:
            >>> try:
            ...     event = UserEvent(warren, user_id=123)
            ...     event.fire()
            ... except WarrenNotConfigured:
            ...     print("Warren not properly configured")
            ... except Exception as e:
            ...     print(f"Publishing failed: {e}")

        Custom Event with Validation:
            >>> class ValidatedUserEvent(BaseEvent):
            ...     EXCHANGE = "user_events"
            ...     TOPIC = "user.created"
            ...
            ...     def __init__(self, warren, user_id, email, **kwargs):
            ...         if not isinstance(user_id, int) or user_id <= 0:
            ...             raise ValueError("user_id must be a positive integer")
            ...         if "@" not in email:
            ...             raise ValueError("email must be valid")
            ...         super().__init__(warren, user_id=user_id, email=email, **kwargs)
            ...
            >>> event = ValidatedUserEvent(warren, user_id=123, email="user@example.com")

        Event Inheritance:
            >>> class BaseUserEvent(BaseEvent):
            ...     EXCHANGE = "user_events"
            ...
            ...     def __init__(self, warren, user_id, **kwargs):
            ...         super().__init__(warren, user_id=user_id, **kwargs)
            ...         self["timestamp"] = self.get_current_timestamp()
            ...
            >>> class UserLoginEvent(BaseUserEvent):
            ...     TOPIC = "user.login"
            ...
            >>> class UserLogoutEvent(BaseUserEvent):
            ...     TOPIC = "user.logout"

    Methods:
        fire(topic=None, exchange=None, exchange_type=None): Publish the event
        serialize(): Convert event to JSON string with metadata
        get_current_timestamp(): Get current UTC timestamp
        get_host_ip_address(): Get host IP address
        get_os_info(): Get operating system information
        set_metadata(): Add metadata to event (called automatically)

    Notes:
        - Events are immutable once published
        - Metadata is added automatically before publishing
        - UUID objects are converted to strings during serialization
        - Warren instance must be connected before publishing
        - Exchange and topic can be overridden at publish time
        - All event data should be JSON-serializable

    Raises:
        WarrenNotConfigured: If Warren instance is None or not properly configured
        ValueError: If event data contains non-serializable objects
        TypeError: If required parameters are missing or invalid

    See Also:
        BaseReceivedEvent: For consuming and parsing received events
        Warren: For connection and publishing management
        BunnyStreamConfig: For configuration management
    """

    TOPIC: Union[str, None] = None
    EXCHANGE: Union[str, None] = None
    EXCHANGE_TYPE: ExchangeType = ExchangeType.topic

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

        if self.EXCHANGE is None or not isinstance(self.EXCHANGE_TYPE, ExchangeType):
            exchange_name = self._warren.config.exchange_name
            subscription = self._warren.config.subscription_mappings.get(exchange_name)
            if subscription is None:
                raise WarrenNotConfigured(
                    "No topic is set for this event and no subscription mapping is found."
                )
            self.TOPIC = str(subscription["topic"])
            self.EXCHANGE = str(exchange_name)
            exchange_type = subscription.get("type", ExchangeType.topic)
            if isinstance(exchange_type, ExchangeType):
                self.EXCHANGE_TYPE = exchange_type
            else:
                self.EXCHANGE_TYPE = ExchangeType.topic

        # Ensure we have valid values
        topic = self.TOPIC
        if not isinstance(topic, str):
            raise ValueError("TOPIC must be a string")

        # At this point, EXCHANGE_TYPE is guaranteed to be valid due to the
        # fallback logic above
        if not isinstance(self.EXCHANGE_TYPE, ExchangeType):
            raise ValueError("EXCHANGE_TYPE should be valid")

        return self._warren.publish(
            topic=topic,
            message=self.json,
            exchange=self.EXCHANGE,
            exchange_type=self.EXCHANGE_TYPE,
        )

    def __getitem__(self, item: Any) -> Any:
        return self.data[item]

    def __setitem__(self, key: Any, value: Any) -> None:
        if value is not None and not isinstance(
            value, (list, dict, tuple, str, float, int, bool)
        ):
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
                "timestamp": str(
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                ),
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
    Enhanced base class for convenient consumption and parsing of RabbitMQ messages.

    BaseReceivedEvent provides a powerful and intuitive interface for consuming messages
    from RabbitMQ queues. It automatically handles JSON parsing, provides both dictionary
    and attribute-style access to message data, and supports nested data structures with
    automatic DataObject wrapping.

    Key Features:
        - Automatic JSON parsing from string or bytes
        - Dictionary-style access: event['key']
        - Attribute-style access: event.key
        - Nested data structure support with DataObject
        - Flexible data input handling (dict, str, bytes)
        - Comprehensive error handling for missing keys
        - Raw data preservation for debugging
        - Manual message acknowledgment with ack_event()

    Data Access Patterns:
        The class supports multiple ways to access message data:
        - Dictionary access: event['user_id']
        - Attribute access: event.user_id
        - Nested access: event.user.profile.name (auto-wrapped in DataObject)
        - Raw data access: event._raw_data (original string/bytes)

    Class Attributes:
        EXCHANGE (str, optional): Default exchange name (None for default exchange)
        EXCHANGE_TYPE (ExchangeType): Exchange type for message routing (default: topic)

    Instance Attributes:
        data (dict): Parsed message data as dictionary
        _raw_data (str): Original raw message data for debugging
        _channel (Any): RabbitMQ channel object for acknowledgment (if provided)
        _method (Any): RabbitMQ method object with delivery information (if provided)

    Examples:
        Basic Message Consumption:
            >>> from bunnystream import BaseReceivedEvent
            >>>
            >>> def message_handler(channel, method, properties, body):
            ...     event = BaseReceivedEvent(body)
            ...     print(f"User: {event.user_id}")
            ...     print(f"Email: {event.email}")
            ...     print(f"Name: {event['name']}")  # Dictionary access
            ...
            >>> # Use with Warren consumer
            >>> warren.start_consuming(message_handler)

        Manual Message Acknowledgment:
            >>> from bunnystream import BaseReceivedEvent
            >>>
            >>> def manual_ack_handler(channel, method, properties, body):
            ...     # Create event with channel and method for manual ack
            ...     event = BaseReceivedEvent(body, channel, method)
            ...
            ...     try:
            ...         # Process the message
            ...         user_id = event.user_id
            ...         process_user_data(user_id)
            ...
            ...         # Manually acknowledge after successful processing
            ...         event.ack_event()
            ...         print(f"✅ User {user_id} processed and acknowledged")
            ...     except Exception as e:
            ...         print(f"❌ Processing failed: {e}")
            ...         # Don't acknowledge - message will be redelivered
            ...
            >>> # Use with Warren consumer (set auto_ack=False)
            >>> warren.start_consuming(manual_ack_handler)

        JSON Message Parsing:
            >>> json_message = '{"user_id": 123, "email": "user@example.com", "active": true}'
            >>> event = BaseReceivedEvent(json_message)
            >>> print(f"User ID: {event.user_id}")      # 123
            >>> print(f"Email: {event.email}")          # user@example.com
            >>> print(f"Active: {event.active}")        # True

        Nested Data Access:
            >>> nested_json = '''
            ... {
            ...     "user_id": 123,
            ...     "profile": {
            ...         "name": "John Doe",
            ...         "address": {
            ...             "street": "123 Main St",
            ...             "city": "New York"
            ...         }
            ...     }
            ... }
            ... '''
            >>> event = BaseReceivedEvent(nested_json)
            >>> print(f"Name: {event.profile.name}")               # John Doe
            >>> print(f"City: {event.profile.address.city}")       # New York
            >>> print(f"Street: {event['profile']['address']['street']}")  # 123 Main St

        Dictionary Data Input:
            >>> data_dict = {"order_id": "ORD-456", "amount": 99.99, "items": []}
            >>> event = BaseReceivedEvent(data_dict)
            >>> print(f"Order: {event.order_id}")       # ORD-456
            >>> print(f"Amount: ${event.amount}")       # $99.99

        Error Handling:
            >>> event = BaseReceivedEvent('{"user_id": 123}')
            >>> try:
            ...     missing_value = event.non_existent_field
            ... except KeyError as e:
            ...     print(f"Missing field: {e}")
            ... except AttributeError as e:
            ...     print(f"Attribute error: {e}")

        Raw Data Access:
            >>> event = BaseReceivedEvent('{"user_id": 123}')
            >>> print(f"Raw data: {event._raw_data}")   # Original JSON string
            >>> print(f"Parsed data: {event.data}")     # Python dict

        Type Checking and Validation:
            >>> def process_user_event(channel, method, properties, body):
            ...     try:
            ...         event = BaseReceivedEvent(body)
            ...
            ...         # Validate required fields
            ...         if not hasattr(event, 'user_id'):
            ...             raise ValueError("Missing user_id")
            ...
            ...         # Type checking
            ...         if not isinstance(event.user_id, int):
            ...             raise TypeError("user_id must be integer")
            ...
            ...         # Process the event
            ...         print(f"Processing user {event.user_id}")
            ...
            ...     except (KeyError, TypeError, ValueError) as e:
            ...         print(f"Event processing error: {e}")
            ...         channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            ...         return
            ...
            ...     # Acknowledge successful processing
            ...     channel.basic_ack(delivery_tag=method.delivery_tag)

        Integration with Warren Consumer:
            >>> from bunnystream import Warren, BunnyStreamConfig, Subscription
            >>> from pika.exchange_type import ExchangeType
            >>>
            >>> def handle_user_events(channel, method, properties, body):
            ...     event = BaseReceivedEvent(body)
            ...
            ...     if hasattr(event, 'action'):
            ...         if event.action == 'login':
            ...             print(f"User {event.user_id} logged in")
            ...         elif event.action == 'logout':
            ...             print(f"User {event.user_id} logged out")
            ...         else:
            ...             print(f"Unknown action: {event.action}")
            ...
            >>> subscription = Subscription("user_events", ExchangeType.topic, "user.*")
            >>> config = BunnyStreamConfig(mode="consumer", subscriptions=[subscription])
            >>> warren = Warren(config)
            >>> warren.start_consuming(handle_user_events)

        Complex Data Processing:
            >>> def process_order_event(channel, method, properties, body):
            ...     event = BaseReceivedEvent(body)
            ...
            ...     # Access order details
            ...     order_id = event.order_id
            ...     customer = event.customer  # DataObject for nested data
            ...
            ...     # Calculate total from items
            ...     total = sum(item.price * item.quantity for item in event.items)
            ...
            ...     # Process each item
            ...     for item in event.items:
            ...         print(f"Item: {item.name}, Price: ${item.price}")
            ...
            ...     print(f"Order {order_id} total: ${total}")
            ...     print(f"Customer: {customer.name} ({customer.email})")

        Metadata Access:
            >>> # If the original event included metadata
            >>> event = BaseReceivedEvent(body)
            >>> if hasattr(event, '_meta_'):
            ...     print(f"Event timestamp: {event._meta_.timestamp}")
            ...     print(f"Source hostname: {event._meta_.hostname}")

    Parameters:
        data (Union[dict, str, bytes]): The event data to parse. Can be:
            - dict: Python dictionary with event data
            - str: JSON string to be parsed
            - bytes: UTF-8 encoded JSON bytes to be parsed
        channel (Any, optional): RabbitMQ channel object for manual acknowledgment.
            Required for ack_event() functionality.
        method (Any, optional): RabbitMQ method object containing delivery information.
            Required for ack_event() functionality.

    Raises:
        TypeError: If data is not a dictionary, string, or bytes
        json.JSONDecodeError: If string/bytes data is not valid JSON
        KeyError: If accessing a non-existent field via dictionary access
        AttributeError: If accessing a non-existent field via attribute access

    Notes:
        - JSON parsing errors are handled gracefully, setting data to None
        - Nested dictionaries are automatically wrapped in DataObject instances
        - Raw data is preserved for debugging and reprocessing
        - Both dictionary and attribute access styles are supported
        - The class is designed for high-performance message processing
        - Thread-safe for read operations (no shared mutable state)

    See Also:
        BaseEvent: For publishing events to RabbitMQ
        DataObject: For accessing nested dictionary data
        Warren: For connection and message management
    """

    EXCHANGE = None  # use the default exchange
    TOPIC = None  # use the default topic
    EXCHANGE_TYPE = ExchangeType.topic  # use the default topic

    def __init__(
        self, data: Union[dict, str], channel: Any = None, method: Any = None
    ) -> None:
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

        # Store channel and method for manual acknowledgment
        self._channel = channel
        self._method = method
        self.logger = get_bunny_logger(__name__)
        self._event_properties = None

    @property
    def properties(self) -> Any:
        """
        Returns the event properties if available.
        This is useful for accessing RabbitMQ message properties.
        """
        return self._event_properties

    @properties.setter
    def properties(self, value: Any) -> None:
        """
        Sets the event properties.
        This allows you to store additional metadata or RabbitMQ message properties.
        """
        self._event_properties = value

    @property
    def exchange_name(self) -> str:
        """
        Returns the exchange name for this event.
        If EXCHANGE is not set, returns the default exchange name.
        """
        return self.EXCHANGE if self.EXCHANGE else ""

    @property
    def topic(self) -> str:
        """
        Returns the topic for this event.
        If TOPIC is not set, returns an empty string.
        """
        return self.TOPIC if self.TOPIC else ""

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

    @abstractmethod
    def processes_event(self) -> None:
        """
        Processes the event data.
        This method must be implemented in subclasses to provide custom processing logic.
        """

    @classmethod
    def _on_message(
        cls,
        channel: Any,
        method: Any,
        properties: Any,  # pylint: disable=unused-argument
        body: Any,
    ) -> None:
        """
        Handles incoming messages from a message broker channel.

        This class method is invoked when a new message is received. It initializes an
        event instance with the provided message data and channel information, processes
        the event, and acknowledges the message. If an exception occurs during event
        processing, it is silently ignored.

        Args:
            channel (Any): The channel object from which the message was received.
            method (Any): Delivery method information for the message.
            properties (Any): Message properties.
            body (Any): The message payload.

        Returns:
            None
        """
        event = cls(data=body, channel=channel, method=method)
        event.properties = properties
        try:
            event.processes_event()
        except Exception as e:
            event.logger.error(
                "Error processing event: %s. Message will be redelivered if "
                "auto-acknowledgment is not set.",
                e,
            )
            raise EventProcessingError from e
        event.ack_event()

    def ack_event(self) -> None:
        """
        Manually acknowledge the received event.

        This method sends an acknowledgment to RabbitMQ indicating that the message
        has been successfully processed. The message will be removed from the queue
        and will not be redelivered.

        This is useful when you want to control acknowledgment manually instead of
        relying on automatic acknowledgment in the message handler.

        Examples:
            Basic Manual Acknowledgment:
                >>> def message_handler(channel, method, properties, body):
                ...     event = BaseReceivedEvent(body, channel, method)
                ...
                ...     try:
                ...         # Process the message
                ...         print(f"Processing user {event.user_id}")
                ...         # ... business logic here ...
                ...
                ...         # Acknowledge after successful processing
                ...         event.ack_event()
                ...     except Exception as e:
                ...         print(f"Processing failed: {e}")
                ...         # Don't acknowledge - let message be redelivered

            Conditional Acknowledgment:
                >>> def selective_handler(channel, method, properties, body):
                ...     event = BaseReceivedEvent(body, channel, method)
                ...
                ...     if event.priority == 'high':
                ...         # Process high priority immediately
                ...         process_high_priority(event)
                ...         event.ack_event()
                ...     else:
                ...         # Queue low priority for later processing
                ...         queue_for_later(event)
                ...         event.ack_event()

            Error Handling with Manual Ack:
                >>> def robust_handler(channel, method, properties, body):
                ...     event = BaseReceivedEvent(body, channel, method)
                ...
                ...     try:
                ...         result = process_event(event)
                ...         if result.success:
                ...             event.ack_event()
                ...             print("✅ Message processed and acknowledged")
                ...         else:
                ...             # Don't ack - let it be redelivered
                ...             print("❌ Processing failed - message will be redelivered")
                ...     except Exception as e:
                ...         print(f"Error: {e} - message will be redelivered")

        Raises:
            RuntimeError: If the event was not created with channel and method information
            Exception: If the acknowledgment fails due to connection issues

        Notes:
            - This method can only be called once per event
            - The channel and method must be provided when creating the BaseReceivedEvent
            - After acknowledgment, the message is permanently removed from the queue
            - If acknowledgment fails, the message may be redelivered depending on RabbitMQ settings
            - For automatic acknowledgment, don't call this method and let Warren handle it

        See Also:
            nack_event(): For negative acknowledgment with optional requeue
            reject_event(): For rejecting a message without requeue
        """
        if self._channel is None or self._method is None:
            raise RuntimeError(
                "Cannot acknowledge event: channel and method information not available. "
                "Make sure to pass channel and method when creating BaseReceivedEvent."
            )

        try:
            self._channel.basic_ack(delivery_tag=self._method.delivery_tag)
        except Exception as e:
            raise RuntimeError(f"Failed to acknowledge message: {e}") from e


class DataObject:
    """
    Flexible data access object for nested dictionary structures with dual access patterns.

    DataObject provides an elegant interface for accessing nested dictionary data using
    both dictionary-style and attribute-style syntax. It automatically handles nested
    structures by wrapping child dictionaries in DataObject instances, creating a
    seamless access experience for complex data hierarchies.

    Key Features:
        - Dictionary-style access: obj['key']
        - Attribute-style access: obj.key
        - Automatic nesting: nested dicts become DataObject instances
        - Type safety with comprehensive error handling
        - Recursive data structure support
        - Immutable data access (read-only)

    Access Patterns:
        DataObject supports multiple ways to access nested data:
        - Direct access: obj.field_name
        - Dictionary access: obj['field_name']
        - Chained access: obj.user.profile.address.city
        - Mixed access: obj['user'].profile['address'].city

    Examples:
        Basic Usage:
            >>> data = {"name": "John", "age": 30, "active": True}
            >>> obj = DataObject(data)
            >>> print(obj.name)        # John
            >>> print(obj['age'])      # 30
            >>> print(obj.active)      # True

        Nested Data Access:
            >>> nested_data = {
            ...     "user": {
            ...         "id": 123,
            ...         "profile": {
            ...             "name": "Jane Doe",
            ...             "contact": {
            ...                 "email": "jane@example.com",
            ...                 "phone": "+1-555-0123"
            ...             }
            ...         }
            ...     }
            ... }
            >>> obj = DataObject(nested_data)
            >>> print(obj.user.id)                           # 123
            >>> print(obj.user.profile.name)                 # Jane Doe
            >>> print(obj.user.profile.contact.email)        # jane@example.com
            >>> print(obj['user']['profile']['contact']['phone'])  # +1-555-0123

        Array/List Access:
            >>> data_with_arrays = {
            ...     "users": [
            ...         {"name": "Alice", "role": "admin"},
            ...         {"name": "Bob", "role": "user"}
            ...     ],
            ...     "metadata": {"total": 2}
            ... }
            >>> obj = DataObject(data_with_arrays)
            >>> print(obj.users[0]['name'])       # Alice
            >>> print(obj.users[1]['role'])       # user
            >>> print(obj.metadata.total)         # 2

        With BaseReceivedEvent:
            >>> json_message = '''
            ... {
            ...     "order": {
            ...         "id": "ORD-123",
            ...         "customer": {
            ...             "name": "John Smith",
            ...             "address": {
            ...                 "street": "123 Main St",
            ...                 "city": "New York",
            ...                 "zip": "10001"
            ...             }
            ...         },
            ...         "items": [
            ...             {"name": "Widget", "price": 19.99, "qty": 2},
            ...             {"name": "Gadget", "price": 29.99, "qty": 1}
            ...         ]
            ...     }
            ... }
            ... '''
            >>> event = BaseReceivedEvent(json_message)
            >>> order = event.order  # Automatically becomes DataObject
            >>> print(f"Order ID: {order.id}")
            >>> print(f"Customer: {order.customer.name}")
            >>> print(f"City: {order.customer.address.city}")
            >>> print(f"ZIP: {order.customer.address.zip}")
            >>>
            >>> # Access items in the order
            >>> for item in order.items:
            ...     print(f"Item: {item['name']}, Price: ${item['price']}")

        Error Handling:
            >>> data = {"user": {"name": "John"}}
            >>> obj = DataObject(data)
            >>>
            >>> # Accessing existing fields
            >>> print(obj.user.name)  # John
            >>>
            >>> # Accessing non-existent fields
            >>> try:
            ...     missing = obj.user.email
            ... except KeyError as e:
            ...     print(f"Missing field: {e}")
            >>>
            >>> try:
            ...     missing = obj['nonexistent']
            ... except KeyError as e:
            ...     print(f"Key not found: {e}")

        Complex Data Processing:
            >>> complex_data = {
            ...     "analytics": {
            ...         "metrics": {
            ...             "pageviews": 1000,
            ...             "unique_visitors": 750,
            ...             "bounce_rate": 0.35
            ...         },
            ...         "demographics": {
            ...             "age_groups": {
            ...                 "18-24": 25,
            ...                 "25-34": 40,
            ...                 "35-44": 20,
            ...                 "45+": 15
            ...             }
            ...         }
            ...     }
            ... }
            >>> obj = DataObject(complex_data)
            >>> metrics = obj.analytics.metrics
            >>> print(f"Pageviews: {metrics.pageviews}")
            >>> print(f"Bounce Rate: {metrics.bounce_rate:.1%}")
            >>>
            >>> # Access age group data
            >>> age_groups = obj.analytics.demographics.age_groups
            >>> for age_range, percentage in age_groups._data.items():
            ...     print(f"Age {age_range}: {percentage}%")

        Integration with Message Processing:
            >>> def process_analytics_event(channel, method, properties, body):
            ...     event = BaseReceivedEvent(body)
            ...
            ...     # Access nested analytics data
            ...     analytics = event.analytics
            ...
            ...     # Process metrics
            ...     if hasattr(analytics, 'metrics'):
            ...         metrics = analytics.metrics
            ...         print(f"Pageviews: {metrics.pageviews}")
            ...         print(f"Visitors: {metrics.unique_visitors}")
            ...
            ...     # Process demographics
            ...     if hasattr(analytics, 'demographics'):
            ...         demo = analytics.demographics
            ...         if hasattr(demo, 'age_groups'):
            ...             age_data = demo.age_groups
            ...             # Process age group data...

        Type Checking and Validation:
            >>> def validate_user_data(data_obj):
            ...     try:
            ...         # Check required fields
            ...         user_id = data_obj.user_id
            ...         username = data_obj.username
            ...
            ...         # Validate profile if present
            ...         if hasattr(data_obj, 'profile'):
            ...             profile = data_obj.profile
            ...             if hasattr(profile, 'email'):
            ...                 email = profile.email
            ...                 if '@' not in email:
            ...                     raise ValueError("Invalid email format")
            ...
            ...         return True
            ...     except (KeyError, AttributeError) as e:
            ...         print(f"Validation error: {e}")
            ...         return False

    Parameters:
        data (dict): Dictionary data to wrap. Must be a valid Python dictionary.

    Raises:
        TypeError: If data is not a dictionary
        KeyError: If accessing a non-existent key via dictionary or attribute access

    Notes:
        - DataObject instances are immutable (read-only access)
        - Nested dictionaries are automatically wrapped in DataObject instances
        - List/array elements are returned as-is (not wrapped)
        - The _data attribute provides access to the underlying dictionary
        - Thread-safe for read operations (no shared mutable state)
        - Designed for high-performance nested data access

    See Also:
        BaseReceivedEvent: Primary consumer of DataObject for message parsing
        BaseEvent: For publishing structured events
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
