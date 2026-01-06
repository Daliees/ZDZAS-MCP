
# app.py - entrypoint voor de MCP-server
# Laadt core + alle tool-modules en start de HTTP-server.

from core import mcp
import tools_ticket  # noqa: F401  # registreert tickets-tools
import tools_kb  # noqa: F401  # registreert kb-tools
import tools_reporting  # noqa: F401  # registreert reporting-tools
import tools_general  # noqa: F401  # registreert general-tools
import tools_jira       # noqa: F401 # registreert jira-tools
import tools_confluence # noqa: F401 # registreert confluence-tools
import tools_salesforce  # noqa: F401 # registreert salesforce session tools
import tools_admin  # noqa: F401 # registreert admin-tools (org urls)


if __name__ == "__main__":
	try:
		mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp", stateless_http=True,)
	except KeyboardInterrupt:
		print("MCP server netjes afgesloten.")
