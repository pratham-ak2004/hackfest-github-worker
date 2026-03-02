from tasks.base import BaseEventTask
from utils.schema import TaskResponse
from utils.logger import get_logger
from utils.tasks import mailerClient
from .invite import SendOrgInviteTask


logger = get_logger(__name__)

class SendInviteNotificationTask(BaseEventTask):
    name = "task.pipeline.send_invite_notification"
    
    class TaskPayload(SendOrgInviteTask.TaskPayload):
        pass
    
    def validate(self, event:dict) -> bool:
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def process(self, event) -> dict:
        logger.info(f"Sending notification to {self.payload.data.member.name}")

        mailerClient.send_invite_notification(
            to_email=self.payload.data.member.email,
            subject=f"You've been invited to join Hackfest Organization on GitHub",
            repository_name=self.payload.data.team.github_repo.name,
            repository_url=self.payload.data.team.github_repo.html_url
        )
        
        logger.info(f"Invite notification sent to {self.payload.data.member.name}")
        return TaskResponse(
            success=True,
            message=f"Invite notification sent to {self.payload.data.member.name}.",
            payload=self.payload.model_dump()
        )