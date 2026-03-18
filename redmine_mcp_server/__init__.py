"""
Redmine MCP Server
uvx で起動するエントリーポイント
"""
from .server import mcp


def main() -> None:
    mcp.run(transport="stdio")
