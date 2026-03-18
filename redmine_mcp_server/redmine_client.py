"""
Redmine REST API クライアント
"""
import httpx
from typing import Any, Optional


class RedmineClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, url, headers=self.headers, params=params, json=json
            )
            if response.status_code == 204:
                return None
            if not response.is_success:
                raise Exception(
                    f"Redmine API Error [{response.status_code}]: {response.text}"
                )
            return response.json()

    # ─── Issues ───────────────────────────────────────────────

    async def get_issues(
        self,
        project_id: Optional[str] = None,
        status_id: Optional[str] = None,
        assigned_to_id: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> dict:
        params: dict = {"limit": limit, "offset": offset}
        if project_id:
            params["project_id"] = project_id
        if status_id:
            params["status_id"] = status_id
        if assigned_to_id:
            params["assigned_to_id"] = assigned_to_id
        if subject:
            params["subject"] = f"~{subject}"
        return await self._request("GET", "/issues.json", params=params)

    async def get_issue(self, issue_id: int) -> dict:
        return await self._request(
            "GET", f"/issues/{issue_id}.json",
            params={"include": "journals,attachments"}
        )

    async def create_issue(self, data: dict) -> dict:
        return await self._request("POST", "/issues.json", json={"issue": data})

    async def update_issue(self, issue_id: int, data: dict) -> None:
        await self._request("PUT", f"/issues/{issue_id}.json", json={"issue": data})

    async def add_comment(self, issue_id: int, notes: str) -> None:
        await self._request(
            "PUT", f"/issues/{issue_id}.json", json={"issue": {"notes": notes}}
        )

    # ─── Projects ─────────────────────────────────────────────

    async def get_projects(self, limit: int = 25, offset: int = 0) -> dict:
        return await self._request(
            "GET", "/projects.json", params={"limit": limit, "offset": offset}
        )
