import pika, smtplib, email, os
from config import settings
from utils.logger import get_logger
from utils.schema import TeamPayload, Payload, GithubRepoProperties
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
        
    def create_invite_task(self, member_payload: dict) -> None:
        payload = Payload(data=member_payload)
        self._send_task("task.pipeline.send_invite", payload)
        
    def create_invite_notification_task(self, member_payload: dict) -> None:
        payload = Payload(data=member_payload)
        self._send_task("task.pipeline.send_invite_notification", payload)
        
    def create_selected_teams_notification_task(self, member_payload: dict) -> None:
        payload = Payload(data=member_payload)
        self._send_task("task.pipeline.selected_teams_notification", payload)
        
    def create_update_repo_task(self, repo_payload: GithubRepoProperties) -> None:
        payload = Payload(data=repo_payload)
        self._send_task("task.pipeline.update_repo", payload)
        
    def create_update_team_task(self, repo_payload: GithubRepoProperties) -> None:
        payload = Payload(data=repo_payload)
        self._send_task("task.pipeline.update_team", payload)
        
    
class MailerClient:        
    def __init__(self):
        self.smtp_session = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        self.smtp_session.starttls()
        self.smtp_session.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"])
        )
        
        self.templates = dict()
        template_list = ["invite", "selected_notification"]
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
        
    def send_selected_team_notification(self, to_email: str, subject: str, team_name: str, track: str, is_leader: bool) -> None:
        template = self.templates["selected_notification"]
        html_content = template.render(
            subject=subject,
            team_name=team_name,
            track=track,
            is_leader=is_leader
        )
        self._send_mail(to_email=to_email, subject=subject, body=html_content)
        

taskClient = TaskClient()
mailerClient = MailerClient()