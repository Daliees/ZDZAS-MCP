from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class SalesforceContext(BaseModel):
	orgId: Optional[str] = None
	userId: Optional[str] = None
	userName: Optional[str] = None
	userEmail: Optional[str] = None


class ChatRequest(BaseModel):
	message: str = Field(..., description="User message")
	conversationId: Optional[str] = Field(None, description="Conversation id om history te bewaren")
	tenantId: Optional[str] = None
	url: Optional[str] = None
	salesforceContext: Optional[SalesforceContext] = None


class ChatResponse(BaseModel):
	reply: str
	conversationId: str


class FeedbackItem(BaseModel):
	conversationId: str
	sessionId: Optional[str] = None
	userMessage: Optional[str] = None
	agentReply: str
	rating: Literal["good", "neutral", "bad"]
	createdAt: datetime


class ResetRequest(BaseModel):
	conversationId: Optional[str] = None


def estimate_tokens(message: str, reply: str) -> int:
	return max(1, int((len(message) + len(reply)) / 4))
