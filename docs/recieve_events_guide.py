"""
BunnyStream recieve_events Method Guide
=======================================

This guide provides comprehensive documentation for the new `recieve_events` method
in the Warren class, which allows consuming multiple event types with individual
consumer management.

Overview
--------

The `recieve_events` method enables you to set up consumption for multiple event
types in a single call. Each event class is treated as an independent consumer
with its own consumer tag, queue, and message routing.

Key Benefits:
- Independent consumer management for each event type
- Automatic queue and exchange declaration
- Type-safe event handling with custom processing logic
- Simplified setup for complex event-driven architectures
- Individual consumer tag tracking for granular control

Basic Usage
-----------

1. Define Event Classes
~~~~~~~~~~~~~~~~~~~~~~~

Create event classes that inherit from BaseReceivedEvent:

.. code-block:: python

    from bunnystream import BaseReceivedEvent
    from pika.exchange_type import ExchangeType

    class UserLoginEvent(BaseReceivedEvent):
        EXCHANGE = "user_events"
        TOPIC = "user.login"
        EXCHANGE_TYPE = ExchangeType.topic  # Optional, defaults to topic

        def processes_event(self) -> None:
            '''Process user login event.'''
            user_id = self.data.get("user_id")
            username = self.data.get("username")
            print(f"🟢 User {username} (ID: {user_id}) logged in")

    class UserLogoutEvent(BaseReceivedEvent):
        EXCHANGE = "user_events"
        TOPIC = "user.logout"

        def processes_event(self) -> None:
            '''Process user logout event.'''
            user_id = self.data.get("user_id")
            username = self.data.get("username")
            print(f"🔴 User {username} (ID: {user_id}) logged out")

    class OrderCreatedEvent(BaseReceivedEvent):
        EXCHANGE = "order_events"
        TOPIC = "order.created"

        def processes_event(self) -> None:
            '''Process order creation event.'''
            order_id = self.data.get("order_id")
            customer_id = self.data.get("customer_id")
            total = self.data.get("total", 0)
            print(f"📦 Order {order_id} created for customer {customer_id}, total: ${total}")

2. Set Up Warren Consumer
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from bunnystream import BunnyStreamConfig, Warren

    # Create Warren configuration for consumer mode
    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)

    # Connect to RabbitMQ
    warren.connect()

    # Set up consumption for multiple event types
    event_classes = [UserLoginEvent, UserLogoutEvent, OrderCreatedEvent]
    warren.recieve_events(event_classes)

    # Start the IO loop to begin consuming
    warren.start_io_loop()

3. Monitoring Consumers
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Check number of active consumers
    consumer_count = warren.get_consumer_count()
    print(f"Active consumers: {consumer_count}")

    # Stop all consumers
    warren.stop_consuming()

    # Stop the IO loop
    warren.stop_io_loop()

    # Disconnect
    warren.disconnect()

Advanced Usage
--------------

Custom Exchange Types
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class BroadcastEvent(BaseReceivedEvent):
        EXCHANGE = "broadcast"
        TOPIC = "announcement"
        EXCHANGE_TYPE = ExchangeType.fanout  # Fanout exchange

        def processes_event(self) -> None:
            message = self.data.get("message")
            print(f"📢 Broadcast: {message}")

    class DirectMessageEvent(BaseReceivedEvent):
        EXCHANGE = "direct_messages"
        TOPIC = "user.123"  # Direct routing
        EXCHANGE_TYPE = ExchangeType.direct

        def processes_event(self) -> None:
            content = self.data.get("content")
            sender = self.data.get("sender")
            print(f"💬 Direct message from {sender}: {content}")

Error Handling in Event Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class RobustOrderEvent(BaseReceivedEvent):
        EXCHANGE = "orders"
        TOPIC = "order.process"

        def processes_event(self) -> None:
            try:
                # Validate required fields
                order_id = self.data["order_id"]
                customer_id = self.data["customer_id"]

                # Process the order
                result = process_order(order_id, customer_id)

                if result.success:
                    print(f"✅ Order {order_id} processed successfully")
                else:
                    # This will cause the message to be redelivered
                    raise ValueError(f"Order processing failed: {result.error}")

            except KeyError as e:
                print(f"❌ Missing required field: {e}")
                # Message will be redelivered due to exception
                raise
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                raise

Manual Message Acknowledgment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class ManualAckEvent(BaseReceivedEvent):
        EXCHANGE = "critical_events"
        TOPIC = "critical.process"

        def processes_event(self) -> None:
            try:
                # Process the critical event
                result = process_critical_data(self.data)

                if result.success:
                    # Manually acknowledge successful processing
                    self.ack_event()
                    print("✅ Critical event processed and acknowledged")
                else:
                    # Don't acknowledge - message will be redelivered
                    print("❌ Critical event processing failed - will retry")

            except Exception as e:
                print(f"❌ Critical error: {e}")
                # Don't acknowledge on error

Combining with Traditional Consumers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Traditional callback-based consumer
    def legacy_message_handler(channel, method, properties, body):
        print(f"Legacy handler: {body.decode()}")
        channel.basic_ack(delivery_tag=method.delivery_tag)

    # Set up both types of consumers
    warren.start_consuming(legacy_message_handler)  # 1 consumer tag
    warren.recieve_events([EventClass1, EventClass2])  # 2 more consumer tags

    # Total consumers: 3
    print(f"Total consumers: {warren.get_consumer_count()}")

Multiple Calls to recieve_events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # First batch of events
    user_events = [UserLoginEvent, UserLogoutEvent]
    warren.recieve_events(user_events)

    # Second batch of events (adds to existing consumers)
    order_events = [OrderCreatedEvent, OrderUpdatedEvent]
    warren.recieve_events(order_events)

    # All 4 event types are now being consumed
    print(f"Total consumers: {warren.get_consumer_count()}")  # 4

Architecture Patterns
------------------

Event-Driven Microservices
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # User Service Events
    class UserCreatedEvent(BaseReceivedEvent):
        EXCHANGE = "user_service"
        TOPIC = "user.created"

        def processes_event(self) -> None:
            # Update user analytics
            update_user_analytics(self.data)

    class UserUpdatedEvent(BaseReceivedEvent):
        EXCHANGE = "user_service"
        TOPIC = "user.updated"

        def processes_event(self) -> None:
            # Sync user data
            sync_user_data(self.data)

    # Order Service Events
    class OrderPlacedEvent(BaseReceivedEvent):
        EXCHANGE = "order_service"
        TOPIC = "order.placed"

        def processes_event(self) -> None:
            # Process payment
            process_payment(self.data)

    class OrderShippedEvent(BaseReceivedEvent):
        EXCHANGE = "order_service"
        TOPIC = "order.shipped"

        def processes_event(self) -> None:
            # Send notification
            send_shipping_notification(self.data)

    # Set up cross-service event consumption
    all_events = [
        UserCreatedEvent, UserUpdatedEvent,
        OrderPlacedEvent, OrderShippedEvent
    ]
    warren.recieve_events(all_events)

Domain-Specific Event Grouping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Authentication domain
    auth_events = [LoginEvent, LogoutEvent, PasswordResetEvent]

    # E-commerce domain
    commerce_events = [OrderCreatedEvent, PaymentProcessedEvent, ShipmentEvent]

    # Analytics domain
    analytics_events = [PageViewEvent, ClickEvent, ConversionEvent]

    # Set up all domains
    warren.recieve_events(auth_events + commerce_events + analytics_events)

Best Practices
--------------

1. Event Class Design
~~~~~~~~~~~~~~~~~~~~~

- Use descriptive class names that clearly indicate the event type
- Define EXCHANGE and TOPIC as class attributes
- Implement robust error handling in processes_event()
- Keep event processing logic focused and single-purpose
- Use type hints for better code documentation

2. Exchange and Topic Naming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Use consistent naming conventions across your application
- Group related events in the same exchange
- Use hierarchical topic names (e.g., "user.created", "user.updated")
- Consider using different exchanges for different domains

3. Error Handling
~~~~~~~~~~~~~~~~~

- Always handle expected exceptions in processes_event()
- Let unexpected exceptions bubble up to trigger message redelivery
- Use manual acknowledgment for critical processing
- Log errors with sufficient context for debugging

4. Resource Management
~~~~~~~~~~~~~~~~~~~~~~

- Always call stop_consuming() and disconnect() in cleanup code
- Use try/finally blocks or context managers for resource cleanup
- Monitor consumer counts to detect resource leaks
- Consider using connection pooling for high-throughput applications

5. Testing
~~~~~~~~~~

- Mock the Warren channel for unit testing event processing
- Test error conditions and exception handling
- Verify consumer tag management and cleanup
- Use integration tests with actual RabbitMQ for end-to-end validation

Common Patterns
---------------

Conditional Event Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class ConditionalEvent(BaseReceivedEvent):
        EXCHANGE = "conditional"
        TOPIC = "process.conditional"

        def processes_event(self) -> None:
            event_type = self.data.get("type")

            if event_type == "urgent":
                self.process_urgent()
            elif event_type == "normal":
                self.process_normal()
            else:
                print(f"Unknown event type: {event_type}")

        def process_urgent(self):
            # Handle urgent processing
            pass

        def process_normal(self):
            # Handle normal processing
            pass

Event Chaining
~~~~~~~~~~~~~~

.. code-block:: python

    class ChainedEvent(BaseReceivedEvent):
        EXCHANGE = "workflow"
        TOPIC = "step.complete"

        def processes_event(self) -> None:
            step_id = self.data.get("step_id")
            workflow_id = self.data.get("workflow_id")

            # Process current step
            result = process_step(step_id, self.data)

            # Trigger next step if successful
            if result.success:
                next_step_data = prepare_next_step(workflow_id, result)
                publish_next_step_event(next_step_data)

Event Aggregation
~~~~~~~~~~~~~~~~~

.. code-block:: python

    class AggregationEvent(BaseReceivedEvent):
        EXCHANGE = "metrics"
        TOPIC = "metric.update"

        def processes_event(self) -> None:
            metric_name = self.data.get("metric")
            value = self.data.get("value")
            timestamp = self.data.get("timestamp")

            # Update aggregated metrics
            update_metric_aggregation(metric_name, value, timestamp)

            # Check if aggregation window is complete
            if is_aggregation_window_complete(metric_name):
                publish_aggregated_metric(metric_name)

Troubleshooting
---------------

Common Issues and Solutions:

1. **ValueError: Event class must define EXCHANGE and TOPIC attributes**
   - Ensure your event class has both EXCHANGE and TOPIC class attributes
   - Check that the values are not None or empty strings

2. **WarrenNotConnected: Cannot start consuming**
   - Call warren.connect() before recieve_events()
   - Ensure RabbitMQ is running and accessible

3. **BunnyStreamConfigurationError: Must be in consumer mode**
   - Set mode="consumer" in BunnyStreamConfig
   - Don't mix producer and consumer operations in the same Warren instance

4. **Messages not being processed**
   - Check that warren.start_io_loop() is called
   - Verify exchange and topic names match message routing
   - Check RabbitMQ management interface for queue status

5. **Memory leaks with consumer tags**
   - Always call warren.stop_consuming() in cleanup code
   - Monitor warren.get_consumer_count() in long-running applications

Performance Considerations
-------------------------

1. **Prefetch Count**: Adjust the prefetch_count in BunnyStreamConfig for optimal throughput
2. **Queue Types**: The method automatically uses quorum queues for high availability
3. **Connection Pooling**: Consider separate Warren instances for high-throughput scenarios
4. **Event Processing**: Keep processes_event() methods lightweight and fast
5. **Acknowledgment**: Use manual acknowledgment sparingly, only for critical operations

Examples Repository
-------------------

See the examples/ directory for complete working examples:

- `multiple_events_demo.py`: Basic usage demonstration
- `test_recieve_events.py`: Logic verification and testing
- `manual_ack_demo.py`: Manual acknowledgment patterns

API Reference
-------------

Warren.recieve_events(event_classes: Sequence[type[BaseReceivedEvent]]) -> None

Parameters:
    event_classes: Sequence of BaseReceivedEvent subclasses

Raises:
    WarrenNotConnected: If no channel is available
    BunnyStreamConfigurationError: If not in consumer mode
    ValueError: If event class validation fails

Related Methods:
    - warren.get_consumer_count() -> int
    - warren.stop_consuming() -> None
    - warren.start_io_loop() -> None
    - warren.stop_io_loop() -> None

This completes the comprehensive guide for the recieve_events method.
"""
