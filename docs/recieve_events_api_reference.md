"""
Warren.recieve_events() Method - Complete API Reference
=======================================================

This document provides comprehensive documentation for the Warren.recieve_events() method,
a powerful feature for consuming multiple event types with individual consumer management.

Table of Contents
-----------------
1. Overview
2. Method Signature
3. Parameters
4. Return Value
5. Exceptions
6. Basic Usage
7. Advanced Usage
8. Consumer Management
9. Best Practices
10. Troubleshooting
11. Examples

1. Overview
-----------

The `recieve_events()` method enables you to set up consumption for multiple event types
in a single call. Each event class is treated as an independent consumer with its own
consumer tag, queue, and message routing.

Key Benefits:
- Independent consumer management for each event type
- Automatic queue and exchange declaration
- Type-safe event handling with custom processing logic
- Simplified setup for complex event-driven architectures
- Individual consumer tag tracking for granular control

2. Method Signature
-------------------

```python
def recieve_events(self, event_classes: Sequence[type[BaseReceivedEvent]]) -> None:
```

3. Parameters
-------------

event_classes : Sequence[type[BaseReceivedEvent]]
    A sequence (list, tuple, etc.) of event classes to consume. Each class must:
    - Inherit from BaseReceivedEvent
    - Define EXCHANGE and TOPIC class attributes
    - Implement the processes_event() method
    - Optionally define EXCHANGE_TYPE (defaults to ExchangeType.topic)

4. Return Value
---------------

None - This method doesn't return a value but sets up the consumers internally.

5. Exceptions
-------------

WarrenNotConnected
    Raised if no channel is available (Warren not connected to RabbitMQ)

BunnyStreamConfigurationError
    Raised if Warren is not in 'consumer' mode

ValueError
    Raised if an event class doesn't have required EXCHANGE and TOPIC attributes
    or if they are None/empty

6. Basic Usage
--------------

```python
from bunnystream import Warren, BunnyStreamConfig, BaseReceivedEvent
from pika.exchange_type import ExchangeType

# Define event classes
class UserLoginEvent(BaseReceivedEvent):
    EXCHANGE = "user_events"
    TOPIC = "user.login"
    
    def processes_event(self) -> None:
        user_id = self.data.get('user_id')
        print(f"🟢 User {user_id} logged in")

class OrderCreatedEvent(BaseReceivedEvent):
    EXCHANGE = "order_events"
    TOPIC = "order.created"
    EXCHANGE_TYPE = ExchangeType.direct
    
    def processes_event(self) -> None:
        order_id = self.data.get('order_id')
        amount = self.data.get('amount')
        print(f"📦 Order {order_id} created for ${amount}")

# Set up Warren and consume events
config = BunnyStreamConfig(mode="consumer")
warren = Warren(config)
warren.connect()

# Each event class gets its own consumer tag
warren.recieve_events([UserLoginEvent, OrderCreatedEvent])

# Start processing (blocking call)
warren.start_io_loop()
```

7. Advanced Usage
-----------------

### Multiple Event Groups

```python
# Handle different event categories
user_events = [UserLoginEvent, UserLogoutEvent, UserUpdateEvent]
order_events = [OrderCreatedEvent, OrderCancelledEvent, OrderShippedEvent]
payment_events = [PaymentProcessedEvent, PaymentFailedEvent]

# Set up all user event consumers
warren.recieve_events(user_events)
print(f"User event consumers: {warren.get_consumer_count()}")

# Add order event consumers
warren.recieve_events(order_events)
print(f"After adding order events: {warren.get_consumer_count()}")

# Add payment event consumers
warren.recieve_events(payment_events)
print(f"Total consumers: {warren.get_consumer_count()}")
```

### Different Exchange Types

```python
class TopicEvent(BaseReceivedEvent):
    EXCHANGE = "topic_exchange"
    TOPIC = "event.#"  # Wildcard pattern
    EXCHANGE_TYPE = ExchangeType.topic

class DirectEvent(BaseReceivedEvent):
    EXCHANGE = "direct_exchange"
    TOPIC = "specific_event"
    EXCHANGE_TYPE = ExchangeType.direct

class FanoutEvent(BaseReceivedEvent):
    EXCHANGE = "fanout_exchange"
    TOPIC = ""  # Not used in fanout
    EXCHANGE_TYPE = ExchangeType.fanout

warren.recieve_events([TopicEvent, DirectEvent, FanoutEvent])
```

### Combining with Traditional Consumption

```python
# Traditional callback-based consumption
def legacy_handler(channel, method, properties, body):
    print(f"Legacy message: {body.decode()}")

# Set up both traditional and event-based consumers
warren.start_consuming(legacy_handler)  # Creates 1 consumer
warren.recieve_events([UserLoginEvent, OrderCreatedEvent])  # Adds 2 more

print(f"Total consumers: {warren.get_consumer_count()}")  # Shows: 3
```

8. Consumer Management
----------------------

### Monitoring Consumers

```python
# Check number of active consumers
count = warren.get_consumer_count()
print(f"Active consumers: {count}")

# Get connection info
info = warren.get_connection_info()
print(f"Mode: {info['mode']}, Has channel: {info['has_channel']}")
```

### Stopping Consumers

```python
# Stop all consumers (both traditional and event-based)
warren.stop_consuming()
print(f"Consumers after stop: {warren.get_consumer_count()}")  # Shows: 0

# Warren tracks consumer tags internally
# All consumers are properly cancelled when stop_consuming() is called
```

### Consumer Tags

Each event class gets its own unique consumer tag for independent management:

```python
# Internal tracking (for reference - you don't access this directly)
# warren._consumer_tags contains all event-based consumer tags
# warren._consumer_tag contains the traditional consumer tag

# You interact through the public API:
warren.get_consumer_count()  # Total count
warren.stop_consuming()      # Stop all consumers
```

9. Best Practices
------------------

### Event Class Design

```python
class WellDesignedEvent(BaseReceivedEvent):
    EXCHANGE = "my_domain_events"
    TOPIC = "my_domain.specific_action"
    EXCHANGE_TYPE = ExchangeType.topic  # Explicit is better than implicit
    
    def processes_event(self) -> None:
        try:
            # Always validate data
            if not self.data:
                self.logger.warning("Received empty event data")
                return
            
            # Use get() with defaults for safety
            entity_id = self.data.get('id', 'unknown')
            action = self.data.get('action', 'unknown')
            
            # Log for debugging
            self.logger.info(f"Processing {action} for entity {entity_id}")
            
            # Your business logic here
            self._handle_business_logic()
            
        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            # Don't re-raise unless you want the message to be redelivered
    
    def _handle_business_logic(self) -> None:
        # Separate business logic for better testing
        pass
```

### Error Handling

```python
# Always use try-catch in processes_event()
def processes_event(self) -> None:
    try:
        # Your event processing logic
        self._do_processing()
    except ValueError as e:
        self.logger.error(f"Validation error: {e}")
        # Don't re-raise for invalid data - acknowledge the message
    except Exception as e:
        self.logger.error(f"Unexpected error: {e}")
        # Re-raise to trigger message redelivery if needed
        raise
```

### Resource Management

```python
# Always ensure proper cleanup
try:
    warren.connect()
    warren.recieve_events(event_classes)
    warren.start_io_loop()
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    warren.stop_consuming()
    warren.stop_io_loop()
    warren.disconnect()
```

10. Troubleshooting
-------------------

### Common Issues and Solutions

**Issue: Event classes not being processed**
- Ensure EXCHANGE and TOPIC attributes are defined and non-empty
- Check that classes inherit from BaseReceivedEvent
- Verify Warren is in 'consumer' mode
- Confirm processes_event() method is implemented

**Issue: Some events not received**
- Verify exchange types match message routing expectations
- Check topic patterns for wildcards (# and *)
- Ensure queues are properly bound to exchanges
- Monitor consumer tags with get_consumer_count()

**Issue: Consumer tags not cleaned up**
- Always call stop_consuming() when shutting down
- Check that all consumer tags are cancelled
- Monitor active consumers with get_consumer_count()

**Issue: Memory/performance problems**
- Tune prefetch_count for consumers
- Monitor queue depths
- Use appropriate exchange types
- Consider batching if processing many events

### Debugging Code

```python
# Enable debug logging
from bunnystream import configure_bunny_logger
configure_bunny_logger(level="DEBUG")

# Check Warren status
info = warren.get_connection_info()
print(f"Warren status: {info}")

# Monitor consumers
print(f"Consumer count: {warren.get_consumer_count()}")

# Test event class validation
try:
    warren.recieve_events([YourEventClass])
    print("✅ Event class validation passed")
except ValueError as e:
    print(f"❌ Event class validation failed: {e}")
```

11. Examples
------------

### Real-World E-commerce Example

```python
from bunnystream import Warren, BunnyStreamConfig, BaseReceivedEvent
from pika.exchange_type import ExchangeType
import json

class UserRegisteredEvent(BaseReceivedEvent):
    EXCHANGE = "user_events"
    TOPIC = "user.registered"
    EXCHANGE_TYPE = ExchangeType.topic
    
    def processes_event(self) -> None:
        user_id = self.data.get('user_id')
        email = self.data.get('email')
        self.logger.info(f"New user registered: {email} (ID: {user_id})")
        # Send welcome email, create user profile, etc.

class OrderPlacedEvent(BaseReceivedEvent):
    EXCHANGE = "order_events"
    TOPIC = "order.placed"
    EXCHANGE_TYPE = ExchangeType.direct
    
    def processes_event(self) -> None:
        order_id = self.data.get('order_id')
        customer_id = self.data.get('customer_id')
        total = self.data.get('total', 0)
        self.logger.info(f"Order {order_id} placed by customer {customer_id} for ${total}")
        # Process payment, update inventory, send confirmation

class PaymentProcessedEvent(BaseReceivedEvent):
    EXCHANGE = "payment_events"
    TOPIC = "payment.processed"
    EXCHANGE_TYPE = ExchangeType.topic
    
    def processes_event(self) -> None:
        payment_id = self.data.get('payment_id')
        order_id = self.data.get('order_id')
        amount = self.data.get('amount', 0)
        self.logger.info(f"Payment {payment_id} processed for order {order_id}: ${amount}")
        # Update order status, trigger fulfillment

class SystemAlertEvent(BaseReceivedEvent):
    EXCHANGE = "system_events"
    TOPIC = "system.alert"
    EXCHANGE_TYPE = ExchangeType.fanout
    
    def processes_event(self) -> None:
        level = self.data.get('level', 'info')
        message = self.data.get('message', 'No message')
        component = self.data.get('component', 'unknown')
        self.logger.warning(f"System alert [{level}] from {component}: {message}")
        # Send notifications, trigger monitoring alerts

# Application setup
if __name__ == "__main__":
    # Configure logging
    configure_bunny_logger(level="INFO")
    
    # Set up Warren
    config = BunnyStreamConfig(mode="consumer")
    warren = Warren(config)
    
    try:
        # Connect to RabbitMQ
        warren.connect()
        
        # Set up all event consumers
        event_classes = [
            UserRegisteredEvent,
            OrderPlacedEvent,
            PaymentProcessedEvent,
            SystemAlertEvent
        ]
        
        warren.recieve_events(event_classes)
        
        print(f"Started consuming {warren.get_consumer_count()} event types")
        print("Press Ctrl+C to stop...")
        
        # Start processing events
        warren.start_io_loop()
        
    except KeyboardInterrupt:
        print("\\nShutting down gracefully...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        warren.stop_consuming()
        warren.stop_io_loop()
        warren.disconnect()
        print("Shutdown complete")
```

### Microservices Integration Example

```python
class ServiceHealthEvent(BaseReceivedEvent):
    EXCHANGE = "service_mesh"
    TOPIC = "health.#"  # Matches health.check, health.degraded, etc.
    EXCHANGE_TYPE = ExchangeType.topic
    
    def processes_event(self) -> None:
        service_name = self.data.get('service')
        status = self.data.get('status')
        timestamp = self.data.get('timestamp')
        
        if status == 'unhealthy':
            self.logger.error(f"Service {service_name} is unhealthy at {timestamp}")
            # Trigger alerts, update service registry
        else:
            self.logger.debug(f"Service {service_name} status: {status}")

class LogAggregationEvent(BaseReceivedEvent):
    EXCHANGE = "logging"
    TOPIC = "log.error"
    EXCHANGE_TYPE = ExchangeType.direct
    
    def processes_event(self) -> None:
        service = self.data.get('service')
        level = self.data.get('level')
        message = self.data.get('message')
        
        # Aggregate logs, detect patterns, send to monitoring
        self.logger.info(f"Aggregating {level} log from {service}: {message}")

# Use in multiple microservices
warren.recieve_events([ServiceHealthEvent, LogAggregationEvent])
```

This completes the comprehensive documentation for the Warren.recieve_events() method!
"""
