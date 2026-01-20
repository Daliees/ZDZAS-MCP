"""Conversation logging utilities for EU AI Act compliance"""
import json
import time
from datetime import datetime
from typing import Any

from src.zas.core.database import ConversationLog, SessionLocal


def estimate_tokens(text: str) -> int:
	"""Rough token estimation (4 chars ≈ 1 token)"""
	return len(text) // 4


def log_conversation(
	session_id: str,
	organisation_id: str | None,
	user_id: str | None,
	input_prompt: str,
	output_response: str,
	tool_calls: list[str] | None = None,
	model_used: str = "gpt-4.1-mini",
	latency_ms: int | None = None,
	ip_address: str | None = None,
	user_agent: str | None = None,
	actual_tokens: dict[str, int] | None = None,
) -> str:
	"""
	Log a conversation to the database for EU AI Act compliance.
	
	Returns the conversation log ID.
	"""
	# Calculate tokens
	if actual_tokens:
		input_tokens = actual_tokens.get("input", 0)
		output_tokens = actual_tokens.get("output", 0)
		total_tokens = actual_tokens.get("total", input_tokens + output_tokens)
	else:
		input_tokens = estimate_tokens(input_prompt)
		output_tokens = estimate_tokens(output_response)
		total_tokens = input_tokens + output_tokens
	
	# Create log entry
	log_entry = ConversationLog(
		organisation_id=organisation_id,
		user_id=user_id,
		session_id=session_id,
		timestamp=datetime.utcnow(),
		input_prompt=input_prompt,  # TODO: Encrypt in production
		output_response=output_response,  # TODO: Encrypt in production
		tool_calls=json.dumps(tool_calls) if tool_calls else None,
		input_tokens=input_tokens,
		output_tokens=output_tokens,
		total_tokens=total_tokens,
		model_used=model_used,
		latency_ms=latency_ms,
		flagged_content=False,  # TODO: Add content moderation
		ip_address=ip_address,  # TODO: Anonymize after retention period
		user_agent=user_agent,
	)
	
	with SessionLocal() as db:
		db.add(log_entry)
		db.commit()
		db.refresh(log_entry)
		return log_entry.id


async def log_conversation_async(
	session_id: str,
	organisation_id: str | None,
	user_id: str | None,
	input_prompt: str,
	output_response: str,
	tool_calls: list[str] | None = None,
	model_used: str = "gpt-4.1-mini",
	latency_ms: int | None = None,
	ip_address: str | None = None,
	user_agent: str | None = None,
	actual_tokens: dict[str, int] | None = None,
) -> str:
	"""Async wrapper for conversation logging"""
	return log_conversation(
		session_id=session_id,
		organisation_id=organisation_id,
		user_id=user_id,
		input_prompt=input_prompt,
		output_response=output_response,
		tool_calls=tool_calls,
		model_used=model_used,
		latency_ms=latency_ms,
		ip_address=ip_address,
		user_agent=user_agent,
		actual_tokens=actual_tokens,
	)
