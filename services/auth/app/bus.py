"""Consommation de auth.video-events. Démarre seulement si AUTH_AMQP_URL est défini."""

import json
import os

from .db import SessionLocal
from .events import apply_bus_event


def amqp_url() -> str:
    return os.environ.get("AUTH_AMQP_URL", "").strip()


async def consume_video_events() -> None:
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
    queue = await channel.declare_queue("auth.video-events", durable=True)
    await queue.bind(exchange, routing_key="video.published")
    await queue.bind(exchange, routing_key="video.removed")
    async with queue.iterator() as messages:
        async for message in messages:
            try:
                payload = json.loads(message.body)
            except json.JSONDecodeError:
                await message.reject(requeue=False)
                continue
            db = SessionLocal()
            try:
                apply_bus_event(db, payload)
                await message.ack()
            except Exception:
                await message.nack(requeue=True)
            finally:
                db.close()
