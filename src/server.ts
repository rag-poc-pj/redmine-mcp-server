/**
 * MCP Server - Redmineツール定義
 * Model Context Protocol SDK を使ったツール定義
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { RedmineClient } from "./redmine-client.js";

export function createMcpServer(): McpServer {
  const client = new RedmineClient({
    baseUrl: process.env.REDMINE_URL ?? "",
    apiKey: process.env.REDMINE_API_KEY ?? "",
  });

  const server = new McpServer({
    name: "redmine-mcp-server",
    version: "1.0.0",
  });

  // ─── Tool: チケット一覧取得・検索 ────────────────────────────

  server.tool(
    "get_issues",
    "Redmineのチケット(Issue)一覧を取得・検索します",
    {
      project_id: z.string().optional().describe("プロジェクトIDまたは識別子 (例: my-project)"),
      status_id: z
        .enum(["open", "closed", "*"])
        .optional()
        .describe("ステータスフィルタ: open=未完了, closed=完了, *=全て"),
      assigned_to_id: z.string().optional().describe("担当者のユーザーID (me で自分のチケット)"),
      subject: z.string().optional().describe("件名の部分一致検索キーワード"),
      limit: z.number().int().min(1).max(100).optional().describe("取得件数 (デフォルト: 25, 最大: 100)"),
      offset: z.number().int().min(0).optional().describe("取得開始位置 (ページネーション用)"),
    },
    async (params) => {
      try {
        const result = await client.getIssues(params);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  total_count: result.total_count,
                  issues: result.issues.map((i) => ({
                    id: i.id,
                    subject: i.subject,
                    status: i.status.name,
                    priority: i.priority.name,
                    project: i.project.name,
                    assigned_to: i.assigned_to?.name ?? "未割り当て",
                    due_date: i.due_date ?? "未設定",
                    done_ratio: i.done_ratio,
                    updated_on: i.updated_on,
                  })),
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (e: unknown) {
        return { content: [{ type: "text", text: `エラー: ${(e as Error).message}` }], isError: true };
      }
    }
  );

  // ─── Tool: チケット詳細取得 ───────────────────────────────────

  server.tool(
    "get_issue",
    "Redmineの特定チケット(Issue)の詳細・コメント・添付ファイルを取得します",
    {
      issue_id: z.number().int().describe("チケットID (例: 123)"),
    },
    async ({ issue_id }) => {
      try {
        const { issue } = await client.getIssue(issue_id);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  id: issue.id,
                  subject: issue.subject,
                  description: issue.description,
                  project: issue.project.name,
                  status: issue.status.name,
                  priority: issue.priority.name,
                  tracker: issue.tracker.name,
                  author: issue.author.name,
                  assigned_to: issue.assigned_to?.name ?? "未割り当て",
                  start_date: issue.start_date,
                  due_date: issue.due_date,
                  done_ratio: issue.done_ratio,
                  created_on: issue.created_on,
                  updated_on: issue.updated_on,
                  comments: issue.journals
                    .filter((j) => j.notes)
                    .map((j) => ({
                      id: j.id,
                      author: j.user.name,
                      notes: j.notes,
                      created_on: j.created_on,
                    })),
                  attachments: issue.attachments.map((a) => ({
                    id: a.id,
                    filename: a.filename,
                    filesize: a.filesize,
                    content_url: a.content_url,
                    created_on: a.created_on,
                  })),
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (e: unknown) {
        return { content: [{ type: "text", text: `エラー: ${(e as Error).message}` }], isError: true };
      }
    }
  );

  // ─── Tool: チケット作成 ───────────────────────────────────────

  server.tool(
    "create_issue",
    "Redmineに新しいチケット(Issue)を作成します",
    {
      project_id: z.string().describe("プロジェクトIDまたは識別子 (必須)"),
      subject: z.string().describe("チケットの件名 (必須)"),
      description: z.string().optional().describe("チケットの詳細説明"),
      tracker_id: z.number().int().optional().describe("トラッカーID (1=バグ, 2=機能, 3=サポート等)"),
      priority_id: z.number().int().optional().describe("優先度ID (1=低, 2=通常, 3=高, 4=急いで, 5=今すぐ)"),
      assigned_to_id: z.number().int().optional().describe("担当者のユーザーID"),
      due_date: z.string().optional().describe("期日 (YYYY-MM-DD形式)"),
    },
    async (params) => {
      try {
        const { issue } = await client.createIssue(params);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  message: "チケットを作成しました",
                  id: issue.id,
                  subject: issue.subject,
                  status: issue.status.name,
                  project: issue.project.name,
                  url: `${process.env.REDMINE_URL}/issues/${issue.id}`,
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (e: unknown) {
        return { content: [{ type: "text", text: `エラー: ${(e as Error).message}` }], isError: true };
      }
    }
  );

  // ─── Tool: チケット更新 ───────────────────────────────────────

  server.tool(
    "update_issue",
    "Redmineの既存チケット(Issue)を更新します",
    {
      issue_id: z.number().int().describe("更新するチケットのID"),
      subject: z.string().optional().describe("新しい件名"),
      description: z.string().optional().describe("新しい詳細説明"),
      status_id: z.number().int().optional().describe("新しいステータスID"),
      priority_id: z.number().int().optional().describe("新しい優先度ID"),
      assigned_to_id: z.number().int().optional().describe("新しい担当者のユーザーID"),
      due_date: z.string().optional().describe("新しい期日 (YYYY-MM-DD形式)"),
      done_ratio: z.number().int().min(0).max(100).optional().describe("進捗率 (0〜100)"),
    },
    async ({ issue_id, ...data }) => {
      try {
        await client.updateIssue(issue_id, data);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                message: `チケット #${issue_id} を更新しました`,
                url: `${process.env.REDMINE_URL}/issues/${issue_id}`,
              }, null, 2),
            },
          ],
        };
      } catch (e: unknown) {
        return { content: [{ type: "text", text: `エラー: ${(e as Error).message}` }], isError: true };
      }
    }
  );

  // ─── Tool: コメント追加 ───────────────────────────────────────

  server.tool(
    "add_comment",
    "Redmineのチケット(Issue)にコメントを追加します",
    {
      issue_id: z.number().int().describe("コメントを追加するチケットのID"),
      notes: z.string().describe("追加するコメント内容"),
    },
    async ({ issue_id, notes }) => {
      try {
        await client.addComment(issue_id, notes);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                message: `チケット #${issue_id} にコメントを追加しました`,
                url: `${process.env.REDMINE_URL}/issues/${issue_id}`,
              }, null, 2),
            },
          ],
        };
      } catch (e: unknown) {
        return { content: [{ type: "text", text: `エラー: ${(e as Error).message}` }], isError: true };
      }
    }
  );

  // ─── Tool: プロジェクト一覧取得 ───────────────────────────────

  server.tool(
    "get_projects",
    "Redmineのプロジェクト一覧を取得します",
    {
      limit: z.number().int().min(1).max(100).optional().describe("取得件数 (デフォルト: 25)"),
      offset: z.number().int().min(0).optional().describe("取得開始位置"),
    },
    async (params) => {
      try {
        const result = await client.getProjects(params);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  total_count: result.total_count,
                  projects: result.projects.map((p) => ({
                    id: p.id,
                    name: p.name,
                    identifier: p.identifier,
                    description: p.description,
                    status: p.status === 1 ? "アクティブ" : "アーカイブ",
                  })),
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (e: unknown) {
        return { content: [{ type: "text", text: `エラー: ${(e as Error).message}` }], isError: true };
      }
    }
  );

  return server;
}
