from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from faststream.rabbit.schemas.constants import ExchangeType
from faststream.rabbit.schemas.queue import QueueType

from core.config import config

PAYMENTS_EXCHANGE_NAME = "payments.events"
PAYMENTS_NEW_ROUTING_KEY = "payments.new"
PAYMENTS_DLQ_ROUTING_KEY = "payments.new.dlq"

broker = RabbitBroker(config.rabbitmq.url)
app = FastStream(broker)

payments_exchange = RabbitExchange(
    name=PAYMENTS_EXCHANGE_NAME,
    type=ExchangeType.TOPIC,
    durable=True,
)
payments_queue = RabbitQueue(
    name="payments.new",
    queue_type=QueueType.QUORUM,
    durable=True,
    routing_key=PAYMENTS_NEW_ROUTING_KEY,
    arguments={
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": PAYMENTS_DLQ_ROUTING_KEY,
    },
)

payments_retry_queues = [
    RabbitQueue(
        name=f"payments.new.retry.{attempt}",
        queue_type=QueueType.QUORUM,
        durable=True,
        routing_key=f"payments.new.retry.{attempt}",
        arguments={
            "x-message-ttl": ttl,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": PAYMENTS_NEW_ROUTING_KEY,
        },
    )
    for attempt, ttl in ((2, 1_000), (3, 2_000))
]

payments_dlq = RabbitQueue(
    name="payments.new.dlq",
    queue_type=QueueType.QUORUM,
    durable=True,
    routing_key=PAYMENTS_DLQ_ROUTING_KEY,
)


async def declare_topology() -> None:
    await broker.declare_exchange(payments_exchange)
    await broker.declare_queue(payments_queue)
    await broker.declare_queue(payments_dlq)
    for queue in payments_retry_queues:
        await broker.declare_queue(queue)
