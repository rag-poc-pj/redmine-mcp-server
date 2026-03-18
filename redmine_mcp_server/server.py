"""
MCP Server - Redmine ツール定義 (FastMCP)
"""
import json
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .redmine_client import RedmineClient

mcp = FastMCP("redmine-mcp-server")


def get_client() -> RedmineClient:
    url = os.environ.get("REDMINE_URL", "")
    key = os.environ.get("REDMINE_API_KEY", "")
    if not url or not key:
        raise ValueError("REDMINE_URL と REDMINE_API_KEY の環境変数が必要です")
    return RedmineClient(base_url=url, api_key=key)


# ─── Tool: チケット一覧取得・検索 ────────────────────────────

@mcp.tool()
async def get_issues(
    project_id: Optional[str] = None,
    status_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    subject: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> str:
    """
    Redmineのチケット(Issue)一覧を取得・検索します。

    Args:
        project_id: プロジェクトIDまたは識別子 (例: my-project)
        status_id: ステータスフィルタ (open / closed / *)
        assigned_to_id: 担当者のユーザーID (me で自分のチケット)
        subject: 件名の部分一致検索キーワード
        limit: 取得件数 (デフォルト: 25、最大: 100)
        offset: 取得開始位置 (ページネーション用)
    """
    client = get_client()
    result = await client.get_issues(
        project_id=project_id,
        status_id=status_id,
        assigned_to_id=assigned_to_id,
        subject=subject,
        limit=limit,
        offset=offset,
    )
    issues = [
        {
            "id": i["id"],
            "subject": i["subject"],
            "status": i["status"]["name"],
            "priority": i["priority"]["name"],
            "project": i["project"]["name"],
            "assigned_to": i.get("assigned_to", {}).get("name", "未割り当て"),
            "due_date": i.get("due_date", "未設定"),
            "done_ratio": i["done_ratio"],
            "updated_on": i["updated_on"],
        }
        for i in result.get("issues", [])
    ]
    return json.dumps(
        {"total_count": result.get("total_count", 0), "issues": issues},
        ensure_ascii=False,
        indent=2,
    )


# ─── Tool: チケット詳細取得 ───────────────────────────────────

@mcp.tool()
async def get_issue(issue_id: int) -> str:
    """
    Redmineの特定チケット(Issue)の詳細・コメント・添付ファイルを取得します。

    Args:
        issue_id: チケットID (例: 123)
    """
    client = get_client()
    result = await client.get_issue(issue_id)
    issue = result["issue"]
    data = {
        "id": issue["id"],
        "subject": issue["subject"],
        "description": issue.get("description", ""),
        "project": issue["project"]["name"],
        "status": issue["status"]["name"],
        "priority": issue["priority"]["name"],
        "tracker": issue["tracker"]["name"],
        "author": issue["author"]["name"],
        "assigned_to": issue.get("assigned_to", {}).get("name", "未割り当て"),
        "start_date": issue.get("start_date"),
        "due_date": issue.get("due_date"),
        "done_ratio": issue["done_ratio"],
        "created_on": issue["created_on"],
        "updated_on": issue["updated_on"],
        "comments": [
            {
                "id": j["id"],
                "author": j["user"]["name"],
                "notes": j["notes"],
                "created_on": j["created_on"],
            }
            for j in issue.get("journals", [])
            if j.get("notes")
        ],
        "attachments": [
            {
                "id": a["id"],
                "filename": a["filename"],
                "filesize": a["filesize"],
                "content_url": a["content_url"],
                "created_on": a["created_on"],
            }
            for a in issue.get("attachments", [])
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


# ─── Tool: チケット作成 ───────────────────────────────────────

@mcp.tool()
async def create_issue(
    project_id: str,
    subject: str,
    description: Optional[str] = None,
    tracker_id: Optional[int] = None,
    priority_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
    due_date: Optional[str] = None,
) -> str:
    """
    Redmineに新しいチケット(Issue)を作成します。

    Args:
        project_id: プロジェクトIDまたは識別子 (必須)
        subject: チケットの件名 (必須)
        description: チケットの詳細説明
        tracker_id: トラッカーID (1=バグ, 2=機能, 3=サポート等)
        priority_id: 優先度ID (1=低, 2=通常, 3=高, 4=急いで, 5=今すぐ)
        assigned_to_id: 担当者のユーザーID
        due_date: 期日 (YYYY-MM-DD形式)
    """
    client = get_client()
    data: dict = {"project_id": project_id, "subject": subject}
    if description is not None:
        data["description"] = description
    if tracker_id is not None:
        data["tracker_id"] = tracker_id
    if priority_id is not None:
        data["priority_id"] = priority_id
    if assigned_to_id is not None:
        data["assigned_to_id"] = assigned_to_id
    if due_date is not None:
        data["due_date"] = due_date

    result = await client.create_issue(data)
    issue = result["issue"]
    return json.dumps(
        {
            "message": "チケットを作成しました",
            "id": issue["id"],
            "subject": issue["subject"],
            "status": issue["status"]["name"],
            "project": issue["project"]["name"],
            "url": f"{os.environ.get('REDMINE_URL', '')}/issues/{issue['id']}",
        },
        ensure_ascii=False,
        indent=2,
    )


# ─── Tool: チケット更新 ───────────────────────────────────────

@mcp.tool()
async def update_issue(
    issue_id: int,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    status_id: Optional[int] = None,
    priority_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
    due_date: Optional[str] = None,
    done_ratio: Optional[int] = None,
) -> str:
    """
    Redmineの既存チケット(Issue)を更新します。

    Args:
        issue_id: 更新するチケットのID
        subject: 新しい件名
        description: 新しい詳細説明
        status_id: 新しいステータスID
        priority_id: 新しい優先度ID
        assigned_to_id: 新しい担当者のユーザーID
        due_date: 新しい期日 (YYYY-MM-DD形式)
        done_ratio: 進捗率 (0〜100)
    """
    client = get_client()
    data: dict = {}
    if subject is not None:
        data["subject"] = subject
    if description is not None:
        data["description"] = description
    if status_id is not None:
        data["status_id"] = status_id
    if priority_id is not None:
        data["priority_id"] = priority_id
    if assigned_to_id is not None:
        data["assigned_to_id"] = assigned_to_id
    if due_date is not None:
        data["due_date"] = due_date
    if done_ratio is not None:
        data["done_ratio"] = done_ratio

    await client.update_issue(issue_id, data)
    return json.dumps(
        {
            "message": f"チケット #{issue_id} を更新しました",
            "url": f"{os.environ.get('REDMINE_URL', '')}/issues/{issue_id}",
        },
        ensure_ascii=False,
        indent=2,
    )


# ─── Tool: コメント追加 ───────────────────────────────────────

@mcp.tool()
async def add_comment(issue_id: int, notes: str) -> str:
    """
    Redmineのチケット(Issue)にコメントを追加します。

    Args:
        issue_id: コメントを追加するチケットのID
        notes: 追加するコメント内容
    """
    client = get_client()
    await client.add_comment(issue_id, notes)
    return json.dumps(
        {
            "message": f"チケット #{issue_id} にコメントを追加しました",
            "url": f"{os.environ.get('REDMINE_URL', '')}/issues/{issue_id}",
        },
        ensure_ascii=False,
        indent=2,
    )


# ─── Tool: プロジェクト一覧取得 ───────────────────────────────

@mcp.tool()
async def get_projects(limit: int = 25, offset: int = 0) -> str:
    """
    Redmineのプロジェクト一覧を取得します。

    Args:
        limit: 取得件数 (デフォルト: 25)
        offset: 取得開始位置
    """
    client = get_client()
    result = await client.get_projects(limit=limit, offset=offset)
    projects = [
        {
            "id": p["id"],
            "name": p["name"],
            "identifier": p["identifier"],
            "description": p.get("description", ""),
            "status": "アクティブ" if p["status"] == 1 else "アーカイブ",
        }
        for p in result.get("projects", [])
    ]
    return json.dumps(
        {"total_count": result.get("total_count", 0), "projects": projects},
        ensure_ascii=False,
        indent=2,
    )
