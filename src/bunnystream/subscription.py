from dataclasses import dataclass, field

from pika.exchange_type import ExchangeType


@dataclass
class Subscription:
    """
    Represents a subscription to a message exchange.

    Attributes:
        exchange_name (str): The name of the exchange to subscribe to.
        exchange_type (pika.exchange_type.ExchangeType): The type of the exchange (default is ExchangeType.topic).
        topics (list[str]): A list of topics to subscribe to (default is an empty list).
    """

    exchange_name: str
    exchange_type: ExchangeType = ExchangeType.topic
    topics: list[str] = field(default_factory=list)
