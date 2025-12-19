"""
Unified server wrapper.

Runs both the MCP server and optionally the chat API or proxy.
"""

from fastapi import FastAPI
import uvicorn

from src.zas.core import Config, get_config


app = FastAPI(title="ZAS Server Wrapper")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "zas-wrapper"}


@app.get("/mcp")
def mcp():
    """Info about MCP endpoint."""
    return {
        "info": "This is a health endpoint. The actual MCP server runs on port 8000.",
        "mcp_url": "http://127.0.0.1:8000/mcp"
    }


def main():
    """Main entry point."""
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")


if __name__ == "__main__":
    main()
