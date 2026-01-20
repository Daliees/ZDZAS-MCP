from __future__ import annotations

import argparse
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime

import requests
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("mcp_proxy")
logging.basicConfig(level=logging.INFO)

# URL of local FastMCP server
MCP_UPSTREAM_URL = os.getenv("MCP_UPSTREAM_URL", "http://127.0.0.1:8000/mcp")

# Metrics tracking
metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_error": 0,
    "latency_sum": 0.0,
    "start_time": datetime.now().isoformat(),
    "tools_called": defaultdict(int),
}

app = FastAPI(
	title="ZAS MCP HTTP proxy",
	description="Proxy tussen OpenAI HostedMCPTool en lokale FastMCP server.",
)

# CORS – niet kritisch, maar kan geen kwaad om alles toe te staan
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.post("/mcp")
async def mcp_proxy(request: Request) -> Response:
	"""
	Proxy endpoint that forwards JSON-RPC requests to the local MCP server.
	- Enforces Accept header that FastMCP expects
	- Adds sessionId to querystring
	- Converts upstream HTTP errors to HTTP 200 with JSON-RPC error
	  to prevent http_error/424 errors with HostedMCPTool
	"""
	start_time = time.time()
	metrics["requests_total"] += 1
	
	# Read raw body
	try:
		body_bytes = await request.body()
		body_text = body_bytes.decode("utf-8") if body_bytes else ""
	except Exception as e:
		logger.exception("Could not read request body: %s", e)
		metrics["requests_error"] += 1
		error = {
			"jsonrpc": "2.0",
			"id": "proxy-error",
			"error": {
				"code": -32700,
				"message": f"Proxy could not read request body: {e}",
			},
		}
		return Response(
			content=json.dumps(error),
			media_type="application/json",
			status_code=200,
		)

	# Bepaal upstream URL met sessionId
	if "?" in MCP_UPSTREAM_URL:
		upstream_url = MCP_UPSTREAM_URL + "&sessionId=mcp_proxy"
	else:
		upstream_url = MCP_UPSTREAM_URL + "?sessionId=mcp_proxy"

	logger.info("Proxying MCP request naar %s", upstream_url)

	# Bouw headers – zo minimaal mogelijk
	headers = {
		"Content-Type": "application/json",
		"Accept": "application/json, text/event-stream",
	}

	try:
		upstream_resp = requests.post(
			upstream_url,
			data=body_text.encode("utf-8"),
			headers=headers,
			timeout=60,
		)
	except Exception as e:
		logger.exception("Error calling upstream MCP: %s", e)
		metrics["requests_error"] += 1
		error = {
			"jsonrpc": "2.0",
			"id": "proxy-upstream-error",
			"error": {
				"code": -32001,
				"message": f"Proxy could not reach upstream MCP: {e}",
			},
		}
		return Response(
			content=json.dumps(error),
			media_type="application/json",
			status_code=200,
		)

	# Probeer JSON te parsen; als dat niet lukt, wrap als JSON-RPC error
	try:
		upstream_json = upstream_resp.json()
	except Exception:
		logger.error(
			"Upstream MCP gaf geen geldige JSON terug. Status=%s, body=%r",
			upstream_resp.status_code,
			upstream_resp.text[:500],
		)
		error = {
			"jsonrpc": "2.0",
			"id": "proxy-upstream-nonjson",
			"error": {
				"code": -32002,
				"message": (
					f"Upstream MCP gaf geen geldige JSON terug. "
					f"HTTP {upstream_resp.status_code}"
				),
				"data": upstream_resp.text[:1000],
			},
		}
		return Response(
			content=json.dumps(error),
			media_type="application/json",
			status_code=200,
		)

	# Als upstream een HTTP foutstatus geeft (4xx/5xx), wrap dat ook in JSON-RPC error
	if not (200 <= upstream_resp.status_code < 300):
		logger.error(
			"Upstream MCP HTTP error %s: %s",
			upstream_resp.status_code,
			upstream_resp.text[:500],
		)
		# Als upstream_json al een JSON-RPC error is, geef die gewoon door
		if isinstance(upstream_json, dict) and "error" in upstream_json:
			payload = upstream_json
		else:
			payload = {
				"jsonrpc": "2.0",
				"id": upstream_json.get("id", "proxy-upstream-http-error")
				if isinstance(upstream_json, dict)
				else "proxy-upstream-http-error",
				"error": {
					"code": -32003,
					"message": (f"Upstream MCP HTTP error {upstream_resp.status_code}"),
					"data": upstream_json,
				},
			}
		return Response(
			content=json.dumps(payload),
			media_type="application/json",
			status_code=200,
		)

	# Happy path: upstream gave 2xx + valid JSON – pass through
	metrics["requests_success"] += 1
	metrics["latency_sum"] += time.time() - start_time
	
	# Track tool calls
	try:
		body_json = json.loads(body_text) if body_text else {}
		if isinstance(body_json, dict) and body_json.get("method") == "tools/call":
			tool_name = body_json.get("params", {}).get("name", "unknown")
			metrics["tools_called"][tool_name] += 1
	except:
		pass
	
	return Response(
		content=json.dumps(upstream_json),
		media_type="application/json",
		status_code=200,
	)


@app.get("/health")
async def health() -> dict:
	"""Health check endpoint with upstream connectivity test"""
	health_status = {
		"status": "healthy",
		"service": "mcp-proxy",
		"upstream": MCP_UPSTREAM_URL,
		"timestamp": datetime.now().isoformat(),
	}
	
	# Test upstream connectivity
	try:
		resp = requests.get(MCP_UPSTREAM_URL.replace("/mcp", "/health"), timeout=2)
		if resp.status_code == 200:
			health_status["upstream_status"] = "ok"
		else:
			health_status["upstream_status"] = f"error: HTTP {resp.status_code}"
			health_status["status"] = "degraded"
	except Exception as e:
		health_status["upstream_status"] = f"error: {str(e)}"
		health_status["status"] = "degraded"
	
	return health_status


@app.get("/metrics")
async def get_metrics() -> dict:
	"""Metrics endpoint for monitoring"""
	total_requests = metrics["requests_total"]
	avg_latency = (
		metrics["latency_sum"] / metrics["requests_success"]
		if metrics["requests_success"] > 0
		else 0
	)
	
	return {
		"service": "mcp-proxy",
		"start_time": metrics["start_time"],
		"uptime_seconds": (datetime.now() - datetime.fromisoformat(metrics["start_time"])).total_seconds(),
		"requests": {
			"total": total_requests,
			"success": metrics["requests_success"],
			"error": metrics["requests_error"],
			"success_rate": metrics["requests_success"] / total_requests if total_requests > 0 else 0,
		},
		"latency": {
			"average_ms": round(avg_latency * 1000, 2),
		},
		"tools_called": dict(metrics["tools_called"]),
	}


if __name__ == "__main__":
	import uvicorn

	parser = argparse.ArgumentParser(description="MCP HTTP Proxy Server")
	parser.add_argument(
		"--host",
		default="0.0.0.0",
		help="Host to bind to (default: 0.0.0.0)",
	)
	parser.add_argument(
		"--port",
		type=int,
		default=int(os.getenv("MCP_PROXY_PORT", "8100")),
		help="Port to bind to (default: 8100)",
	)
	parser.add_argument(
		"--reload",
		action="store_true",
		help="Enable auto-reload on code changes",
	)
	args = parser.parse_args()

	uvicorn.run(
		"mcp_proxy:app",
		host=args.host,
		port=args.port,
		reload=args.reload,
	)
