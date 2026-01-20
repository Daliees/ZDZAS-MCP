# chat_api.py
from __future__ import annotations

import os
from pathlib import Path

from agents import TResponseInputItem
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.zas.api.logging_utils import setup_logging
from src.zas.api.middleware import setup_middleware
from src.zas.api.routes import create_router
from src.zas.core.database import init_db

# Load .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# Logging
logger, default_structured_log_path = setup_logging(Path(BASE_DIR))
STRUCTURED_LOG_PATH = os.getenv("ZAS_CHAT_JSONL", default_structured_log_path)

init_db()

# ---------------------------------------------------------------------------
# In-memory conversatiegeschiedenis
# ---------------------------------------------------------------------------

conversation_histories: dict[str, list[TResponseInputItem]] = {}

# Pad voor feedback-log (JSON Lines)
FEEDBACK_LOG_PATH = os.getenv("ZAS_FEEDBACK_LOG", "zas_feedback_log.jsonl")


# ---------------------------------------------------------------------------
# FastAPI app + CORS
# ---------------------------------------------------------------------------

app = FastAPI(
	title="ZAS Chat API",
	description="AI-powered chat assistant for Zendesk, Jira, Confluence, and Salesforce",
	version="1.0.0",
	docs_url="/docs",
	redoc_url="/redoc",
	openapi_url="/openapi.json",
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # voor productie strakker maken
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

setup_middleware(app, logger)

router = create_router(
	logger=logger,
	structured_log_path=STRUCTURED_LOG_PATH,
	feedback_log_path=FEEDBACK_LOG_PATH,
	conversation_histories=conversation_histories,
)

app.include_router(router)


# ---------------------------------------------------------------------------
# Entrypoint (standalone draaien)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
	import uvicorn

	port = int(os.getenv("ZAS_CHAT_PORT", "9000"))

	uvicorn.run(
		"chat_api:app",
		host="0.0.0.0",
		port=port,
		reload=True,
	)
