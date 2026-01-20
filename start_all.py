import multiprocessing as mp
import os
import signal
import sys
import time
from pathlib import Path

import requests
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
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
CHAT_HOST = os.getenv("CHAT_HOST", "0.0.0.0")
CHAT_PORT = int(os.getenv("CHAT_PORT", "9000"))


def run_mcp() -> None:
	"""Start the MCP server (same as app.py)."""
	print(f"Starting MCP server on {MCP_HOST}:{MCP_PORT}")
	try:
		helpers.mcp.run(
			transport="http", host=MCP_HOST, port=MCP_PORT, path="/mcp", stateless_http=True
		)
	except KeyboardInterrupt:
		print("MCP server shutting down...")


def run_chat_api() -> None:
	"""Start the Chat API via uvicorn."""
	print(f"Starting Chat API on {CHAT_HOST}:{CHAT_PORT}")
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
		print("Chat API shutting down...")


def health_check(name: str, url: str, max_retries: int = 10) -> bool:
	"""Check if a service is healthy"""
	for i in range(max_retries):
		try:
			resp = requests.get(url, timeout=2)
			if resp.status_code == 200:
				print(f"✓ {name} is healthy")
				return True
		except Exception:
			pass
		if i < max_retries - 1:
			time.sleep(1)
	print(f"✗ {name} health check failed")
	return False


def main() -> None:
	print("=" * 60)
	print("ZDZAS-MCP - Starting all services")
	print("=" * 60)
	
	mp.set_start_method("spawn", force=True)  # safer on Windows

	procs = [
		mp.Process(target=run_mcp, name="mcp-server"),
		mp.Process(target=run_chat_api, name="chat-api"),
	]

	for p in procs:
		p.start()
		print(f"Started process: {p.name} (PID: {p.pid})")

	def shutdown(signum=None, frame=None):
		print("\n" + "=" * 60)
		print("Shutting down all services...")
		print("=" * 60)
		
		for p in procs:
			if p.is_alive():
				print(f"Terminating {p.name}...")
				p.terminate()
		
		# Wait for graceful shutdown
		for p in procs:
			p.join(timeout=5)
			if p.is_alive():
				print(f"Force killing {p.name}...")
				p.kill()
				p.join()
		
		print("All services stopped")
		sys.exit(0)

	signal.signal(signal.SIGINT, shutdown)
	signal.signal(signal.SIGTERM, shutdown)
	
	# Wait for services to start
	time.sleep(3)
	
	# Perform health checks
	print("\n" + "=" * 60)
	print("Health checks")
	print("=" * 60)
	health_check("MCP Server", f"http://{MCP_HOST}:{MCP_PORT}/mcp")
	health_check("Chat API", f"http://{CHAT_HOST}:{CHAT_PORT}/ping")
	
	print("\n" + "=" * 60)
	print("All services running")
	print(f"MCP Server:  http://{MCP_HOST}:{MCP_PORT}/mcp")
	print(f"Chat API:    http://{CHAT_HOST}:{CHAT_PORT}")
	print(f"API Docs:    http://{CHAT_HOST}:{CHAT_PORT}/docs")
	print("Press Ctrl+C to stop")
	print("=" * 60 + "\n")

	try:
		while True:
			time.sleep(1)
			# Check if any process died unexpectedly
			for p in procs:
				if not p.is_alive():
					print(f"✗ Process {p.name} died unexpectedly!")
					shutdown()
	except KeyboardInterrupt:
		pass
	finally:
		shutdown()


if __name__ == "__main__":
	main()
