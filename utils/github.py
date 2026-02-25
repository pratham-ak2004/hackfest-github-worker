from config.setttings import settings
from email.utils import parsedate_to_datetime
from utils.typing import HttpMethod, GithubMetaData

import requests, time

class GithubClient:    
    def __init__(self, token=None) -> None:
        if token is None:
            raise ValueError("GitHub token must be provided")
        
        self.token = token
        self.api_url = "https://api.github.com"
        self._github_api_version = "2022-11-28"
        
        self._server_time = None
        self._local_time = None
        self._limit = 0
        self._remaining = 0
        self._reset = 0
        
        self.year = 26
        self.org_name = "hackfest-dev"
        
        self.rate_limit()
        
    def _update_rate_limit(self, response: requests.Response) -> None:
        """Update the rate limit information based on the response headers"""
        
        self._limit = int(response.headers.get("X-RateLimit-Limit", 0))
        self._remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        self._reset = int(response.headers.get("X-RateLimit-Reset", 0))
        self._server_time = int(parsedate_to_datetime(response.headers.get("Date")).timestamp())
        self._local_time = int(time.time())
        
    def _make_request(self, endpoint: str, method: HttpMethod, headers: dict, payload: dict = None) -> requests.Response:
        endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        response = requests.request(method, f"{self.api_url}{endpoint}", headers=headers, json=payload)
        self._update_rate_limit(response)
        return response
        
    def get_rate_limit_info(self) -> GithubMetaData:
        """Get the current rate limit information"""
        
        return GithubMetaData(
            limit=self._limit,
            remaining=self._remaining,
            reset=GithubMetaData.TimeMeta(
                timestamp=self._reset,
                readable=time.ctime(self._reset)
            ),
            server_time=GithubMetaData.TimeMeta(
                timestamp=self._server_time,
                readable=time.ctime(self._server_time)
            ),
            local_time=GithubMetaData.TimeMeta(
                timestamp=self._local_time,
                readable=time.ctime(self._local_time)
            )
        )
        
    def rate_limit(self) -> requests.Response:
        """Fetch the current rate limit status from GitHub API"""
        route = "/rate_limit"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-Github-Api-Version": self._github_api_version
        }
        return self._make_request(route, HttpMethod.GET, headers)