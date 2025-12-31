module.exports = {
  apps: [
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
  ],

  // Global configuration
  instances: 1,
  exec_mode: "fork",
  max_memory_restart: "1G",
  autorestart: true,
  max_restarts: 10,
  min_uptime: "10s",
};
