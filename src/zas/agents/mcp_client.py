"""MCP HTTP client for agent integration."""

import os
import json
from typing import Any, Dict

import requests


class MCPClient:
    """HTTP client for communicating with FastMCP server."""
    
    def __init__(self, server_url: str):
        """
        Initialize MCP client.
        
        Args:
            server_url: URL of the MCP server (e.g., 'http://127.0.0.1:8000/mcp')
        """
        self.server_url = server_url
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool via HTTP JSON-RPC.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            RuntimeError: If the call fails
        """
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        
        try:
            resp = requests.post(
                self.server_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"MCP call failed for {tool_name}: {e}")
        
        # Parse response
        result = self._parse_response(tool_name, resp)
        
        # Extract content from MCP response structure
        if isinstance(result, dict):
            if "result" in result:
                result = result["result"]
            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    if isinstance(first_item, dict) and "text" in first_item:
                        try:
                            return json.loads(first_item["text"])
                        except json.JSONDecodeError:
                            return first_item["text"]
        
        return result
    
    def _parse_response(self, tool_name: str, resp: requests.Response) -> Any:
        """
        Parse HTTP response from MCP server.
        
        Args:
            tool_name: Tool name (for logging)
            resp: HTTP response
            
        Returns:
            Parsed response data
        """
        content_type = (resp.headers.get("Content-Type") or "").lower()
        body = resp.text
        
        if not body:
            raise RuntimeError(
                f"MCP response from {tool_name} had empty body (status {resp.status_code})"
            )
        
        # JSON response
        if "application/json" in content_type:
            try:
                return resp.json()
            except Exception as e:
                raise RuntimeError(
                    f"JSON decode error for {tool_name}: {e}\nBody: {body[:300]}"
                )
        
        # Server-Sent Events (SSE)
        if "text/event-stream" in content_type:
            data_line = None
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    data_line = line[len("data:"):].strip()
            
            if not data_line:
                raise RuntimeError(f"MCP SSE response from {tool_name} had no data line")
            
            try:
                return json.loads(data_line)
            except Exception as e:
                raise RuntimeError(
                    f"SSE JSON decode error for {tool_name}: {e}\nData: {data_line[:300]}"
                )
        
        # Unknown content type
        raise RuntimeError(
            f"Unexpected Content-Type from MCP for {tool_name}: {content_type}"
        )


def get_mcp_client() -> MCPClient:
    """
    Get MCP client instance from environment.
    
    Returns:
        MCPClient instance
    """
    server_url = os.getenv("ZAS_MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
    return MCPClient(server_url)
