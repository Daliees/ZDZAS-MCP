"""Test configuration and shared fixtures"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.zas.core.database import Base


@pytest.fixture
def db_session():
	"""Create a test database session"""
	engine = create_engine("sqlite:///:memory:")
	Base.metadata.create_all(engine)
	SessionLocal = sessionmaker(bind=engine)
	session = SessionLocal()
	try:
		yield session
	finally:
		session.close()


@pytest.fixture
def api_client():
	"""Create a test client for the chat API"""
	from chat_api import app

	return TestClient(app)


@pytest.fixture
def mock_zendesk_response():
	"""Mock Zendesk API response"""
	return {
		"tickets": [
			{
				"id": 123,
				"subject": "Test ticket",
				"status": "open",
				"priority": "normal",
				"created_at": "2026-01-20T10:00:00Z",
			}
		]
	}


@pytest.fixture
def mock_openai_response():
	"""Mock OpenAI API response"""
	return {
		"id": "msg_123",
		"role": "assistant",
		"content": [{"type": "text", "text": "This is a test response"}],
	}
