"""
Chat API application.

This module starts the FastAPI server for chat interactions.
"""

import sys
import traceback
import uvicorn

from src.zas.core import Config, get_config
from src.zas.core.metrics import get_metrics
from src.zas.services.telegram_service import get_telegram_service
from src.zas.api import ChatAPI
from src.zas.agents import ZASAgent
from src.zas.agents.mcp_client import get_mcp_client


def create_chat_api(config: Config = None) -> ChatAPI:
    """
    Create and configure the Chat API.
    
    Args:
        config: Optional configuration (will load from env if not provided)
        
    Returns:
        Configured ChatAPI instance
    """
    if config is None:
        config = get_config()
    
    # Create MCP client
    mcp_client = get_mcp_client()
    
    # Create agent
    agent = ZASAgent(mcp_client)
    
    # Create Chat API with agent runner
    chat_api = ChatAPI(config, agent_runner=agent.run)
    
    return chat_api


def main():
    """Main entry point for the Chat API server."""
    config = get_config()
    metrics = get_metrics()
    
    # Initialize Telegram if configured
    telegram = None
    if config.telegram_enabled and config.telegram_bot_token and config.telegram_chat_id:
        telegram = get_telegram_service(config.telegram_bot_token, config.telegram_chat_id)
    
    try:
        chat_api = create_chat_api(config)
        
        # Set status and notify startup
        metrics.set_chat_status("✅ Online")
        if telegram:
            url = f"http://{config.chat_api_host}:{config.chat_api_port}"
            telegram.notify_startup_sync("Chat API", config.chat_api_host, config.chat_api_port, url)
        
        print(f"Starting Chat API on {config.chat_api_host}:{config.chat_api_port}")
        
        # Run with uvicorn
        uvicorn.run(
            chat_api.app,
            host=config.chat_api_host,
            port=config.chat_api_port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nChat API shut down gracefully.")
        metrics.set_chat_status("⏹️ Stopped")
    except Exception as e:
        print(f"\nChat API crashed: {e}")
        metrics.set_chat_status("🔴 Crashed")
        if telegram:
            tb = traceback.format_exc()
            telegram.notify_crash_sync("Chat API", e, tb)
        sys.exit(1)


if __name__ == "__main__":
    main()
