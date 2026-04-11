from tasks.base import BaseEventTask
from tasks.pipeline.stages.invite import SendOrgInviteTask
from utils.schema import Payload, TeamPayload, TaskResponse, TeamDetails, GithubRepoProperties
from utils.logger import get_logger
from utils.github import orgClient
from utils.tasks import taskClient

logger = get_logger(__name__)

class CreateRepoTask(BaseEventTask):
    name = "task.pipeline.create_repo"
    
    class TaskPayload(Payload):
        data: TeamPayload
        
    def validate(self, event):
        try:
            self.payload = self.TaskPayload(**event)
            if self.payload.data.github_team is None:
                logger.error(f"GitHub team not found for {self.payload.data.team_name}")
                raise ValueError("GitHub team must be created before creating repository")
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Creating GitHub repository for {self.payload.data.team_name}")
        
        githubRepo = orgClient.create_team_repo(self.payload.data.github_team.id, self.payload.data.team_no)
        self.payload.data.github_repo = githubRepo
        
        # Follow up task: send invites to team members
        for member in self.payload.data.members:
            logger.debug(f"Scheduling invite task for member {member.name} of team {self.payload.data.team_name}")
            taskClient.create_invite_task(SendOrgInviteTask.TaskPayload.DataModel(
                team=TeamDetails(
                    team_id=self.payload.data.team_id,
                    team_no=self.payload.data.team_no,
                    team_name=self.payload.data.team_name,
                    github_team=self.payload.data.github_team,
                    github_repo=self.payload.data.github_repo
                ),
                member=member
            ))
        
        logger.info(f"Successfully created GitHub repository: {self.payload.data.github_repo.name}")
        return TaskResponse(
            success=True,
            message=f"GitHub repository {self.payload.data.team_name} created successfully.",
            payload=self.payload.model_dump()
        )
        

class UpdateRepoTask(BaseEventTask):
    name = "task.pipeline.update_repo"
    
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
        logger.info(f"Updating GitHub repository properties for {self.payload.data.github_repo.name}")
        
        updatedRepo = orgClient.update_repo_visibility(
            repo_name=self.payload.data.github_repo.name,
            repo_owner=orgClient.org_name,
            private=self.payload.data.private
        )
        self.payload.data.github_repo = updatedRepo
        
        logger.info(f"Successfully updated GitHub repository: {self.payload.data.github_repo.name}")
        return TaskResponse(
            success=True,
            message=f"GitHub repository {self.payload.data.github_repo.name} updated successfully.",
            payload=self.payload.model_dump()
        )