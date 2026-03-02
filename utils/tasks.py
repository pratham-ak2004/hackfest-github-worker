import pika, smtplib, email, os
from config import settings
from utils.logger import get_logger
from utils.schema import TeamPayload, Payload
from tasks.pipeline.stages.invite import SendOrgInviteTask
from uuid import uuid7 ## using uuid7 for better db indexing performance
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

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
        
    def create_invite_task(self, member_payload: SendOrgInviteTask.TaskPayload.DataModel) -> None:
        payload = Payload(data=member_payload)
        self._send_task("task.pipeline.send_invite", payload)
        
    def create_invite_notification_task(self, member_payload: SendOrgInviteTask.TaskPayload.DataModel) -> None:
        payload = Payload(data=member_payload)
        self._send_task("task.pipeline.send_invite_notification", payload)
        
    
class MailerClient:        
    def __init__(self):
        self.smtp_session = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        self.smtp_session.starttls()
        self.smtp_session.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"])
        )
        
        self.templates = dict()
        template_list = ["invite"]
        for template_name in template_list:
            self.templates[template_name] = self.jinja_env.get_template(f"{template_name}.html")
        
    def _send_mail(self, to_email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        
        message["From"] = settings.SMTP_USER
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body, subtype="html")
        
        self.smtp_session.send_message(message)
        
    def send_invite_notification(self, to_email: str, subject: str, repository_url: str, repository_name: str) -> None:
        template = self.templates["invite"]
        html_content = template.render(
            subject=subject,
            repository_url=repository_url,
            repository_name=repository_name
        )
        self._send_mail(to_email=to_email, subject=subject, body=html_content)
        

taskClient = TaskClient()
mailerClient = MailerClient()