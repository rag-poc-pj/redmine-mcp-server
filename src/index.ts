/**
 * ローカル開発用エントリーポイント
 * npm run dev で起動
 */

import app from "./app.js";

const PORT = process.env.PORT ?? 3000;

app.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════════╗
║       Redmine MCP Server (Local Dev)         ║
╠══════════════════════════════════════════════╣
║  MCP Endpoint : http://localhost:${PORT}/mcp   ║
║  Health Check : http://localhost:${PORT}/health║
╚══════════════════════════════════════════════╝

環境変数:
  REDMINE_URL     = ${process.env.REDMINE_URL ?? "❌ 未設定"}
  REDMINE_API_KEY = ${process.env.REDMINE_API_KEY ? "✅ 設定済み" : "❌ 未設定"}
`);
});
