"""Admin Dashboard Backend API

Provides REST API endpoints for the admin dashboard to:
- View conversation logs
- Monitor token usage and costs
- Manage organizations and users
- View audit logs
- Generate compliance reports (EU AI Act)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.zas.core.database import init_db
from src.zas.dashboard.backend.routes import analytics, audit, compliance, conversations, organizations, users

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Initialize database on startup."""
	logger.info("Initializing dashboard database...")
	init_db()
	yield
	logger.info("Dashboard backend shutdown")


app = FastAPI(
	title="ZAS Admin Dashboard API",
	description="Admin dashboard for ZAS AI Agent - EU AI Act compliant",
	version="1.0.0",
	lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173"],  # Vite default port
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Register route modules
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["organizations"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])


@app.get("/health")
async def health_check():
	"""Health check endpoint."""
	return {"status": "healthy"}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(
		"src.zas.dashboard.backend.app:app",
		host="0.0.0.0",
		port=9001,
		reload=True,
	)
