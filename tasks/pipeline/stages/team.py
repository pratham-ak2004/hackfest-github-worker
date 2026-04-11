from tasks import BaseEventTask
from utils.schema import Payload, TeamPayload, TaskResponse, GithubRepoProperties
from utils.github import orgClient
from utils.tasks import taskClient
from utils.logger import get_logger
from config import settings

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
        # follow up task: create repo for team
        taskClient.create_repo_task(self.payload.data)
                            
        logger.info(f"Successfully created GitHub team: {self.payload.data.team_name}")
        return TaskResponse(
            success=True,
            message=f"GitHub team {self.payload.data.team_name} created successfully.",
            payload=self.payload.model_dump()
        )
        

class UpdateTeamTask(BaseEventTask):
    name = "task.pipeline.update_team"
    
    class TaskPayload(Payload):
        data: GithubRepoProperties
        
    def validate(self, event):
        try:
            self.payload = self.TaskPayload(**event)
            return True
        except Exception as e:
            logger.error(f"Validation error in {self.name}: {e}")
            return False
        
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Updating GitHub team for {self.payload.data.github_team.name}")
        
        github_team = orgClient.update_team_permissions(
            org=settings.GITHUB_ORG,
            owner=settings.GITHUB_ORG,
            team_slug=self.payload.data.team_slug,
            permission=self.payload.data.permission,
            repo=self.payload.data.repo
        )
        self.payload.data.github_team = github_team
        
        logger.info(f"Successfully updated GitHub team: {self.payload.data.github_team.name}")
        return TaskResponse(
            success=True,
            message=f"GitHub team {self.payload.data.github_team.name} updated successfully.",
            payload=self.payload.model_dump()
        )
        
        