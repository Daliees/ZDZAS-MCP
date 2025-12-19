"""MCP Proxy for OpenAI integration."""

import json
import logging
from typing import Optional

import requests
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from ..core import Config

logger = logging.getLogger("mcp_proxy")


class MCPProxy:
    """Proxy between OpenAI HostedMCPTool and local FastMCP server."""
    
    def __init__(self, config: Config, upstream_url: Optional[str] = None):
        """
        Initialize the MCP proxy.
        
        Args:
            config: Application configuration
            upstream_url: Optional upstream MCP URL (defaults to config)
        """
        self.config = config
        self.upstream_url = upstream_url or (
            f"http://{config.mcp_host}:{config.mcp_port}{config.mcp_path}"
        )
        
        # Create FastAPI app
        self.app = FastAPI(
            title="ZAS MCP HTTP Proxy",
            description="Proxy between OpenAI HostedMCPTool and local FastMCP server.",
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self) -> None:
        """Register proxy routes."""
        
        @self.app.post("/mcp")
        async def mcp_proxy(request: Request) -> Response:
            """
            Proxy endpoint for JSON-RPC requests.
            
            - Enforces Accept headers that FastMCP expects
            - Adds sessionId to querystring
            - Converts HTTP errors to JSON-RPC errors
            """
            # Read request body
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8") if body_bytes else ""
            except Exception as e:
                logger.exception("Failed to read request body: %s", e)
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
            
            # Build upstream URL with sessionId
            upstream_url = self.upstream_url
            if "?" in upstream_url:
                upstream_url += "&sessionId=mcp_proxy"
            else:
                upstream_url += "?sessionId=mcp_proxy"
            
            logger.info("Proxying MCP request to %s", upstream_url)
            
            # Build headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            
            # Make upstream request
            try:
                upstream_resp = requests.post(
                    upstream_url,
                    data=body_text.encode("utf-8"),
                    headers=headers,
                    timeout=60,
                )
            except Exception as e:
                logger.exception("Failed to call upstream MCP: %s", e)
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
            
            # Parse response
            try:
                content_type = upstream_resp.headers.get("Content-Type", "")
                
                if "application/json" in content_type:
                    # Return JSON directly
                    return Response(
                        content=upstream_resp.content,
                        media_type="application/json",
                        status_code=200,
                    )
                elif "text/event-stream" in content_type:
                    # Extract data from SSE
                    body = upstream_resp.text
                    data_line = None
                    for line in body.splitlines():
                        line = line.strip()
                        if line.startswith("data:"):
                            data_line = line[len("data:"):].strip()
                    
                    if data_line:
                        return Response(
                            content=data_line,
                            media_type="application/json",
                            status_code=200,
                        )
                
                # Fallback: return as-is
                return Response(
                    content=upstream_resp.content,
                    media_type=content_type or "application/json",
                    status_code=200,
                )
            
            except Exception as e:
                logger.exception("Failed to parse upstream response: %s", e)
                error = {
                    "jsonrpc": "2.0",
                    "id": "proxy-parse-error",
                    "error": {
                        "code": -32002,
                        "message": f"Proxy could not parse upstream response: {e}",
                    },
                }
                return Response(
                    content=json.dumps(error),
                    media_type="application/json",
                    status_code=200,
                )
