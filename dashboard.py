"""
Dashboard application entry point.

This module starts the web dashboard for ZAS monitoring and control.
"""

import uvicorn

from src.zas.core import Config, get_config
from src.zas.dashboard import create_dashboard


def main():
    """Main entry point for the dashboard server."""
    config = get_config()
    dashboard = create_dashboard(config)
    
    dashboard_host = getattr(config, 'dashboard_host', '0.0.0.0')
    dashboard_port = getattr(config, 'dashboard_port', 5000)
    
    print(f"Starting ZAS Dashboard on {dashboard_host}:{dashboard_port}")
    print(f"Access at: http://{dashboard_host}:{dashboard_port}")
    print("Default credentials: admin / admin123")
    
    # Run with uvicorn
    uvicorn.run(
        dashboard.app,
        host=dashboard_host,
        port=dashboard_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
