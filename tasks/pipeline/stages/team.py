from tasks import BaseEventTask
from utils.schema import Payload, TeamPayload, TaskResponse
from utils.github import orgClient
from utils.tasks import taskClient
from utils.logger import get_logger

logger = get_logger(__name__)

class CreateTeamTask(BaseEventTask):
    name = "task.pipeline.create_team"
    
    class TaskPayload(Payload):
        data: TeamPayload
    
    def validate(self, event:dict) -> bool:
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Creating GitHub team for {self.payload.data.team_name}")
        
        githubTeam = orgClient.create_org_team(self.payload.data.team_no, self.payload.data.team_name)
        self.payload.data.github_team = githubTeam
        # follow up task
        taskClient.create_repo_task(self.payload.data)
                            
        logger.info(f"Successfully created GitHub team: {self.payload.data.team_name}")
        return TaskResponse(
            success=True,
            message=f"GitHub team {self.payload.data.team_name} created successfully.",
            payload=self.payload.model_dump()
        )
        