#!/usr/bin/env node
/**
 * stdio エントリーポイント
 * EC2上のGenUから npx で呼び出される際に使用
 *
 * 使用例（mcp.json）:
 * {
 *   "redmine": {
 *     "command": "npx",
 *     "args": ["-y", "github:rag-poc-pj/redmine-mcp-server"],
 *     "env": {
 *       "REDMINE_URL": "https://your-redmine.example.com",
 *       "REDMINE_API_KEY": "your_api_key"
 *     }
 *   }
 * }
 */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createMcpServer } from "./server.js";

async function main() {
  if (!process.env.REDMINE_URL || !process.env.REDMINE_API_KEY) {
    process.stderr.write(
      "エラー: REDMINE_URL と REDMINE_API_KEY の環境変数が必要です\n"
    );
    process.exit(1);
  }

  const server = createMcpServer();
  const transport = new StdioServerTransport();

  await server.connect(transport);

  process.stderr.write("Redmine MCP Server が起動しました (stdio)\n");
}

main().catch((err) => {
  process.stderr.write(`起動エラー: ${err}\n`);
  process.exit(1);
});
