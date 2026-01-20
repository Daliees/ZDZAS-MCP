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
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel

from src.zas.core.database import SessionLocal, init_db
from src.zas.dashboard.backend.auth import authenticate_user, create_access_token, get_current_user, security
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


class LoginResponse(BaseModel):
	"""Login response model."""

	access_token: str
	token_type: str
	username: str


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(credentials: HTTPBasicCredentials = Depends(security)):
	"""Login endpoint - returns JWT token."""
	username = authenticate_user(credentials.username, credentials.password)
	if not username:
		raise HTTPException(status_code=401, detail="Invalid credentials")

	access_token = create_access_token(data={"sub": username}, expires_delta=timedelta(hours=8))
	return LoginResponse(access_token=access_token, token_type="bearer", username=username)


@app.get("/api/auth/verify")
async def verify_token(current_user: str = Depends(get_current_user)):
	"""Verify authentication token."""
	return {"username": current_user, "authenticated": True}


@app.get("/api/test/database")
async def test_database():
	"""Test database connectivity and return statistics."""
	try:
		from sqlalchemy import text
		
		with SessionLocal() as db:
			# Test basic query
			result = db.execute(text("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"))
			table_count = result.scalar()

			# Get table names
			result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
			tables = [row[0] for row in result.fetchall()]

			return {
				"status": "connected",
				"database": "sqlite",
				"table_count": table_count,
				"tables": tables,
			}
	except Exception as e:
		logger.exception("Database test failed")
		return {"status": "error", "message": str(e)}


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(
		"src.zas.dashboard.backend.app:app",
		host="0.0.0.0",
		port=9001,
		reload=True,
	)
