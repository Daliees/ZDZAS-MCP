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
      env: {
        OPENAI_API_KEY: "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",
        ZAS_MCP_SERVER_URL: "http://127.0.0.1:8000/mcp"
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
