# Multi-Topic Warren Demo

This demo shows how to use BunnyStream's Warren class to:

1. **Set up a consumer that listens to multiple topics** 
2. **Set up a producer that publishes events to multiple topics**
3. **Handle different event types with specific routing**

The demo simulates a simple e-commerce system with different business domains:
- **Order events**: `order.created`, `order.updated`, `order.cancelled`
- **User events**: `user.registered`, `user.updated`  
- **Product events**: `product.created`, `product.updated`

## Features Demonstrated

### Multi-Topic Consumer
- Configures a Warren consumer to listen to multiple topic patterns (`order.*`, `user.*`, `product.*`)
- Uses a single message handler that processes different event types
- Shows how to route different messages based on their topic/routing key
- Demonstrates proper message acknowledgment

### Multi-Topic Producer
- Creates specific event classes for different business domains
- Publishes events to different topics using the same exchange
- Shows how to structure event data with metadata
- Demonstrates the event serialization and messaging

### Event Classes
The demo defines several event classes that inherit from `BaseEvent`:
- `OrderCreatedEvent`, `OrderUpdatedEvent`, `OrderCancelledEvent`
- `UserRegisteredEvent`, `UserUpdatedEvent`
- `ProductCreatedEvent`, `ProductUpdatedEvent`

Each event class has:
- A predefined `TOPIC` (routing key)
- A predefined `EXCHANGE` name
- Custom data fields relevant to that event type

## Usage

### Running the Demo

```bash
python examples/multi_topic_demo.py
```

The script will present three options:
1. **Start Consumer** - Sets up a consumer that listens to multiple topics
2. **Run Producer** - Publishes events to multiple topics
3. **Run Both** - Runs producer first, then consumer

### With RabbitMQ

To run the demo with a real RabbitMQ server:

1. **Install RabbitMQ** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install rabbitmq-server
   
   # macOS with Homebrew
   brew install rabbitmq
   
   # Or use Docker
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
   ```

2. **Start RabbitMQ**:
   ```bash
   sudo systemctl start rabbitmq-server
   # or
   brew services start rabbitmq
   # or if using Docker, the container should already be running
   ```

3. **Run the demo** - the script will connect to RabbitMQ and demonstrate real message publishing/consuming

### Without RabbitMQ

If RabbitMQ is not running, the demo will:
- Show what the configuration would look like
- Display the JSON structure of the events that would be published
- Provide helpful information about setting up RabbitMQ

## Code Structure

### Consumer Setup
```python
# Create consumer config
consumer_config = BunnyStreamConfig(
    mode="consumer",
    rabbit_host="localhost",
    rabbit_port=5672,
    exchange_name="ecommerce_events"
)

# Add multiple topic subscriptions
subscriptions = [
    Subscription(exchange_name="ecommerce_events", topic="order.*"),
    Subscription(exchange_name="ecommerce_events", topic="user.*"),
    Subscription(exchange_name="ecommerce_events", topic="product.*")
]

for subscription in subscriptions:
    consumer_config.add_subscription(subscription)

consumer = Warren(consumer_config)
consumer.connect()
consumer.start_consuming(message_handler)
```

### Producer Setup
```python
# Create producer config
producer_config = BunnyStreamConfig(
    mode="producer",
    rabbit_host="localhost",
    rabbit_port=5672,
    exchange_name="ecommerce_events"
)

producer = Warren(producer_config)
producer.connect()

# Create and publish events
order_event = OrderCreatedEvent(
    warren=producer,
    order_id="ORD-12345",
    customer_id="CUST-67890",
    total=99.99,
    items_count=3
)
order_event.fire()  # Publishes to topic "order.created"
```

### Event Classes
```python
class OrderCreatedEvent(BaseEvent):
    TOPIC = "order.created"
    EXCHANGE = "ecommerce_events"
    
    def __init__(self, warren: Warren, order_id: str, customer_id: str, **kwargs):
        super().__init__(warren, **kwargs)
        self.data.update({
            'event_type': 'order.created',
            'order_id': order_id,
            'customer_id': customer_id
        })
```

## Message Flow

1. **Producer** creates events and publishes them to specific topics:
   - `order.created` → OrderCreatedEvent
   - `user.registered` → UserRegisteredEvent  
   - `product.updated` → ProductUpdatedEvent
   - etc.

2. **Consumer** subscribes to topic patterns and receives all matching messages:
   - `order.*` pattern catches all order events
   - `user.*` pattern catches all user events
   - `product.*` pattern catches all product events

3. **Message Handler** processes each message based on its routing key and event type

## Key Concepts Demonstrated

- **Topic-based routing**: Using RabbitMQ's topic exchange with wildcard patterns
- **Event-driven architecture**: Publishing domain events for different business operations
- **Multi-topic consumption**: Single consumer handling multiple event types
- **Event serialization**: Converting Python objects to JSON for messaging
- **Error handling**: Graceful handling of connection failures
- **Configuration management**: Setting up Warren for different modes (producer/consumer)

This demo provides a comprehensive example of how to build event-driven applications using BunnyStream's Warren class with multiple topics and proper separation of concerns.
