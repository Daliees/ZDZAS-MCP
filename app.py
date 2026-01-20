
# app.py - entrypoint for the MCP server
# Loads core and all tool modules and starts the HTTP server.

from src.zas.core import helpers
import src.zas.tools.ticket  # noqa: F401  # registers ticket tools
import src.zas.tools.kb  # noqa: F401  # registers kb tools
import src.zas.tools.reporting  # noqa: F401  # registers reporting tools
import src.zas.tools.general  # noqa: F401  # registers general tools
import src.zas.tools.jira  # noqa: F401  # registers jira tools
import src.zas.tools.confluence  # noqa: F401  # registers confluence tools
import src.zas.tools.salesforce  # noqa: F401  # registers salesforce session tools
import src.zas.tools.admin  # noqa: F401  # registers admin tools


if __name__ == "__main__":
	try:
		helpers.mcp.run(
			transport="http",
			host="127.0.0.1",
			port=8000,
			path="/mcp",
			stateless_http=True,
		)
	except KeyboardInterrupt:
		print("MCP server gracefully shut down.")

