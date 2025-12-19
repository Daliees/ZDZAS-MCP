#!/usr/bin/env python3
"""
Telegram bot runner for ZAS monitoring.

This script starts the Telegram bot that responds to /status commands.
Run this separately from the main services.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.zas.core import get_config
from src.zas.core.metrics import get_metrics
from src.zas.services.telegram_service import get_telegram_service


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\n🛑 Stopping Telegram bot...")
    sys.exit(0)


async def main():
    """Main entry point for Telegram bot."""
    print("🤖 Starting ZAS Telegram Bot...")
    
    # Load configuration
    config = get_config()
    
    if not config.telegram_enabled or not config.telegram_bot_token or not config.telegram_chat_id:
        print("❌ Telegram not configured. Set TELEGRAM_ENABLED=true, TELEGRAM_BOT_TOKEN, and TELEGRAM_CHAT_ID in .env")
        sys.exit(1)
    
    # Get services
    metrics = get_metrics()
    telegram = get_telegram_service(config.telegram_bot_token, config.telegram_chat_id)
    
    if not telegram or not telegram.enabled:
        print("❌ Failed to initialize Telegram service")
        sys.exit(1)
    
    print(f"✅ Telegram bot initialized")
    print(f"📱 Chat ID: {config.telegram_chat_id}")
    print(f"🤖 Bot token: {config.telegram_bot_token[:10]}...")
    print("\n📊 Bot Commands:")
    print("  /status - Show system status and metrics")
    print("  /help - Show help message")
    print("\nPress Ctrl+C to stop\n")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup and run bot
    try:
        await telegram.setup_bot_commands(lambda: metrics.get_metrics())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await telegram.stop_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
