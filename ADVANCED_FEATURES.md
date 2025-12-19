# ZAS Advanced Features

Complete guide for AI Orchestration and Web Dashboard features.

## 🤖 AI Orchestration System

### Overview
The AI Orchestration system enables multi-agent evaluation of responses to ensure quality and accuracy. Multiple AI evaluators review each response and reach consensus on the best answer.

### Features
- **Multi-Agent Evaluation**: 3+ AI agents evaluate each response
- **Consensus Scoring**: Aggregate scores from all evaluators
- **Quality Criteria**: Accuracy, Completeness, Clarity, Efficiency, Safety
- **Automatic Improvement**: Suggests and applies improvements to responses
- **Decision Reasoning**: Transparent explanation of evaluation process

### Configuration

Add to `.env`:
```bash
# Enable orchestration
ORCHESTRATION_ENABLED=true
NUM_EVALUATOR_AGENTS=3

# Optional: Anthropic API key for advanced evaluation
ANTHROPIC_API_KEY=your-api-key-here
```

### Usage

The orchestration system integrates automatically with Chat API when enabled:

```python
from src.zas.orchestration import create_orchestrator
from src.zas.agents import ZASAgent
from src.zas.agents.mcp_client import get_mcp_client

# Create orchestrated agent
mcp_client = get_mcp_client()
agent = ZASAgent(mcp_client)

orchestrator = create_orchestrator(
    primary_agent_runner=agent.run,
    anthropic_api_key="sk-ant-...",  # Optional
    num_evaluators=3
)

# Run with orchestration
result = orchestrator.run_with_orchestration(
    "Your question here",
    "conversation-123"
)

# Result includes:
# - response: Final answer
# - consensus_score: 0.0-1.0
# - decision_reasoning: Explanation
# - evaluations: Individual evaluator scores
```

### Evaluation Criteria

Each response is scored on:
1. **Accuracy** (0.0-1.0): Correctness of information
2. **Completeness** (0.0-1.0): How fully it answers the question
3. **Clarity** (0.0-1.0): Readability and structure
4. **Efficiency** (0.0-1.0): Conciseness without losing information
5. **Safety** (0.0-1.0): No harmful or inappropriate content

### Example Output

```
Consensus Score: 0.85/1.0
Evaluations: 3 evaluators reviewed the response

Criteria Scores:
  • Accuracy: 0.90
  • Completeness: 0.80
  • Clarity: 0.85
  • Efficiency: 0.88
  • Safety: 1.00

Suggested Improvements: 2
  • Add specific ticket numbers for reference
  • Include troubleshooting steps

✅ Response approved
```

---

## 🌐 Web Dashboard

### Overview
Full-featured web interface for monitoring, controlling, and analyzing your ZAS system with authentication and detailed analytics.

### Features

#### 🔐 **Authentication System**
- Username/password login
- Session management with cookies
- SQLite database for user storage
- Default admin account (admin/admin123)

#### 📊 **Dashboard Pages**

1. **Home** (`/`)
   - Real-time service metrics
   - Request counters for all services
   - System uptime and status
   - Quick stats overview

2. **Tools** (`/tools`)
   - List of available ZAS tools
   - Execute tools directly from UI
   - Tool usage statistics
   - Success/error rates
   - Average execution times

3. **Logs** (`/logs`)
   - Recent activity logs
   - User actions
   - Service operations
   - IP addresses and user agents
   - Filterable and sortable

4. **Analytics** (`/analytics`)
   - Interactive charts (Chart.js)
   - User activity graphs
   - Tool usage pie charts
   - Detailed statistics tables
   - "Who used the most" rankings

#### 📈 **Analytics & Insights**
- Total users, activities, executions
- Per-user statistics
- Tool popularity and performance
- Success rates and error tracking
- Time-based trends

### Quick Start

```bash
# 1. Ensure dependencies are installed
pip install -r requirements.txt

# 2. Configure .env
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000

# 3. Start the ecosystem (includes dashboard)
./start_ecosystem.sh

# 4. Access dashboard
open http://localhost:5000

# 5. Login with default credentials
Username: admin
Password: admin123
```

### Database Schema

The dashboard uses SQLite with these tables:

```sql
- users: User accounts and authentication
- sessions: Login sessions with expiration
- activity_logs: All user actions and events
- tool_executions: Tool execution history with timing
- conversations: Chat conversation tracking
- messages: Individual messages with consensus scores
```

### Creating Users

```python
from src.zas.dashboard import get_database

db = get_database()

# Create new user
user_id = db.create_user(
    username="john",
    password="secure_password",
    email="john@example.com",
    is_admin=False
)

# Create admin user
admin_id = db.create_user(
    username="superadmin",
    password="very_secure",
    is_admin=True
)
```

### API Endpoints

The dashboard exposes REST APIs:

```bash
# Get metrics (requires authentication)
GET /api/metrics

# Get statistics
GET /api/stats

# Execute a tool
POST /api/tool/execute
{
  "tool_name": "search_tickets",
  "parameters": {"query": "urgent"}
}
```

### Security Features

- **Password Hashing**: SHA256 with salt
- **Session Tokens**: Secure random tokens
- **HTTP-Only Cookies**: XSS protection
- **Session Expiration**: 24-hour default
- **Activity Logging**: All actions tracked
- **IP Address Logging**: Security audit trail

### Customization

#### Change Dashboard Port

```bash
# In .env
DASHBOARD_PORT=8080
```

#### Customize Appearance

Edit templates in `src/zas/dashboard/templates/`:
- `base.html` - Layout and styling
- `index.html` - Home page
- `tools.html` - Tools page
- `logs.html` - Logs page
- `analytics.html` - Analytics page

#### Add Custom Charts

Edit `analytics.html` and add Chart.js charts:

```javascript
new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Mon', 'Tue', 'Wed'],
        datasets: [{
            label: 'Custom Metric',
            data: [12, 19, 3]
        }]
    }
});
```

### Integration with Services

All ZAS services automatically log to the dashboard:

```python
from src.zas.dashboard import get_database

db = get_database()

# Log activity
db.log_activity(
    user_id=1,
    action="ticket_created",
    service="zendesk",
    details="Created ticket #12345"
)

# Log tool execution
db.log_tool_execution(
    user_id=1,
    tool_name="search_tickets",
    parameters='{"query": "urgent"}',
    result='{"tickets": [...]}',
    status="success",
    execution_time_ms=250
)
```

### Monitoring

Check dashboard status:

```bash
./status_ecosystem.sh

# Output includes:
# Dashboard:
#   Status: ✅ Running
#   PID: 12345
#   Port: 5000
#   URL: http://0.0.0.0:5000
```

### Backup Database

```bash
# Backup SQLite database
cp zas_dashboard.db zas_dashboard_backup_$(date +%Y%m%d).db

# Or schedule with cron
0 2 * * * cp /path/to/zas_dashboard.db /backups/zas_$(date +\%Y\%m\%d).db
```

---

## 🚀 Complete System Architecture

```
┌─────────────────┐
│  Web Dashboard  │ ← Users login here
│   Port: 5000    │
└────────┬────────┘
         │
         ├──→ SQLite Database
         │    • Users & Auth
         │    • Activity Logs
         │    • Analytics
         │
┌────────┴────────┐
│  Chat API       │
│   Port: 3000    │ ← Optional: AI Orchestration
└────────┬────────┘
         │
    ┌────┴────┐
    │ MCP     │
    │ Server  │ ← Tools registered here
    │ 8000    │
    └─────────┘
```

---

## 📚 Complete Workflow

1. **Start System**: `./start_ecosystem.sh`
   - MCP Server (8000)
   - Chat API (3000)
   - MCP Proxy (8080)
   - Telegram Bot (optional)
   - **Dashboard (5000)** ← NEW!

2. **Access Dashboard**: http://localhost:5000

3. **Login**: admin / admin123

4. **Monitor Services**: Real-time metrics on home page

5. **Execute Tools**: Go to Tools page, click Execute

6. **View Logs**: Check Logs page for all activity

7. **Analyze Usage**: Analytics page shows charts and stats

8. **AI Orchestration** (optional): Enable for multi-agent evaluation

---

## 🎯 Use Cases

### For Developers
- Monitor service health and performance
- Debug tool executions
- Track error rates
- Analyze API usage patterns

### For Managers
- See who's using the system most
- Track tool popularity
- Monitor system uptime
- Generate usage reports

### For Operations
- Real-time service status
- Quick troubleshooting access
- Activity audit trail
- Performance metrics

---

## 🔧 Troubleshooting

### Dashboard Won't Start
```bash
# Check if port is in use
lsof -i:5000

# Check logs
tail -f logs/dashboard.log

# Verify dependencies
pip install jinja2
```

### Can't Login
```bash
# Reset database (creates new admin user)
rm zas_dashboard.db
python3 dashboard.py  # Will recreate with defaults
```

### Charts Not Showing
- Ensure internet connection (loads Chart.js from CDN)
- Check browser console for errors
- Clear browser cache

### Orchestration Not Working
```bash
# Enable in .env
ORCHESTRATION_ENABLED=true

# Optional: Add Anthropic API key for better evaluation
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## 📖 Additional Resources

- **Main README**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Telegram Setup**: [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)
- **Ecosystem Guide**: [ECOSYSTEM_GUIDE.md](ECOSYSTEM_GUIDE.md)
