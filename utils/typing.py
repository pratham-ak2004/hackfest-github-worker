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
