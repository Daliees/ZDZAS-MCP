from __future__ import annotations

import os
import json
import logging

import requests
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("mcp_proxy")
logging.basicConfig(level=logging.INFO)

# URL van lokale FastMCP-server
# Voorbeeld: "http://127.0.0.1:8000/mcp" (zonder sessionId; voegen 'mcp_proxy' zelf toe)
MCP_UPSTREAM_URL = os.getenv("MCP_UPSTREAM_URL", "http://127.0.0.1:8000/mcp")

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
	Proxy endpoint dat JSON-RPC requests doorstuurt naar de lokale MCP-server.
	- Dwingt Accept-header af die FastMCP verwacht.
	- Voegt een sessionId toe aan de querystring.
	- Converteert upstream HTTP-fouten naar HTTP 200 met JSON-RPC error, om
	  'http_error' / 424 fouten bij HostedMCPTool te voorkomen.
	"""
	# Lees raw body
	try:
		body_bytes = await request.body()
		body_text = body_bytes.decode("utf-8") if body_bytes else ""
	except Exception as e:
		logger.exception("Kon request body niet lezen: %s", e)
		error = {
			"jsonrpc": "2.0",
			"id": "proxy-error",
			"error": {
				"code": -32700,
				"message": f"Proxy kon request body niet lezen: {e}",
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
		logger.exception("Fout bij HTTP-call naar MCP upstream: %s", e)
		error = {
			"jsonrpc": "2.0",
			"id": "proxy-upstream-error",
			"error": {
				"code": -32001,
				"message": f"Proxy kon upstream MCP niet bereiken: {e}",
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
					"message": (
						f"Upstream MCP HTTP error {upstream_resp.status_code}"
					),
					"data": upstream_json,
				},
			}
		return Response(
			content=json.dumps(payload),
			media_type="application/json",
			status_code=200,
		)

	# Happy path: upstream gaf 2xx + geldige JSON – geef 1-op-1 door
	return Response(
		content=json.dumps(upstream_json),
		media_type="application/json",
		status_code=200,
	)


@app.get("/health")
async def health() -> dict:
	return {
		"status": "ok",
		"upstream": MCP_UPSTREAM_URL,
	}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(
		"mcp_proxy:app",
		host="0.0.0.0",
		port=int(os.getenv("MCP_PROXY_PORT", "8100")),
		reload=True,
	)
