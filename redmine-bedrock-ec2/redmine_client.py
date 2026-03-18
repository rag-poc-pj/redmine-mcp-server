"""
Redmine API クライアント
EC2のIPでRedmineに接続する
"""
import httpx
from typing import Optional


class RedmineClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json",
        }

    def get_issues(
        self,
        project_id: Optional[str] = None,
        status_id: str = "open",
        limit: int = 25,
    ) -> dict:
        params = {"limit": limit, "status_id": status_id}
        if project_id:
            params["project_id"] = project_id

        with httpx.Client(timeout=30.0, verify=False) as client:
            response = client.get(
                f"{self.base_url}/issues.json",
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    def get_projects(self, limit: int = 25) -> dict:
        with httpx.Client(timeout=30.0, verify=False) as client:
            response = client.get(
                f"{self.base_url}/projects.json",
                headers=self.headers,
                params={"limit": limit},
            )
            response.raise_for_status()
            return response.json()

    def get_issue(self, issue_id: int) -> dict:
        with httpx.Client(timeout=30.0, verify=False) as client:
            response = client.get(
                f"{self.base_url}/issues/{issue_id}.json",
                headers=self.headers,
                params={"include": "journals,attachments"},
            )
            response.raise_for_status()
            return response.json()
