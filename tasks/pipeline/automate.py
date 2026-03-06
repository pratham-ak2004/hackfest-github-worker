from tasks import BaseEventTask
from utils.schema import Payload, TeamPayload, TaskResponse, TeamMember, GithubRepoProperties
from utils.tasks import taskClient
from utils.logger import get_logger
from eventprocessor.celery_app import app

logger = get_logger(__name__)

def register_automate_github_task():
    from .stages import CreateTeamTask, CreateRepoTask, SendOrgInviteTask, SendInviteNotificationTask
    app.register_task(CreateTeamTask())
    app.register_task(CreateRepoTask())
    app.register_task(SendOrgInviteTask())
    app.register_task(SendInviteNotificationTask())
    
class AutomateGithubTask(BaseEventTask):
    name = "task.pipeline.automate.hackathon_github"
    
    class TaskPayload(Payload):
        data: list[TeamPayload]
    
    def validate(self, event):
        """Validate the incoming event data"""
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as exc:
            logger.error(f"Validation error in {self.name}: {exc}")
            return False
    
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Processing event for task {self.name}")
        
        for team in self.payload.data:
            taskClient.create_team_task(team)
        
        return TaskResponse(
            success=True,
            message=f"Processed {len(self.payload.data)} team payloads for GitHub automation.",
            payload=self.payload.data
        )
        
class AutomateSelectedTeamsNotificationTask(BaseEventTask):
    name = "task.pipeline.automate.selected_teams_notification"
    
    class TaskPayload(Payload):
        class DataModel(TeamMember):
            email: str
            is_leader: bool
            team_name: str
            track: str
        data: list[DataModel]
        
    def validate(self, event):
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as exc:
            logger.error(f"Validation error in {self.name}: {exc}")
            return False
    
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Processing event for task {self.name}")
        
        for member in self.payload.data:
            taskClient.create_selected_teams_notification_task(member)
        
        return TaskResponse(
            success=True,
            message=f"Processed {len(self.payload.data)} team payloads for selected teams notification.",
            payload=self.payload.data
        )
        
    
class AutomateRepoPropertiesUpdate(BaseEventTask):
    name = "task.pipeline.automate.update_repo_properties"
    
    class TaskPayload(Payload):
        data: list[GithubRepoProperties]
    
    def validate(self, event):
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as exc:
            logger.error(f"Validation error in {self.name}: {exc}")
            return False
    
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Processing event for task {self.name}")
        
        for repo in self.payload.data:
            if repo.toggle_visibility:
                taskClient.create_update_repo_task(repo)
            if repo.toggle_access:
                taskClient.create_update_team_task(repo)
        
        logger.info(f"Received {len(self.payload.data)} repo properties to update.")
        return TaskResponse(
            success=True,
            message=f"Processed {len(self.payload.data)} team payloads for toggling repo access.",
            payload=self.payload.data
        )