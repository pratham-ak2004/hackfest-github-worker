from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel

# import logfire

# logfire.configure()
# logfire.instrument_pydantic()


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class TimeMeta(BaseModel):
    timestamp: int
    readable: str

class GithubUserCredential(BaseModel):
    access_token: str
    refresh_token: str
    
    
class GithubMetaData(BaseModel):
    limit: int
    remaining: int
    reset: TimeMeta
    server_time: TimeMeta
    local_time: TimeMeta


class GithubTeam(BaseModel):
    id: int
    name: str
    slug: str
    url: str
    html_url: str


class GithubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    url: str
    html_url: str


class GithubInvitation(BaseModel):
    id: int
    email: str
    created_at: str
    invitation_teams_url: str
    
class GithubRepoProperties(BaseModel):
    toggle_visibility: bool = False
    private: bool = True
    
    toggle_access: bool = False
    team_slug: str
    repo: str
    permission: str = "push" # pull, triage, push, maintain, admin
    
    github_repo: Optional[GithubRepository] = None
    github_team: Optional[GithubTeam] = None


class TeamMember(BaseModel):
    id: Optional[str] = None
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    github_invite: Optional[GithubInvitation] = None
    # credential: Optional[GithubUserCredential] = None


class TeamDetails(BaseModel):
    team_id: str
    team_no: int
    team_name: Optional[str] = None
    github_team: Optional[GithubTeam] = None
    github_repo: Optional[GithubRepository] = None


class TeamPayload(TeamDetails):
    members: list[TeamMember] = []
    

class Payload(BaseModel):
    data: Any
    
    
class TaskResponse(BaseModel):
    success: bool
    message: str
    payload: Optional[dict] = None