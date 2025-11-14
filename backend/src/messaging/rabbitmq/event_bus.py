import json
from aio_pika import Message, ExchangeType
from aio_pika.abc import AbstractRobustChannel

from src.messaging.abstractions import AbstractEventBus, BaseEvent


class RabbitMQEventBus(AbstractEventBus):
    def __init__(self, channel: AbstractRobustChannel, exchange_name: str):
        self.channel = channel
        self.exchange_name = exchange_name

    async def publish(self, routing_key: str, event: BaseEvent):
        exchange = await self.channel.declare_exchange(
            name=self.exchange_name,
            type=ExchangeType.TOPIC,
            durable=True
        )

        message_body = {
            "routing_key": routing_key,
            "event": event.model_dump(),
        }

        await exchange.publish(
            Message(
                body=json.dumps(message_body, default=str).encode(),
                content_type="application/json",
            ),
            routing_key=routing_key,
        )