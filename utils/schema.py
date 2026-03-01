from enum import Enum
from typing import Optional

from pydantic import BaseModel


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class TimeMeta(BaseModel):
    timestamp: int
    readable: str


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


class TeamMember(BaseModel):
    id: int
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    github_invite: Optional[GithubInvitation] = None


class TeamPayload(BaseModel):
    team_no: int
    team_name: Optional[str] = None
    members: list[TeamMember] = []
    
    github_team: Optional[GithubTeam] = None
    github_repo: Optional[GithubRepository] = None
    
class Payload(BaseModel):
    data: any