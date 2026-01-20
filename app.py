# app.py - entrypoint for the MCP server
# Loads core and all tool modules and starts the HTTP server.

import os

import src.zas.tools.admin  # noqa: F401  # registers admin tools
import src.zas.tools.confluence  # noqa: F401  # registers confluence tools
import src.zas.tools.general  # noqa: F401  # registers general tools
import src.zas.tools.jira  # noqa: F401  # registers jira tools
import src.zas.tools.kb  # noqa: F401  # registers kb tools
import src.zas.tools.reporting  # noqa: F401  # registers reporting tools
import src.zas.tools.salesforce  # noqa: F401  # registers salesforce session tools
import src.zas.tools.ticket  # noqa: F401  # registers ticket tools
from src.zas.core import helpers

if __name__ == "__main__":
	MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
	MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
	
	print(f"Starting MCP server (HTTP) on {MCP_HOST}:{MCP_PORT}")
	print("Multi-user support enabled for Salesforce integration")
	
	try:
		helpers.mcp.run(
			transport="http",
			host=MCP_HOST,
			port=MCP_PORT,
			path="/mcp",
			stateless_http=True,
		)
	except KeyboardInterrupt:
		print("\nMCP server gracefully shut down.")
