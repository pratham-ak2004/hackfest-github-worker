from pydantic import BaseModel, Field
from enum import Enum

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    
class TimeMeta(BaseModel):
    timestamp: int = Field(..., description="The timestamp in seconds since the epoch.")
    readable: str = Field(..., description="The human-readable representation of the time.")

class GithubMetaData(BaseModel):
    limit: int = Field(..., description="The total number of requests allowed in the current rate limit window.")
    remaining: int = Field(..., description="The number of requests remaining in the current rate limit window.")
    reset: TimeMeta = Field(..., description="The time at which the current rate limit window resets.")
    server_time: TimeMeta = Field(..., description="The current server time when the response was received.")
    local_time: TimeMeta = Field(..., description="The local time when the response was received.")

class GithubTeam(BaseModel):
    id: int = Field(..., description="The unique identifier of the GitHub team.")
    name: str = Field(..., description="The name of the GitHub team.")
    slug: str = Field(..., description="The slug (URL-friendly name) of the GitHub team.")
    url: str = Field(..., description="The API URL for the GitHub team.")
    html_url: str = Field(..., description="The HTML URL for the GitHub team.")
    
class GithubRepository(BaseModel):
    id: int = Field(..., description="The unique identifier of the GitHub repository.")
    name: str = Field(..., description="The name of the GitHub repository.")
    full_name: str = Field(..., description="The full name of the GitHub repository (including owner).")
    url: str = Field(..., description="The API URL for the GitHub repository.")
    html_url: str = Field(..., description="The HTML URL for the GitHub repository.")
    
class GithubInvitation(BaseModel):
    id: int = Field(..., description="The unique identifier of the GitHub invitation.")
    email: str = Field(..., description="The email address of the invitee.")
    created_at: str = Field(..., description="The timestamp when the invitation was created.")
    invitation_teams_url: str = Field(..., description="The API URL for the teams associated with the invitation.")