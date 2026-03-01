from tasks import BaseEventTask
from utils.schema import Payload, TeamPayload
from utils.tasks import taskClient
from utils.logger import get_logger

logger = get_logger(__name__)

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
    
    def process(self, event):
        logger.info(f"Processing event for task {self.name}")
        
        for team in self.payload.data:
            taskClient.create_team_task(team)
        
        return {
            "success": True,
            "message": f"Processed {len(self.payload.data)} team payloads for GitHub automation.",
            "payload": self.payload.data
        }