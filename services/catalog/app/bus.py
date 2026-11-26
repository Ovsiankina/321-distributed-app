"""Consommation de catalog.video-uploaded. Démarre seulement si CATALOG_AMQP_URL est défini."""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone

from .db import SessionLocal
from .events import ingest_uploaded


def amqp_url() -> str:
    return os.environ.get("CATALOG_AMQP_URL", "").strip()


async def consume_uploaded() -> None:
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
    queue = await channel.declare_queue("catalog.video-uploaded", durable=True)
    await queue.bind(exchange, routing_key="video.uploaded")

    async def publish(kind: str, data: dict) -> None:
        event_id = str(uuid.uuid4())
        body = {
            "event_id": event_id,
            "type": kind,
            "occurred_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "data": data,
        }
        confirm = await connection.channel(publisher_confirms=True)
        topic = await confirm.declare_exchange(
            "stream321.events", aio_pika.ExchangeType.TOPIC, durable=True
        )
        await topic.publish(
            aio_pika.Message(
                body=json.dumps(body).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=event_id,
            ),
            routing_key=kind,
        )

    async with queue.iterator() as messages:
        async for message in messages:
            try:
                payload = json.loads(message.body)
            except json.JSONDecodeError:
                await message.reject(requeue=False)
                continue
            pending: list[tuple[str, dict]] = []
            db = SessionLocal()
            try:
                await asyncio.to_thread(
                    ingest_uploaded,
                    db,
                    payload,
                    lambda kind, data: pending.append((kind, data)),
                )
                for kind, data in pending:
                    await publish(kind, data)
                await message.ack()
            except Exception:
                await message.nack(requeue=True)
            finally:
                db.close()
