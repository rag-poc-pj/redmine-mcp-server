"""
Amazon Bedrock (Claude) を使ってRedmineデータを要約する
"""
import json
import boto3


class BedrockSummarizer:
    def __init__(self, region: str = "ap-northeast-1", model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = model_id

    def _invoke(self, prompt: str) -> str:
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            }),
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def summarize_issues(self, issues: list[dict]) -> str:
        """チケット一覧を要約する"""
        issues_text = "\n".join([
            f"- #{i['id']} [{i['status']['name']}] {i['subject']} "
            f"(担当: {i.get('assigned_to', {}).get('name', '未割り当て')}, "
            f"優先度: {i['priority']['name']})"
            for i in issues
        ])
        prompt = f"""以下はRedmineのチケット一覧です。日本語で簡潔に要約してください。
特に重要な点（優先度が高いもの、期限が近いもの、担当者未割り当てのもの）を強調してください。

チケット一覧:
{issues_text}

要約:"""
        return self._invoke(prompt)

    def summarize_issue_detail(self, issue: dict) -> str:
        """チケット詳細を要約する"""
        comments = "\n".join([
            f"[{j['created_on']}] {j['user']['name']}: {j['notes']}"
            for j in issue.get("journals", [])
            if j.get("notes")
        ])
        prompt = f"""以下のRedmineチケットの内容を日本語で要約してください。

チケット番号: #{issue['id']}
件名: {issue['subject']}
ステータス: {issue['status']['name']}
優先度: {issue['priority']['name']}
担当者: {issue.get('assigned_to', {}).get('name', '未割り当て')}
説明: {issue.get('description', 'なし')}

コメント履歴:
{comments if comments else 'コメントなし'}

要約（現状・課題・次のアクション）:"""
        return self._invoke(prompt)

    def summarize_projects(self, projects: list[dict]) -> str:
        """プロジェクト一覧を要約する"""
        projects_text = "\n".join([
            f"- {p['name']} (ID: {p['identifier']}, "
            f"状態: {'アクティブ' if p['status'] == 1 else 'アーカイブ'})"
            for p in projects
        ])
        prompt = f"""以下はRedmineのプロジェクト一覧です。日本語で簡潔に要約してください。

プロジェクト一覧:
{projects_text}

要約:"""
        return self._invoke(prompt)
