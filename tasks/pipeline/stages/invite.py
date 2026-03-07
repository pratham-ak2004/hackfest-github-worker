from tasks.base import BaseEventTask
from utils.logger import get_logger
from utils.schema import Payload, TeamDetails, TeamMember, TaskResponse
from pydantic import BaseModel
from utils.github import inviteClient
from utils.tasks import taskClient

logger = get_logger(__name__)

class SendOrgInviteTask(BaseEventTask):
    name = "task.pipeline.send_invite"
    
    class TaskPayload(Payload):
        class DataModel(BaseModel):
            team: TeamDetails
            member: TeamMember  
        data: DataModel
        
    def validate(self, event:dict) -> bool:
        try:
            self.payload = self.TaskPayload(**event)
            if self.payload.data.team.github_team is None or self.payload.data.team.github_repo is None:
                logger.error(f"GitHub team or repo not found for {self.payload.data.team.team_name}")
                raise ValueError("GitHub team and repo must be created before sending invites")
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Sending invite to {self.payload.data.member.name} for team {self.payload.data.team.team_name}")
        
        github_invite = inviteClient.send_team_invite(
            team_ids=[self.payload.data.team.github_team.id],
            username=self.payload.data.member.username,
            email=self.payload.data.member.email,
            user_id=self.payload.data.member.id
        )
        self.payload.data.member.github_invite = github_invite
        
        # send notification to user
        taskClient.create_invite_notification_task(self.payload.data)
        
        logger.info(f"Successfully sent invite to {self.payload.data.member.name}")
        return TaskResponse(
            success=True,
            message=f"Invite sent to {self.payload.data.member.name} for team {self.payload.data.team.team_name}.",
            payload=self.payload.model_dump()
        )

# Requires Administration scope in GitHub App
# Warning: Possesses security vurnerability
class AcceptOrgInviteTask(BaseEventTask):
    name = "task.pipeline.accept_invite"
    
    class TaskPayload(Payload):
        class DataModel(BaseModel):
            team: TeamDetails
            member: TeamMember
        data: DataModel
        
    def validate(self, event:dict) -> bool:
        try:
            self.payload = self.TaskPayload(**event)
            if self.payload.data.member.github_invite is None:
                logger.error(f"GitHub invite not found for member {self.payload.data.member.name}")
                raise ValueError("GitHub invite must be sent before accepting")
            if self.payload.data.member.credential is None:
                logger.error(f"GitHub credentials not found for member {self.payload.data.member.name}")
                raise ValueError("GitHub credentials must be provided to accept invite")
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
        
    def process(self, event: TaskPayload) -> TaskResponse:
        logger.info(f"Accepting invite for {self.payload.data.member.name}")
        
        # TODO: implement invite acceptance logic using inviteClient
        # inviteClient.accept_team_invite(self.payload.data.member.github_invite.id)
        raise NotImplementedError("Invite acceptance logic not implemented yet")
        
        # logger.info(f"Successfully accepted invite for {self.payload.data.member.name}")
        # return TaskResponse(
        #     success=True,
        #     message=f"Invite accepted for {self.payload.data.member.name} to join team {self.payload.data.team.team_name}.",
        #     payload=self.payload.model_dump()
        # )