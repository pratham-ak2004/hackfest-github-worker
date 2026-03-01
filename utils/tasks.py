import pika
from config import settings
from utils.logger import get_logger
from utils.schema import TeamPayload, Payload
from uuid import uuid7

logger = get_logger(__name__)

class TaskClient:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(
                f"amqp://{settings.RABBITMQ_USERNAME}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/%2F"
                )
            )
        self.channel = self.connection.channel()
        self.queue = self.channel.queue_declare(queue=settings.EVENT_QUEUE, durable=True)
    
    def _send_task(self, task_name: str, payload: Payload) -> None:
        self.channel.basic_publish(
            exchange="",
            routing_key=settings.EVENT_QUEUE,
            body={
                "id": str(uuid7()),
                "task": task_name,
                "event": payload.model_dump(),
            }
        )
    
    def create_team_task(self, team_payload: TeamPayload) -> None:
        payload = Payload(data=team_payload)
        self._send_task("task.pipeline.create_team", payload)
        
    def create_repo_task(self, team_payload: TeamPayload) -> None:
        payload = Payload(data=team_payload)
        self._send_task("task.pipeline.create_repo", payload)
        

taskClient = TaskClient()