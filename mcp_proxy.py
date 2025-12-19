"""
MCP Proxy application.

This module starts the MCP proxy server for OpenAI integration.
"""

import sys
import traceback
import uvicorn

from src.zas.core import Config, get_config
from src.zas.core.metrics import get_metrics
from src.zas.services.telegram_service import get_telegram_service
from src.zas.api import MCPProxy


def create_mcp_proxy(config: Config = None) -> MCPProxy:
    """
    Create and configure the MCP proxy.
    
    Args:
        config: Optional configuration (will load from env if not provided)
        
    Returns:
        Configured MCPProxy instance
    """
    if config is None:
        config = get_config()
    
    metrics = get_metrics()
    proxy = MCPProxy(config)
    
    # Add metrics middleware
    @proxy.app.middleware("http")
    async def track_requests(request, call_next):
        metrics.increment_proxy_requests()
        response = await call_next(request)
        return response
    
    return proxy


def main():
    """Main entry point for the MCP proxy server."""
    config = get_config()
    metrics = get_metrics()
    
    # Initialize Telegram if configured
    telegram = None
    if config.telegram_enabled and config.telegram_bot_token and config.telegram_chat_id:
        telegram = get_telegram_service(config.telegram_bot_token, config.telegram_chat_id)
    
    try:
        proxy = create_mcp_proxy(config)
        
        # Set status and notify startup
        metrics.set_proxy_status("✅ Online")
        if telegram:
            url = f"http://{config.mcp_proxy_host}:{config.mcp_proxy_port}/mcp"
            telegram.notify_startup_sync("MCP Proxy", config.mcp_proxy_host, config.mcp_proxy_port, url)
        
        print(f"Starting MCP Proxy on {config.mcp_proxy_host}:{config.mcp_proxy_port}")
        
        # Run with configured host/port
        uvicorn.run(
            proxy.app,
            host=config.mcp_proxy_host,
            port=config.mcp_proxy_port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nMCP Proxy shut down gracefully.")
        metrics.set_proxy_status("⏹️ Stopped")
    except Exception as e:
        print(f"\nMCP Proxy crashed: {e}")
        metrics.set_proxy_status("🔴 Crashed")
        if telegram:
            tb = traceback.format_exc()
            telegram.notify_crash_sync("MCP Proxy", e, tb)
        sys.exit(1)


if __name__ == "__main__":
    main()
