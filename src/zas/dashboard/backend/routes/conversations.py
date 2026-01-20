"""Conversation logs API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc

from src.zas.core.database import ConversationLog, SessionLocal

router = APIRouter()


class ConversationResponse(BaseModel):
	"""Conversation log response model."""

	id: str
	organisation_id: str
	user_id: str
	session_id: str
	timestamp: datetime
	input_prompt: str
	output_response: str
	tool_calls: Optional[dict] = None
	input_tokens: Optional[int] = None
	output_tokens: Optional[int] = None
	total_tokens: Optional[int] = None
	model_used: Optional[str] = None
	latency_ms: Optional[int] = None
	flagged_content: bool = False
	ip_address: Optional[str] = None

	class Config:
		from_attributes = True


@router.get("/", response_model=list[ConversationResponse])
async def list_conversations(
	organisation_id: Optional[str] = Query(None, description="Filter by organisation"),
	user_id: Optional[str] = Query(None, description="Filter by user"),
	start_date: Optional[datetime] = Query(None, description="Filter from date"),
	end_date: Optional[datetime] = Query(None, description="Filter to date"),
	limit: int = Query(100, le=1000, description="Max results"),
	offset: int = Query(0, ge=0, description="Pagination offset"),
):
	"""List conversation logs with optional filters."""
	with SessionLocal() as db:
		query = db.query(ConversationLog)

		if organisation_id:
			query = query.filter(ConversationLog.organisation_id == organisation_id)
		if user_id:
			query = query.filter(ConversationLog.user_id == user_id)
		if start_date:
			query = query.filter(ConversationLog.timestamp >= start_date)
		if end_date:
			query = query.filter(ConversationLog.timestamp <= end_date)

		query = query.order_by(desc(ConversationLog.timestamp))
		query = query.limit(limit).offset(offset)

		conversations = query.all()
		return [ConversationResponse.from_orm(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
	"""Get a specific conversation by ID."""
	with SessionLocal() as db:
		conversation = db.query(ConversationLog).filter(ConversationLog.id == conversation_id).first()
		if not conversation:
			raise HTTPException(status_code=404, detail="Conversation not found")
		return ConversationResponse.from_orm(conversation)
