from tasks.base import BaseEventTask
from utils.schema import Payload, TeamPayload
from utils.logger import get_logger
from utils.github import orgClient

logger = get_logger(__name__)

class CreateRepoTask(BaseEventTask):
    name = "task.pipeline.create_repo"
    
    class TaskPayload(Payload):
        data: TeamPayload
        
    def validate(self, event):
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def process(self, event):
        logger.info(f"Creating GitHub repository for {self.payload.data.team_name}")
        
        githubRepo = orgClient.create_team_repo(self.payload.data.github_team.id, self.payload.data.team_no)
        self.payload.data.github_repo = githubRepo
        
        # TODO: send invite task
        
        logger.info(f"Successfully created GitHub repository: {self.payload.data.github_repo.name}")
        return {
            "success": True,
            "message": f"GitHub repository {self.payload.data.team_name} created successfully.",
            "payload": self.payload.model_dump()
        }