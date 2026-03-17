/**
 * Express アプリ本体
 * MCP over Streamable HTTP Transport
 * Lambda / ローカルサーバー共通
 *
 * GenU はデフォルトで Content-Type を指定しない場合があるため、
 * Content-Type が未指定またはJSON系の場合はすべて application/json として処理する。
 */

import express, { Request, Response, NextFunction } from "express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpServer } from "./server.js";

const app = express();

// ─── JSON フォールバックミドルウェア ─────────────────────────
// GenU が Content-Type を指定しない場合も JSON として扱う
app.use((req: Request, _res: Response, next: NextFunction) => {
  const contentType = req.headers["content-type"] ?? "";

  // Content-Type が未指定 or JSON系でない場合に application/json を補完
  const isJsonLike =
    contentType === "" ||
    contentType.includes("application/json") ||
    contentType.includes("text/plain");      // 一部クライアントが text/plain で送る場合も考慮

  if (isJsonLike && !contentType.includes("application/json")) {
    req.headers["content-type"] = "application/json";
    console.log(`[Middleware] Content-Type を補完: "${contentType || "(未指定)"}" → "application/json"`);
  }

  next();
});

// JSON パース（補完後なので確実に処理される）
app.use(express.json({ limit: "10mb" }));

// ─── ヘルスチェック ─────────────────────────────────────────

app.get("/health", (_req: Request, res: Response) => {
  res.json({
    status: "ok",
    service: "redmine-mcp-server",
    timestamp: new Date().toISOString(),
  });
});

// ─── MCP エンドポイント (Streamable HTTP) ────────────────────

app.post("/mcp", async (req: Request, res: Response) => {
  // 環境変数チェック
  if (!process.env.REDMINE_URL || !process.env.REDMINE_API_KEY) {
    res.status(500).json({
      error: "REDMINE_URL と REDMINE_API_KEY の環境変数が設定されていません",
    });
    return;
  }

  // body が未パースの場合（万一のフォールバック）
  let body = req.body;
  if (!body || typeof body !== "object") {
    try {
      body = JSON.parse(req.body as string);
    } catch {
      res.status(400).json({
        jsonrpc: "2.0",
        error: { code: -32700, message: "JSON のパースに失敗しました" },
        id: null,
      });
      return;
    }
  }

  // レスポンスは常に application/json で返す
  res.setHeader("Content-Type", "application/json");

  try {
    const server = createMcpServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined, // ステートレスモード（Lambda向け）
    });

    // リクエスト処理後にサーバーをクリーンアップ
    res.on("finish", () => {
      transport.close();
      server.close();
    });

    await server.connect(transport);
    await transport.handleRequest(req, res, body);
  } catch (err: unknown) {
    console.error("[MCP Error]", err);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: { code: -32603, message: "Internal Server Error" },
        id: null,
      });
    }
  }
});

// SSE / GET は非サポートの旨を返す
app.get("/mcp", (_req: Request, res: Response) => {
  res.status(405).json({
    error: "GET /mcp はサポートしていません。POST でリクエストしてください",
  });
});

export default app;
