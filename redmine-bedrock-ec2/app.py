"""
FastAPI サーバー
EC2上で起動し、RedmineデータをBedrockで要約して返す
GenU Lambda からHTTP経由で呼び出す
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from redmine_client import RedmineClient
from bedrock_summarizer import BedrockSummarizer

app = FastAPI(title="Redmine Bedrock API", version="1.0.0")

# 環境変数から設定読み込み
REDMINE_URL = os.environ["REDMINE_URL"]
REDMINE_API_KEY = os.environ["REDMINE_API_KEY"]
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")

redmine = RedmineClient(base_url=REDMINE_URL, api_key=REDMINE_API_KEY)
summarizer = BedrockSummarizer(region=AWS_REGION)


# ─── リクエストモデル ──────────────────────────────────────────

class IssuesRequest(BaseModel):
    project_id: Optional[str] = None
    status_id: str = "open"
    limit: int = 25
    summarize: bool = True   # Bedrockで要約するか否か


class IssueDetailRequest(BaseModel):
    issue_id: int
    summarize: bool = True


# ─── エンドポイント ────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "redmine-bedrock-api"}


@app.post("/issues")
def get_issues(req: IssuesRequest):
    """チケット一覧を取得して要約"""
    try:
        result = redmine.get_issues(
            project_id=req.project_id,
            status_id=req.status_id,
            limit=req.limit,
        )
        issues = result.get("issues", [])

        response = {
            "total_count": result.get("total_count", 0),
            "issues": [
                {
                    "id": i["id"],
                    "subject": i["subject"],
                    "status": i["status"]["name"],
                    "priority": i["priority"]["name"],
                    "assigned_to": i.get("assigned_to", {}).get("name", "未割り当て"),
                    "due_date": i.get("due_date"),
                    "updated_on": i["updated_on"],
                }
                for i in issues
            ],
        }

        # Bedrockで要約
        if req.summarize and issues:
            response["summary"] = summarizer.summarize_issues(issues)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/issues/{issue_id}")
def get_issue_detail(issue_id: int, summarize: bool = True):
    """チケット詳細を取得して要約"""
    try:
        result = redmine.get_issue(issue_id)
        issue = result["issue"]

        response = {
            "id": issue["id"],
            "subject": issue["subject"],
            "status": issue["status"]["name"],
            "priority": issue["priority"]["name"],
            "description": issue.get("description", ""),
            "assigned_to": issue.get("assigned_to", {}).get("name", "未割り当て"),
            "due_date": issue.get("due_date"),
            "done_ratio": issue["done_ratio"],
            "comments": [
                {
                    "author": j["user"]["name"],
                    "notes": j["notes"],
                    "created_on": j["created_on"],
                }
                for j in issue.get("journals", [])
                if j.get("notes")
            ],
        }

        # Bedrockで要約
        if summarize:
            response["summary"] = summarizer.summarize_issue_detail(issue)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects")
def get_projects(limit: int = 25, summarize: bool = True):
    """プロジェクト一覧を取得して要約"""
    try:
        result = redmine.get_projects(limit=limit)
        projects = result.get("projects", [])

        response = {
            "total_count": result.get("total_count", 0),
            "projects": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "identifier": p["identifier"],
                    "status": "アクティブ" if p["status"] == 1 else "アーカイブ",
                }
                for p in projects
            ],
        }

        # Bedrockで要約
        if summarize and projects:
            response["summary"] = summarizer.summarize_projects(projects)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
