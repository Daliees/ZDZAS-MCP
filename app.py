"""
Main MCP server application.

This module starts the FastMCP HTTP server with all registered tools.
"""

import sys
import traceback
from fastmcp import FastMCP

from src.zas.core import Config, get_config
from src.zas.core.metrics import get_metrics
from src.zas.services.telegram_service import get_telegram_service
from src.zas.tools.registry import MCPToolRegistry


def create_mcp_server(config: Config = None) -> FastMCP:
    """
    Create and configure the MCP server.
    
    Args:
        config: Optional configuration (will load from env if not provided)
        
    Returns:
        Configured FastMCP instance
    """
    if config is None:
        config = get_config()
    
    # Create MCP instance
    mcp = FastMCP(name="zendesk_mcp_http")
    
    # Register all tools
    registry = MCPToolRegistry(config, mcp)
    registry.register_all()
    
    return mcp


def main():
    """Main entry point for the MCP server."""
    config = get_config()
    metrics = get_metrics()
    
    # Initialize Telegram if configured
    telegram = None
    if config.telegram_enabled and config.telegram_bot_token and config.telegram_chat_id:
        telegram = get_telegram_service(config.telegram_bot_token, config.telegram_chat_id)
    
    try:
        mcp = create_mcp_server(config)
        
        # Set status and notify startup
        metrics.set_mcp_status("✅ Online")
        if telegram:
            url = f"http://{config.mcp_host}:{config.mcp_port}{config.mcp_path}"
            telegram.notify_startup_sync("MCP Server", config.mcp_host, config.mcp_port, url)
        
        print(f"Starting MCP Server on {config.mcp_host}:{config.mcp_port}")
        
        # Track requests by wrapping the server
        original_run = mcp.run
        def run_with_metrics(*args, **kwargs):
            metrics.increment_mcp_requests()
            return original_run(*args, **kwargs)
        mcp.run = run_with_metrics
        
        mcp.run(
            transport="http",
            host=config.mcp_host,
            port=config.mcp_port,
            path=config.mcp_path,
            stateless_http=True,
        )
    except KeyboardInterrupt:
        print("\nMCP server shut down gracefully.")
        metrics.set_mcp_status("⏹️ Stopped")
    except Exception as e:
        print(f"\nMCP server crashed: {e}")
        metrics.set_mcp_status("🔴 Crashed")
        if telegram:
            tb = traceback.format_exc()
            telegram.notify_crash_sync("MCP Server", e, tb)
        sys.exit(1)


if __name__ == "__main__":
    main()
