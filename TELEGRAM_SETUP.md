# Telegram Bot Setup for ZAS Monitoring

## 🤖 Features

The Telegram bot provides real-time monitoring and notifications for your ZAS system:

- **Startup Notifications**: Get notified when services start with IP addresses and ports
- **Crash Alerts**: Instant notifications when any service crashes with error details
- **Status Command**: Check system status and request metrics via `/status`
- **Help Command**: Get bot information via `/help`

## 📋 Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Copy the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

**Option A: Using @userinfobot**
1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram
2. Start a chat with it
3. Copy your **chat ID** (a number like: `123456789`)

**Option B: Using your bot**
1. Start a chat with your newly created bot
2. Send any message to it
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789}` in the response

**Option C: For Group Chats**
1. Add your bot to a group
2. Send a message in the group
3. Visit the same URL as Option B
4. Look for the group chat ID (negative number like: `-987654321`)

### 3. Configure .env

Add these lines to your `.env` file:

```bash
# Telegram Notifications
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 4. Install Dependencies

```bash
pip install python-telegram-bot
```

Or reinstall all requirements:
```bash
pip install -r requirements.txt
```

### 5. Start the System

```bash
./start_ecosystem.sh
```

The ecosystem script will automatically start:
- MCP Server
- Chat API  
- MCP Proxy
- Telegram Bot (if configured)

## 📱 Bot Commands

Once running, send these commands to your bot:

- `/status` - Show system status and request metrics
- `/help` - Show help message

## 🔔 Notification Examples

### Startup Notification
```
🚀 ZAS Service Started

📦 Service: MCP Server
🕐 Time: 2025-12-19 15:30:45
🌐 Host: 127.0.0.1
🔌 Port: 8000
🔗 URL: http://127.0.0.1:8000/mcp
✅ Status: Online
```

### Crash Notification
```
🔴 ZAS Service Crash

📦 Service: Chat API
🕐 Time: 2025-12-19 15:35:20
⚠️ Error: Connection timeout
📋 Traceback:
  File "chat_api.py", line 45, in main
    ...
```

### Status Response
```
📊 ZAS System Status

🕐 Time: 2025-12-19 15:40:00
✅ Status: Online

📈 Metrics:
• MCP Requests: 127
• Chat Requests: 45
• Proxy Requests: 89
• Total Requests: 261
• Uptime: 2h 15m 30s

🔧 Services:
• MCP Server: ✅ Online
• Chat API: ✅ Online
• MCP Proxy: ✅ Online
```

## 🎮 Manual Bot Control

If you want to run the bot separately:

```bash
# Start bot only
python3 telegram_bot.py

# Check bot logs
tail -f logs/telegram_bot.log

# Stop bot
pkill -f telegram_bot.py
```

## 🐛 Troubleshooting

### Bot Not Responding

1. **Check if bot is running:**
   ```bash
   ./status_ecosystem.sh
   ```

2. **Check bot logs:**
   ```bash
   tail -f logs/telegram_bot.log
   ```

3. **Verify token and chat ID:**
   ```bash
   echo "Token: $TELEGRAM_BOT_TOKEN"
   echo "Chat ID: $TELEGRAM_CHAT_ID"
   ```

### Not Receiving Notifications

1. **Ensure TELEGRAM_ENABLED=true** in `.env`
2. **Check you've started a conversation** with the bot
3. **For groups:** Ensure bot has permission to send messages
4. **Test manually:**
   ```bash
   curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage \
     -d chat_id=<YOUR_CHAT_ID> \
     -d text="Test message"
   ```

### Import Error

If you see `ModuleNotFoundError: No module named 'telegram'`:

```bash
pip install python-telegram-bot
```

## 🔒 Security Tips

1. **Never commit** your bot token to git (it's in `.env` which is gitignored)
2. **Regenerate token** if accidentally exposed via @BotFather
3. **Use private chats** or restrict group access
4. **Monitor bot logs** for unauthorized access attempts

## 💡 Advanced Usage

### Custom Notifications

You can send custom notifications from anywhere in your code:

```python
from src.zas.services.telegram_service import get_telegram_service
from src.zas.core import get_config

config = get_config()
telegram = get_telegram_service(config.telegram_bot_token, config.telegram_chat_id)

if telegram:
    telegram.notify_error_sync(
        "Custom Service",
        "Something interesting happened",
        "Additional details here"
    )
```

### Disable Notifications

To temporarily disable without removing configuration:

```bash
# In .env
TELEGRAM_ENABLED=false
```

## 📚 Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [python-telegram-bot Library](https://github.com/python-telegram-bot/python-telegram-bot)
- [BotFather Commands](https://core.telegram.org/bots#6-botfather)
