from tasks.base import BaseEventTask
from tasks.pipeline.automate import AutomateSelectedTeamsNotificationTask
from utils.schema import TaskResponse, Payload
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
        

class SendSelectedTeamsNotificationTask(BaseEventTask):
    name = "task.pipeline.selected_teams_notification"
    
    class TaskPayload(Payload):
        data: AutomateSelectedTeamsNotificationTask.TaskPayload.DataModel
        
    def validate(self, event):
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as exc:
            logger.error(f"Validation error in {self.name}: {exc}")
            return False
        
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Sending select notification mail to {self.payload.data.name}")
        
        mailerClient.send_selected_team_notification(
            to_email=self.payload.data.email,
            subject=f"Congratulations! Your team has been selected for the final round of Hackfest",
            team_name=self.payload.data.team_name,
            track=self.payload.data.track,
            is_leader=self.payload.data.is_leader
        )
            
        logger.info(f"Selected team notification sent to {self.payload.data.name}")        
        return TaskResponse(
            success=True,
            message=f"elected team notification sent to {self.payload.data.name}.",
            payload=self.payload.model_dump()
        )