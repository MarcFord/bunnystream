"""
This module defines the Subscription dataclass, which encapsulates the configuration
for subscribing to a message exchange using the pika library. It allows specification
of the exchange name, exchange type, and a list of topics to subscribe to.

Classes:
    Subscription: Represents a subscription to a message exchange, including the
    exchange name, type, and topics of interest.
"""

from dataclasses import dataclass

from pika.exchange_type import ExchangeType  # type: ignore


@dataclass
class Subscription:
    """
    Represents a subscription to a message exchange.

    Attributes:
        exchange_name (str): The name of the exchange to subscribe to.
        exchange_type (pika.exchange_type.ExchangeType): The type of the exchange
                        (default is ExchangeType.topic).
        topic (str): A topic to subscribe to (default is an empty str).
    """

    exchange_name: str
    exchange_type: ExchangeType = ExchangeType.topic
    topic: str = ""
