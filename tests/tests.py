import json, os, pika
import sys
from dotenv import load_dotenv
from uuid import uuid7
from config import settings

load_dotenv()

from tasks.pipeline.automate import AutomateSelectedTeamsNotificationTask, AutomateGithubTask

json_path = os.getenv("DATA_PATH")

connection = pika.BlockingConnection(
    pika.URLParameters(
        f"amqp://{settings.RABBITMQ_USERNAME}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/%2F"
    )
)
channel = connection.channel()
channel.queue_declare(queue=settings.EVENT_QUEUE, durable=True)

def send_task(task_name: str, payload: dict, validator: callable) -> None:
    channel.basic_publish(
        exchange="",
        routing_key=settings.EVENT_QUEUE,
        body=json.dumps({
            "id": str(uuid7()),
            "task": task_name,
            "args": [validator(**payload).model_dump()],
        }).encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json"
        )
    )

def test_notification():
    data = json.load(open(os.path.join(json_path, "notification.json")))
    send_task(AutomateSelectedTeamsNotificationTask.name, data, AutomateSelectedTeamsNotificationTask.TaskPayload)
    
def test_automate():
    data = json.load(open(os.path.join(json_path, "team.json")))
    send_task(AutomateGithubTask.name, data, AutomateGithubTask.TaskPayload)