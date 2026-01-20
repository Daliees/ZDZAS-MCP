"""Analytics and token usage API endpoints."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func

from src.zas.core.database import ConversationLog, SessionLocal, TokenUsage

router = APIRouter()


class TokenSummaryResponse(BaseModel):
	"""Token usage summary."""

	organisation_id: str
	date: date
	model: str
	input_tokens: int
	output_tokens: int
	total_tokens: int
	total_requests: int
	average_latency_ms: float
	cost_estimate: Decimal

	class Config:
		from_attributes = True


class AnalyticsSummary(BaseModel):
	"""Overall analytics summary."""

	total_conversations: int
	total_tokens: int
	total_cost_estimate: Decimal
	average_latency_ms: float
	unique_users: int
	unique_organisations: int


@router.get("/tokens", response_model=list[TokenSummaryResponse])
async def get_token_usage(
	organisation_id: Optional[str] = Query(None, description="Filter by organisation"),
	start_date: Optional[date] = Query(None, description="Filter from date"),
	end_date: Optional[date] = Query(None, description="Filter to date"),
	limit: int = Query(100, le=1000),
):
	"""Get token usage statistics."""
	with SessionLocal() as db:
		query = db.query(TokenUsage)

		if organisation_id:
			query = query.filter(TokenUsage.organisation_id == organisation_id)
		if start_date:
			query = query.filter(TokenUsage.date >= start_date)
		if end_date:
			query = query.filter(TokenUsage.date <= end_date)

		query = query.order_by(TokenUsage.date.desc())
		query = query.limit(limit)

		usage = query.all()
		return [TokenSummaryResponse.from_orm(u) for u in usage]


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
	organisation_id: Optional[str] = Query(None, description="Filter by organisation"),
	start_date: Optional[datetime] = Query(None, description="Filter from date"),
	end_date: Optional[datetime] = Query(None, description="Filter to date"),
):
	"""Get overall analytics summary."""
	with SessionLocal() as db:
		query = db.query(ConversationLog)

		if organisation_id:
			query = query.filter(ConversationLog.organisation_id == organisation_id)
		if start_date:
			query = query.filter(ConversationLog.timestamp >= start_date)
		if end_date:
			query = query.filter(ConversationLog.timestamp <= end_date)

		# Calculate aggregates
		total_conversations = query.count()

		total_tokens = db.query(func.sum(ConversationLog.total_tokens)).filter(
			ConversationLog.total_tokens.isnot(None)
		)
		if organisation_id:
			total_tokens = total_tokens.filter(ConversationLog.organisation_id == organisation_id)
		total_tokens = total_tokens.scalar() or 0

		# Get cost estimate from TokenUsage table
		cost_query = db.query(func.sum(TokenUsage.cost_estimate))
		if organisation_id:
			cost_query = cost_query.filter(TokenUsage.organisation_id == organisation_id)
		total_cost = cost_query.scalar() or Decimal("0.00")

		avg_latency = (
			db.query(func.avg(ConversationLog.latency_ms))
			.filter(ConversationLog.latency_ms.isnot(None))
			.scalar()
			or 0
		)

		unique_users = db.query(func.count(func.distinct(ConversationLog.user_id))).scalar() or 0

		unique_orgs = db.query(func.count(func.distinct(ConversationLog.organisation_id))).scalar() or 0

		return AnalyticsSummary(
			total_conversations=total_conversations,
			total_tokens=total_tokens,
			total_cost_estimate=total_cost,
			average_latency_ms=float(avg_latency),
			unique_users=unique_users,
			unique_organisations=unique_orgs,
		)
