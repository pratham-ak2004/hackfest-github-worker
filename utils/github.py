from config import settings
from email.utils import parsedate_to_datetime
from utils.schema import HttpMethod, GithubMetaData, GithubTeam, GithubRepository, GithubInvitation
from typing import Optional
from utils.locks import github_lock

import requests, time

# Fine-grained Permissions: Administration(organization, repository), Members(organization)
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
        self._username_cache = {}
        
        self.year = 26
        self.org_name = settings.GITHUB_ORG
        
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
        with github_lock:
            response = requests.request(method, f"{self.api_url}{endpoint}", headers=headers, json=payload)
        self._update_rate_limit(response)
        return response
    
    # TODO: Implement request and caching
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-Github-Api-Version": self._github_api_version
        }
        
    def _get_user_id(self, username: str) -> int:
        """Get the GitHub user ID for the specified username"""
        
        if username in self._username_cache:
            return self._username_cache[username]
        
        route = "/users/" + username
        headers = self._get_headers()
        response = self._make_request(route, HttpMethod.GET, headers)
        response.raise_for_status()
        
        user_id = int(response.json().id)
        self._username_cache[username] = user_id
        
        return user_id
    
    def generate_team_name(self, team_no: int, team_name: Optional[str] = None) -> str:
        return f"HF{self.year}-T{team_no:02d}{f'-{team_name}' if team_name else ''}"
    
    def generate_repo_name(self, team_no: int) -> str:
        return f"HF{self.year}-{team_no:02d}"
        
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
        headers = self._get_headers()
        response = self._make_request(route, HttpMethod.GET, headers)
        response.raise_for_status()
        return response.json()
    
    def create_org_team(self,team_no: int, team_name: Optional[str] = None, permission: str = "push", privacy: str = "secret") -> GithubTeam:
        """Create a new team in the organization for the specified team number and name
        
        - `Note`: the team is `closed` by default, meaning everyone in the organization can view this team.
        - `Hack`: Use `secret` to make it visible only to ORG owners and team members.
        """
        
        payload = {
            "name": self.generate_team_name(team_no, team_name),
            "description": f"Hackfest{self.year} team for T{team_no:02d}{f' {team_name}' if team_name else ''}",
            "privacy": privacy,
            "permission": permission
        }
        headers = self._get_headers()
        
        response = self._make_request(f"/orgs/{self.org_name}/teams", HttpMethod.POST, headers, payload)
        response.raise_for_status()
        data = response.json()
        
        return GithubTeam(
            id=data["id"],
            name=data["name"],
            slug=data["slug"],
            url=data["url"],
            html_url=data["html_url"]
        )
    
    def create_team_repo(self, team_id: int, team_no: int, private: bool = True) -> GithubRepository:
        """Create a new repository for the specified Team"""
        
        payload = {
            "name": self.generate_repo_name(team_no),
            "description": f"Hackfest{self.year} repository for T{team_no:02d}",
            "private": "true" if private else "false",
            "team_id": team_id
        }
        headers = self._get_headers()
        
        response = self._make_request(f"/orgs/{self.org_name}/repos", HttpMethod.POST, headers, payload)
        response.raise_for_status()
        data = response.json()
        
        return GithubRepository(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            url=data["url"],
            html_url=data["html_url"]
        )
        
    def send_team_invite(self, team_ids: list[int], username: str, email: Optional[str] = None, user_id: Optional[int] = None) -> GithubInvitation:
        """Send an invite to the specified user to join the team"""
        
        payload = {
            "role": "direct_member",
            "team_ids": team_ids
        }
        if email is not None:
            payload["email"] = email
        else:
            if user_id is None:
                user_id = self._get_user_id(username)
                payload["invitee_id"] = user_id

        headers = self._get_headers()
        
        response = self._make_request(f"/orgs/{self.org_name}/invitations", HttpMethod.POST, headers, payload)
        
        data = response.json()
        if response.status_code == 422:
            errors = data.get("errors", [])
            if errors[0]["message"] == "A user with this email address is already a part of this organization":
                return GithubInvitation(
                    id=-1,
                    email=email,
                    created_at=time.ctime(),
                    invitation_teams_url=""
                )
        
        return GithubInvitation(
            id=data["id"],
            email=data["email"],
            created_at=data["created_at"],
            invitation_teams_url=data["invitation_teams_url"]
        )
        
    def update_repo_visibility(self, repo_owner: str, repo_name: str, private: bool) -> GithubRepository:
        """Update the visibility of the specified repository"""
        
        payload = {
            "private": private
        }
        headers = self._get_headers()
        
        response = self._make_request(f"/repos/{repo_owner}/{repo_name}", HttpMethod.PATCH, headers, payload)
        response.raise_for_status()
        data = response.json()
        
        return GithubRepository(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            url=data["url"],
            html_url=data["html_url"]
        )
        
    def update_team_permissions(self, org: str, team_slug: str, permission: str, privacy: str) -> GithubTeam:
        """Update the permissions of the specified team"""
        
        payload = {
            "permission": permission,
            "privacy": privacy
        }
        headers = self._get_headers()
        
        response = self._make_request(f"/orgs/{org}/teams/{team_slug}", HttpMethod.PATCH, headers, payload)
        response.raise_for_status()
        data = response.json()
        
        return GithubTeam(
            id=data["id"],
            name=data["name"],
            slug=data["slug"],
            url=data["url"],
            html_url=data["html_url"]
        )
        
        
orgClient = GithubClient(token=settings.GITHUB_ORG_TOKEN)
inviteClient = GithubClient(token=settings.GITHUB_INVITE_TOKEN)