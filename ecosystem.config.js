module.exports = {
  apps: [
    // MCP: alleen lokaal
    {
      name: "mcp-service",
      script: "app.py",
      cwd: "/home/meetmaxim/Code/DS/ZDZAS-MCP",
      interpreter: "/home/meetmaxim/Code/DS/ZDZAS-MCP/.venv/bin/python"
    },

    {
      name: "zas-all",
      script: "start_all.py",
      interpreter: "python",
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
      },
      error_file: "logs/zas-all-error.log",
      out_file: "logs/zas-all-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    },

    // Chat: publiek op netwerk
    {
      name: "chat-service",
      script: "uvicorn",
      args: "chat_api:app --host 0.0.0.0 --port 9000",
      cwd: "/home/meetmaxim/Code/DS/ZDZAS-MCP",
      interpreter: "/home/meetmaxim/Code/DS/ZDZAS-MCP/.venv/bin/python",
      env_file: ".env",  // Load environment variables from .env file
      env: {
        // Environment variables are now loaded from .env file
        // Add any PM2-specific overrides here if needed
      }
    }
  ],
  instances: 1,
  exec_mode: "fork",
  max_memory_restart: "1G",
  autorestart: true,
  max_restarts: 10,
  min_uptime: "10s",
};
