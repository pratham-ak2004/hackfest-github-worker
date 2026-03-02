from tasks import BaseEventTask
from utils.schema import Payload, TeamPayload, TaskResponse
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
            self.payload = self.TaskPayload(event)
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