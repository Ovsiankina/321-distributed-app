"""Publication et consommation AMQP. Les tests remplacent publish_event."""

import json
import uuid
from datetime import datetime, timezone

from .compensate import delete_video_file
from .config import amqp_url, data_dir


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


def handle_rejected_payload(payload: dict) -> None:
    data = payload.get("data") if isinstance(payload, dict) else None
    video_id = data.get("video_id") if isinstance(data, dict) else None
    if isinstance(video_id, str):
        delete_video_file(data_dir(), video_id)


async def consume_rejected() -> None:
    url = amqp_url()
    if not url:
        return
    import aio_pika

    connection = await aio_pika.connect_robust(url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=5)
    exchange = await channel.declare_exchange(
        "stream321.events", aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue("media.video-rejected", durable=True)
    await queue.bind(exchange, routing_key="video.rejected")
    async with queue.iterator() as messages:
        async for message in messages:
            try:
                payload = json.loads(message.body)
            except json.JSONDecodeError:
                await message.reject(requeue=False)
                continue
            try:
                handle_rejected_payload(payload)
                await message.ack()
            except Exception:
                await message.nack(requeue=True)
