import multiprocessing as mp
import signal
import sys
import time
from pathlib import Path

import uvicorn

# Ensure local modules are importable in child processes
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
	sys.path.insert(0, str(BASE_DIR))

import src.zas.tools.admin  # noqa: F401
import src.zas.tools.confluence  # noqa: F401
import src.zas.tools.general  # noqa: F401
import src.zas.tools.jira  # noqa: F401
import src.zas.tools.kb  # noqa: F401
import src.zas.tools.reporting  # noqa: F401
import src.zas.tools.salesforce  # noqa: F401
import src.zas.tools.ticket  # noqa: F401
from src.zas.core import helpers

# Ports (keep in sync with existing setup)
MCP_HOST = "127.0.0.1"
MCP_PORT = 8000
CHAT_HOST = "0.0.0.0"
CHAT_PORT = 9000


def run_mcp() -> None:
	"""Start the MCP server (same as app.py)."""
	try:
		helpers.mcp.run(
			transport="http", host=MCP_HOST, port=MCP_PORT, path="/mcp", stateless_http=True
		)
	except KeyboardInterrupt:
		pass


def run_chat_api() -> None:
	"""Start the Chat API via uvicorn."""
	try:
		uvicorn.run(
			"chat_api:app",
			host=CHAT_HOST,
			port=CHAT_PORT,
			reload=False,
			log_level="info",
			app_dir=str(BASE_DIR),
		)
	except KeyboardInterrupt:
		pass


def main() -> None:
	mp.set_start_method("spawn", force=True)  # safer on Windows

	procs = [
		mp.Process(target=run_mcp, name="mcp-server"),
		mp.Process(target=run_chat_api, name="chat-api"),
	]

	for p in procs:
		p.start()

	def shutdown(*_):
		for p in procs:
			if p.is_alive():
				p.terminate()
		for p in procs:
			p.join(timeout=5)
		sys.exit(0)

	signal.signal(signal.SIGINT, shutdown)
	signal.signal(signal.SIGTERM, shutdown)

	try:
		while True:
			time.sleep(1)
	finally:
		shutdown()


if __name__ == "__main__":
	main()
