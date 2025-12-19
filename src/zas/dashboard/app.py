"""Web dashboard application for ZAS."""

import json
from datetime import datetime
from typing import Optional
from functools import wraps

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from ..core import Config
from ..core.metrics import get_metrics
from .database import get_database, Database


# Create templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))


class Dashboard:
    """Web dashboard for ZAS monitoring and control."""
    
    def __init__(self, config: Config, db: Database = None):
        """
        Initialize dashboard.
        
        Args:
            config: ZAS configuration
            db: Database instance (optional)
        """
        self.config = config
        self.db = db or get_database()
        self.app = FastAPI(title="ZAS Dashboard", version="1.0.0")
        
        # Try to mount static files, create if doesn't exist
        try:
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        except RuntimeError:
            pass
        
        self._setup_routes()
    
    def _get_current_user(self, session_token: Optional[str] = Cookie(None)) -> Optional[dict]:
        """Get current user from session token."""
        if not session_token:
            return None
        return self.db.validate_session(session_token)
    
    def _require_auth(self, user: Optional[dict] = Depends(lambda st=Cookie(None): st)) -> dict:
        """Require authentication."""
        session_token = user
        user_data = self._get_current_user(session_token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user_data
    
    def _setup_routes(self):
        """Setup all dashboard routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request, session_token: Optional[str] = Cookie(None)):
            """Dashboard home page."""
            user = self._get_current_user(session_token)
            if not user:
                return RedirectResponse(url="/login", status_code=302)
            
            # Get dashboard stats
            metrics = get_metrics().get_metrics()
            db_stats = self.db.get_dashboard_stats()
            
            return templates.TemplateResponse("index.html", {
                "request": request,
                "user": user,
                "metrics": metrics,
                "stats": db_stats,
            })
        
        @self.app.get("/login", response_class=HTMLResponse)
        async def login_page(request: Request):
            """Login page."""
            return templates.TemplateResponse("login.html", {"request": request})
        
        @self.app.post("/login")
        async def login(
            request: Request,
            username: str = Form(...),
            password: str = Form(...)
        ):
            """Handle login."""
            user = self.db.authenticate_user(username, password)
            
            if user:
                # Create session
                session_token = self.db.create_session(user['id'])
                
                # Log activity
                client_host = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                self.db.log_activity(
                    user['id'],
                    "login",
                    details=f"Logged in as {username}",
                    ip_address=client_host,
                    user_agent=user_agent
                )
                
                # Set cookie and redirect
                response = RedirectResponse(url="/", status_code=302)
                response.set_cookie(key="session_token", value=session_token, httponly=True, max_age=86400)
                return response
            else:
                return templates.TemplateResponse("login.html", {
                    "request": request,
                    "error": "Invalid username or password"
                }, status_code=401)
        
        @self.app.get("/logout")
        async def logout(session_token: Optional[str] = Cookie(None)):
            """Handle logout."""
            if session_token:
                self.db.delete_session(session_token)
            
            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie("session_token")
            return response
        
        @self.app.get("/tools", response_class=HTMLResponse)
        async def tools_page(request: Request, session_token: Optional[str] = Cookie(None)):
            """Tools/actions page."""
            user = self._get_current_user(session_token)
            if not user:
                return RedirectResponse(url="/login", status_code=302)
            
            # Get available tools (mock for now)
            tools = [
                {"name": "search_tickets", "description": "Search Zendesk tickets", "category": "Ticket"},
                {"name": "get_ticket", "description": "Get ticket details", "category": "Ticket"},
                {"name": "search_articles", "description": "Search knowledge base", "category": "Knowledge Base"},
                {"name": "create_jira_ticket", "description": "Create Jira ticket", "category": "Jira"},
                {"name": "search_confluence", "description": "Search Confluence", "category": "Confluence"},
                {"name": "generate_report", "description": "Generate ticket report", "category": "Reporting"},
            ]
            
            tool_stats = self.db.get_tool_stats()
            
            return templates.TemplateResponse("tools.html", {
                "request": request,
                "user": user,
                "tools": tools,
                "tool_stats": tool_stats,
            })
        
        @self.app.get("/logs", response_class=HTMLResponse)
        async def logs_page(request: Request, session_token: Optional[str] = Cookie(None)):
            """Activity logs page."""
            user = self._get_current_user(session_token)
            if not user:
                return RedirectResponse(url="/login", status_code=302)
            
            recent_logs = self.db.get_recent_activity(limit=100)
            
            return templates.TemplateResponse("logs.html", {
                "request": request,
                "user": user,
                "logs": recent_logs,
            })
        
        @self.app.get("/analytics", response_class=HTMLResponse)
        async def analytics_page(request: Request, session_token: Optional[str] = Cookie(None)):
            """Analytics and charts page."""
            user = self._get_current_user(session_token)
            if not user:
                return RedirectResponse(url="/login", status_code=302)
            
            user_stats = self.db.get_user_stats()
            tool_stats = self.db.get_tool_stats()
            dashboard_stats = self.db.get_dashboard_stats()
            
            return templates.TemplateResponse("analytics.html", {
                "request": request,
                "user": user,
                "user_stats": user_stats,
                "tool_stats": tool_stats,
                "dashboard_stats": dashboard_stats,
            })
        
        @self.app.get("/api/metrics")
        async def api_metrics(user: dict = Depends(self._require_auth)):
            """API endpoint for metrics."""
            metrics = get_metrics().get_metrics()
            return JSONResponse(metrics)
        
        @self.app.get("/api/stats")
        async def api_stats(user: dict = Depends(self._require_auth)):
            """API endpoint for dashboard stats."""
            stats = self.db.get_dashboard_stats()
            return JSONResponse(stats)
        
        @self.app.post("/api/tool/execute")
        async def api_execute_tool(
            request: Request,
            user: dict = Depends(self._require_auth)
        ):
            """API endpoint to execute a tool."""
            data = await request.json()
            tool_name = data.get("tool_name")
            parameters = data.get("parameters", {})
            
            # Log the execution attempt
            self.db.log_activity(
                user['id'],
                "tool_execution",
                details=f"Executing {tool_name}",
                service="dashboard"
            )
            
            try:
                # Mock execution for now
                import time
                start = time.time()
                result = {
                    "status": "success",
                    "message": f"Tool {tool_name} executed successfully",
                    "data": {"mock": True}
                }
                execution_time = int((time.time() - start) * 1000)
                
                # Log execution
                self.db.log_tool_execution(
                    user['id'],
                    tool_name,
                    json.dumps(parameters),
                    json.dumps(result),
                    status="success",
                    execution_time_ms=execution_time
                )
                
                return JSONResponse(result)
            except Exception as e:
                self.db.log_tool_execution(
                    user['id'],
                    tool_name,
                    json.dumps(parameters),
                    str(e),
                    status="error"
                )
                return JSONResponse({
                    "status": "error",
                    "message": str(e)
                }, status_code=500)


def create_dashboard(config: Config = None, db: Database = None) -> Dashboard:
    """
    Create dashboard instance.
    
    Args:
        config: Optional configuration
        db: Optional database instance
        
    Returns:
        Configured Dashboard instance
    """
    if config is None:
        from ..core import get_config
        config = get_config()
    
    return Dashboard(config, db)
