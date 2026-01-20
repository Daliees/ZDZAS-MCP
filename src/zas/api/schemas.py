from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SalesforceContext(BaseModel):
	orgId: str | None = None
	userId: str | None = None
	userName: str | None = None
	userEmail: str | None = None


class ChatRequest(BaseModel):
	message: str = Field(..., description="User message")
	conversationId: str | None = Field(None, description="Conversation id om history te bewaren")
	tenantId: str | None = None
	url: str | None = None
	salesforceContext: SalesforceContext | None = None


class ChatResponse(BaseModel):
	reply: str
	conversationId: str


class FeedbackItem(BaseModel):
	conversationId: str
	sessionId: str | None = None
	userMessage: str | None = None
	agentReply: str
	rating: Literal["good", "neutral", "bad"]
	createdAt: datetime


class ResetRequest(BaseModel):
	conversationId: str | None = None


def estimate_tokens(message: str, reply: str) -> int:
	return max(1, int((len(message) + len(reply)) / 4))
