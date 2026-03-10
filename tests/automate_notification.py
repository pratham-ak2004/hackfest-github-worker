import json, os, pika
import sys
from uuid import uuid7
from config import settings

from tasks.pipeline.automate import AutomateSelectedTeamsNotificationTask

json_path = "/home/pathu/repos/hackfest-github/tests/json"

data = json.load(open(os.path.join(json_path, "notification.json")))

connection = pika.BlockingConnection(
    pika.URLParameters(
        f"amqp://{settings.RABBITMQ_USERNAME}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/%2F"
    )
)
channel = connection.channel()
channel.queue_declare(queue=settings.EVENT_QUEUE, durable=True)

def send_task(task_name: str, payload: dict) -> None:
    channel.basic_publish(
        exchange="",
        routing_key=settings.EVENT_QUEUE,
        body=json.dumps({
            "id": str(uuid7()),
            "task": task_name,
            "args": [AutomateSelectedTeamsNotificationTask.TaskPayload(**payload).model_dump()],
        }).encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json"
        )
    )

def run():
    send_task(AutomateSelectedTeamsNotificationTask.name, data)