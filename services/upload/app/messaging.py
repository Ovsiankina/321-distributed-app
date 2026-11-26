"""Publication AMQP. Les tests remplacent publish_event."""

import json
import uuid
from datetime import datetime, timezone

from .config import amqp_url


class BrokerError(RuntimeError):
    pass


async def publish_event(event_type: str, data: dict) -> None:
    url = amqp_url()
    if not url:
        raise BrokerError("UPLOAD_AMQP_URL absent")
    import aio_pika

    event_id = str(uuid.uuid4())
    body = {
        "event_id": event_id,
        "type": event_type,
        "occurred_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": data,
    }
    connection = await aio_pika.connect_robust(url)
    try:
        channel = await connection.channel(publisher_confirms=True)
        exchange = await channel.declare_exchange(
            "stream321.events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(body).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=event_id,
            ),
            routing_key=event_type,
        )
    finally:
        await connection.close()
