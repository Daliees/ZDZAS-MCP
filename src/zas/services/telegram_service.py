"""Telegram notification service for ZAS system monitoring."""

import asyncio
import logging
from typing import Optional
from datetime import datetime
import traceback

try:
    import telegram
    from telegram import Bot
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    telegram = None
    Bot = None
    Application = None
    CommandHandler = None
    ContextTypes = None

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending Telegram notifications."""
    
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        """
        Initialize Telegram service.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to send messages to
            enabled: Whether notifications are enabled
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled and TELEGRAM_AVAILABLE
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        if self.enabled:
            try:
                self.bot = Bot(token=bot_token)
                logger.info("Telegram service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        elif not TELEGRAM_AVAILABLE:
            logger.warning("Telegram library not installed. Install with: pip install python-telegram-bot")
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram.
        
        Args:
            message: Message text to send
            parse_mode: Parse mode (HTML, Markdown, or None)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled or not self.bot:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_message_sync(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram (synchronous wrapper).
        
        Args:
            message: Message text to send
            parse_mode: Parse mode (HTML, Markdown, or None)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message(message, parse_mode))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to send Telegram message (sync): {e}")
            return False
    
    async def notify_startup(self, service_name: str, host: str, port: int, url: Optional[str] = None):
        """
        Send startup notification.
        
        Args:
            service_name: Name of the service
            host: Host address
            port: Port number
            url: Optional full URL
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        url_info = f"\n🔗 URL: <code>{url}</code>" if url else ""
        
        message = f"""
🚀 <b>ZAS Service Started</b>

📦 Service: <b>{service_name}</b>
🕐 Time: {timestamp}
🌐 Host: <code>{host}</code>
🔌 Port: <code>{port}</code>{url_info}
✅ Status: <b>Online</b>
"""
        await self.send_message(message)
    
    def notify_startup_sync(self, service_name: str, host: str, port: int, url: Optional[str] = None):
        """Send startup notification (synchronous wrapper)."""
        if not self.enabled:
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.notify_startup(service_name, host, port, url))
            loop.close()
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    async def notify_crash(self, service_name: str, error: Exception, traceback_str: Optional[str] = None):
        """
        Send crash notification.
        
        Args:
            service_name: Name of the service that crashed
            error: The exception that occurred
            traceback_str: Optional traceback string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_msg = str(error)[:500]  # Limit error message length
        
        message = f"""
🔴 <b>ZAS Service Crash</b>

📦 Service: <b>{service_name}</b>
🕐 Time: {timestamp}
⚠️ Error: <code>{error_msg}</code>
"""
        
        if traceback_str:
            tb_preview = traceback_str[-1000:]  # Last 1000 chars of traceback
            message += f"\n📋 Traceback:\n<code>{tb_preview}</code>"
        
        await self.send_message(message)
    
    def notify_crash_sync(self, service_name: str, error: Exception, traceback_str: Optional[str] = None):
        """Send crash notification (synchronous wrapper)."""
        if not self.enabled:
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.notify_crash(service_name, error, traceback_str))
            loop.close()
        except Exception as e:
            logger.error(f"Failed to send crash notification: {e}")
    
    async def notify_error(self, service_name: str, message: str, details: Optional[str] = None):
        """
        Send error notification.
        
        Args:
            service_name: Name of the service
            message: Error message
            details: Optional additional details
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        notification = f"""
⚠️ <b>ZAS Service Error</b>

📦 Service: <b>{service_name}</b>
🕐 Time: {timestamp}
📝 Message: {message}
"""
        
        if details:
            notification += f"\n📋 Details:\n<code>{details[:500]}</code>"
        
        await self.send_message(notification)
    
    def notify_error_sync(self, service_name: str, message: str, details: Optional[str] = None):
        """Send error notification (synchronous wrapper)."""
        if not self.enabled:
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.notify_error(service_name, message, details))
            loop.close()
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    async def setup_bot_commands(self, metrics_callback):
        """
        Setup Telegram bot commands.
        
        Args:
            metrics_callback: Callback function that returns metrics dict
        """
        if not self.enabled or not TELEGRAM_AVAILABLE:
            return
        
        try:
            self.application = Application.builder().token(self.bot_token).build()
            
            async def status_command(update, context):
                """Handle /status command."""
                try:
                    metrics = metrics_callback()
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    message = f"""
📊 <b>ZAS System Status</b>

🕐 Time: {timestamp}
✅ Status: <b>Online</b>

📈 <b>Metrics:</b>
• MCP Requests: {metrics.get('mcp_requests', 0)}
• Chat Requests: {metrics.get('chat_requests', 0)}
• Proxy Requests: {metrics.get('proxy_requests', 0)}
• Total Requests: {metrics.get('total_requests', 0)}
• Uptime: {metrics.get('uptime', 'N/A')}

🔧 <b>Services:</b>
• MCP Server: {metrics.get('mcp_status', '❓')}
• Chat API: {metrics.get('chat_status', '❓')}
• MCP Proxy: {metrics.get('proxy_status', '❓')}
"""
                    await update.message.reply_text(message, parse_mode="HTML")
                except Exception as e:
                    await update.message.reply_text(f"Error retrieving status: {str(e)}")
            
            async def help_command(update, context):
                """Handle /help command."""
                message = """
<b>ZAS Bot Commands:</b>

/status - Show system status and metrics
/help - Show this help message

<b>About:</b>
ZAS (Zendesk Agent System) monitoring bot
"""
                await update.message.reply_text(message, parse_mode="HTML")
            
            # Register command handlers
            self.application.add_handler(CommandHandler("status", status_command))
            self.application.add_handler(CommandHandler("help", help_command))
            
            # Start bot in background
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram bot commands setup successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Telegram bot commands: {e}")
    
    def setup_bot_commands_sync(self, metrics_callback):
        """Setup Telegram bot commands (synchronous wrapper)."""
        if not self.enabled:
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.setup_bot_commands(metrics_callback))
            # Keep loop running for bot
            loop.run_forever()
        except Exception as e:
            logger.error(f"Failed to setup bot commands (sync): {e}")
    
    async def stop_bot(self):
        """Stop the Telegram bot."""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
    
    def stop_bot_sync(self):
        """Stop the Telegram bot (synchronous wrapper)."""
        if not self.application:
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stop_bot())
            loop.close()
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")


# Global Telegram service instance
_telegram_service: Optional[TelegramService] = None


def get_telegram_service(bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> Optional[TelegramService]:
    """
    Get or create the global Telegram service instance.
    
    Args:
        bot_token: Optional Telegram bot token
        chat_id: Optional Telegram chat ID
        
    Returns:
        TelegramService instance or None if not configured
    """
    global _telegram_service
    
    if _telegram_service is None and bot_token and chat_id:
        _telegram_service = TelegramService(bot_token, chat_id)
    
    return _telegram_service
