# app.py - entrypoint for the MCP server
# Loads core and all tool modules and starts the HTTP server.

import argparse
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
	parser = argparse.ArgumentParser(description="ZDZAS MCP Server")
	parser.add_argument(
		"--mode",
		choices=["http", "stdio"],
		default=os.getenv("MCP_MODE", "http"),
		help="Transport mode: http (default, production) or stdio (local dev)",
	)
	parser.add_argument(
		"--host",
		default=os.getenv("MCP_HOST", "0.0.0.0"),
		help="Host to bind to (http mode only, default: 0.0.0.0)",
	)
	parser.add_argument(
		"--port",
		type=int,
		default=int(os.getenv("MCP_PORT", "8000")),
		help="Port to bind to (http mode only, default: 8000)",
	)
	args = parser.parse_args()

	try:
		if args.mode == "stdio":
			print("Starting MCP server in stdio mode (single-client, local only)", flush=True)
			print("Note: This mode does NOT support Salesforce integration or concurrent users", flush=True)
			helpers.mcp.run(transport="stdio")
		else:
			print(f"Starting MCP server in HTTP mode on {args.host}:{args.port}", flush=True)
			print("This is the recommended mode for production and Salesforce integration", flush=True)
			helpers.mcp.run(
				transport="http",
				host=args.host,
				port=args.port,
				path="/mcp",
				stateless_http=True,
			)
	except KeyboardInterrupt:
		print("\nMCP server gracefully shut down.")
