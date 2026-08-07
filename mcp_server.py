"""Single MCP server — local-mac tools (via Swift CLI) + vault (filesystem)."""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.fastmcp import FastMCP
from dispatcher import build_dispatcher

mcp = FastMCP("local-mac")
build_dispatcher(mcp)

if __name__ == "__main__":
    mcp.run()
