#!/usr/bin/env python3
"""Run script for the web search MCP server."""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, Path.joinpath(Path.__dir__, "src"))

from web_search.server import mcp

# Import and run the server
if __name__ == "__main__":
    mcp.run()
