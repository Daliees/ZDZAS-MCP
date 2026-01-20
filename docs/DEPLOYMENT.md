# ZDZAS-MCP Deployment Guide

## Prerequisites

- **Python**: 3.12+
- **Operating System**: Linux (tested on Ubuntu/Debian)
- **Network**: Ports 8000, 9000, 8080 available
- **Memory**: Minimum 1GB RAM recommended
- **Disk**: 500MB for application + logs

## Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd ZDZAS-MCP
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
```env
ZENDESK_EMAIL=your-email@example.com
ZENDESK_TOKEN=your-zendesk-api-token
ZENDESK_SUBDOMAIN=your-subdomain
```

### 5. Initialize Database
```bash
# Database is auto-created on first run
python3 -c "from src.zas.core.database import init_db; init_db()"
```

### 6. Run Application

**Option A: Both servers (recommended for development)**
```bash
python3 start_all.py
```

**Option B: Individual servers**
```bash
# Terminal 1 - MCP Server
python3 app.py

# Terminal 2 - Chat API
python3 chat_api.py
```

### 7. Verify Setup
```bash
# Test MCP Server
curl http://localhost:8000/mcp

# Test Chat API (requires auth)
curl -X POST http://localhost:9000/chat \
  -H "Content-Type: application/json" \
  -H "X-Salesforce-User-Id: test-user" \
  -H "X-Salesforce-Org-Id: test-org" \
  -d '{"message": "Hello"}'
```

## VS Code Debugging

### Setup
1. Open project in VS Code
2. Select Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose `.venv/bin/python`

### Debug Configurations
Press `F5` and select:
- **MCP Server**: Debug MCP tools
- **Chat API**: Debug API endpoints (with hot-reload)
- **Start All**: Debug both (multiprocessing)
- **Current File**: Debug any Python file

### Remote Debugging (SSH/Tunnel)
If using VS Code Remote:
1. Ensure `debugpy` is installed: `pip install debugpy`
2. Verify Python extension is installed on remote
3. Use individual debug configs (not "Start All")

## Production Deployment

### Using PM2 (Process Manager)

#### 1. Install PM2
```bash
npm install -g pm2
```

#### 2. Configure PM2
Already configured in `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: 'zas-mcp-server',
      script: 'app.py',
      interpreter: '.venv/bin/python',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'zas-chat-api',
      script: 'chat_api.py',
      interpreter: '.venv/bin/python',
      instances: 2,
      exec_mode: 'cluster',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
```

#### 3. Start with PM2
```bash
# Start all services
pm2 start ecosystem.config.js

# View status
pm2 status

# View logs
pm2 logs

# Monitor
pm2 monit

# Restart
pm2 restart all

# Stop
pm2 stop all

# Auto-start on boot
pm2 startup
pm2 save
```

### Using systemd

#### 1. Create Service Files

**MCP Server** (`/etc/systemd/system/zas-mcp.service`):
```ini
[Unit]
Description=ZAS MCP Server
After=network.target

[Service]
Type=simple
User=ryan
WorkingDirectory=/home/ryan/code/ZDZAS-MCP
Environment="PATH=/home/ryan/code/ZDZAS-MCP/.venv/bin"
ExecStart=/home/ryan/code/ZDZAS-MCP/.venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Chat API** (`/etc/systemd/system/zas-chat-api.service`):
```ini
[Unit]
Description=ZAS Chat API
After=network.target

[Service]
Type=simple
User=ryan
WorkingDirectory=/home/ryan/code/ZDZAS-MCP
Environment="PATH=/home/ryan/code/ZDZAS-MCP/.venv/bin"
ExecStart=/home/ryan/code/ZDZAS-MCP/.venv/bin/python chat_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable zas-mcp zas-chat-api
sudo systemctl start zas-mcp zas-chat-api

# Check status
sudo systemctl status zas-mcp
sudo systemctl status zas-chat-api

# View logs
sudo journalctl -u zas-mcp -f
sudo journalctl -u zas-chat-api -f
```

### Using Docker (Optional)

#### 1. Build Image
```bash
docker build -t zdzas-mcp .
```

#### 2. Run Container
```bash
docker run -d \
  --name zas-mcp \
  -p 8000:8000 \
  -p 9000:9000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  zdzas-mcp
```

## Reverse Proxy Setup (Nginx)

### Install Nginx
```bash
sudo apt-get install nginx
```

### Configure
Create `/etc/nginx/sites-available/zas`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # MCP Server
    location /mcp {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Chat API
    location /api {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # CORS
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
    }
}
```

### Enable and Restart
```bash
sudo ln -s /etc/nginx/sites-available/zas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Environment-Specific Configuration

### Development
```env
DEBUG=true
LOG_LEVEL=DEBUG
ZAS_CHAT_PORT=9000
```

### Staging
```env
DEBUG=false
LOG_LEVEL=INFO
ZAS_CHAT_PORT=9000
```

### Production
```env
DEBUG=false
LOG_LEVEL=WARNING
ZAS_CHAT_PORT=9000
# Add production-specific Zendesk/API credentials
```

## Monitoring & Logging

### Log Locations
- **Chat Events**: `logs/chat_events.jsonl`
- **Feedback**: `zas_feedback_log.jsonl`
- **Application**: stdout/stderr (captured by PM2/systemd)

### Log Rotation
```bash
# Install logrotate
sudo apt-get install logrotate

# Create config: /etc/logrotate.d/zas
/home/ryan/code/ZDZAS-MCP/logs/*.jsonl {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 ryan ryan
    sharedscripts
    postrotate
        pm2 reloadLogs
    endscript
}
```

### Health Checks
```bash
# Check if services are running
curl -f http://localhost:8000/mcp || echo "MCP Server down"
curl -f http://localhost:9000/ || echo "Chat API down"
```

## Backup & Recovery

### Database Backup
```bash
# Backup SQLite database
cp *.db backups/$(date +%Y%m%d_%H%M%S).db
```

### Full Backup
```bash
tar -czf zas-backup-$(date +%Y%m%d).tar.gz \
  .env \
  *.db \
  logs/ \
  zas_feedback_log.jsonl
```

### Restore
```bash
tar -xzf zas-backup-YYYYMMDD.tar.gz
```

## Troubleshooting

### Services Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check virtual environment
source .venv/bin/activate
which python  # Should point to .venv

# Check dependencies
pip list | grep -E "(fastmcp|fastapi|openai-agents)"

# Check .env file
cat .env | grep ZENDESK
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
lsof -i :9000

# Kill process
kill -9 <PID>
```

### Import Errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Database Errors
```bash
# Delete and recreate
rm *.db
python3 -c "from src.zas.core.database import init_db; init_db()"
```

## Security Checklist

- [ ] Change default Basic Auth credentials in `middleware.py`
- [ ] Set restrictive CORS origins (not `*`)
- [ ] Use HTTPS in production (via Nginx/reverse proxy)
- [ ] Restrict firewall to necessary ports only
- [ ] Keep `.env` file permissions at `600`
- [ ] Regularly rotate API tokens
- [ ] Enable rate limiting
- [ ] Set up fail2ban for brute force protection
- [ ] Monitor logs for suspicious activity

## Performance Tuning

### Chat API
- Increase uvicorn workers: `--workers 4`
- Enable connection pooling
- Consider Redis for session storage

### MCP Server
- Profile tool execution times
- Add caching for frequent queries
- Optimize database queries

### Database
- Add indexes for common queries
- Consider PostgreSQL for production
- Implement connection pooling

## Scaling Considerations

### Horizontal Scaling
- Run multiple Chat API instances behind load balancer
- Use shared database (PostgreSQL)
- Implement distributed caching (Redis)

### Vertical Scaling
- Increase server resources (CPU/RAM)
- Optimize code performance
- Use profiling tools

## Maintenance

### Regular Tasks
- **Daily**: Check logs for errors
- **Weekly**: Review performance metrics
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Database optimization, log cleanup

### Updates
```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart services
pm2 restart all
```

## Support

For issues and questions:
- Check logs in `logs/` directory
- Review error traces in terminal output
- Consult [ARCHITECTURE.md](ARCHITECTURE.md) for system overview
- Check [API.md](API.md) for endpoint documentation
