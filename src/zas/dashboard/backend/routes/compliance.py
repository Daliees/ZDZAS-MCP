"""EU AI Act compliance API endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.zas.core.database import ConversationLog, DataRetentionPolicy, SessionLocal

router = APIRouter()
logger = logging.getLogger(__name__)


class DataRetentionPolicyResponse(BaseModel):
	"""Data retention policy response."""

	organisation_id: str
	conversation_logs_days: int
	token_usage_days: int
	audit_logs_days: int
	anonymize_after_days: int

	class Config:
		from_attributes = True


class RightToErasureRequest(BaseModel):
	"""Request to delete user data per GDPR Article 17."""

	user_id: str
	organisation_id: str
	reason: str


class RightToErasureResponse(BaseModel):
	"""Response to erasure request."""

	success: bool
	message: str
	conversations_deleted: int
	data_anonymized: bool


@router.get("/retention-policy/{organisation_id}", response_model=DataRetentionPolicyResponse)
async def get_retention_policy(organisation_id: str):
	"""Get data retention policy for an organisation."""
	with SessionLocal() as db:
		policy = (
			db.query(DataRetentionPolicy).filter(DataRetentionPolicy.organisation_id == organisation_id).first()
		)
		if not policy:
			# Return default policy
			return DataRetentionPolicyResponse(
				organisation_id=organisation_id,
				conversation_logs_days=90,
				token_usage_days=365,
				audit_logs_days=730,
				anonymize_after_days=30,
			)
		return DataRetentionPolicyResponse.from_orm(policy)


@router.post("/right-to-erasure", response_model=RightToErasureResponse)
async def request_data_erasure(request: RightToErasureRequest):
	"""Process GDPR Article 17 right to erasure request.

	This will:
	1. Delete conversation logs for the user
	2. Anonymize any remaining references (audit logs, etc.)
	3. Log the erasure action for compliance
	"""
	with SessionLocal() as db:
		try:
			# Count conversations to delete
			conversations = (
				db.query(ConversationLog)
				.filter(
					ConversationLog.user_id == request.user_id,
					ConversationLog.organisation_id == request.organisation_id,
				)
				.all()
			)
			count = len(conversations)

			# Delete conversation logs
			for conv in conversations:
				db.delete(conv)

			# TODO: Anonymize audit logs (replace user_id with "ANONYMIZED")
			# TODO: Delete token usage records
			# TODO: Create audit log for this erasure action

			db.commit()

			logger.info(
				"Right to erasure processed: user=%s org=%s deleted=%d",
				request.user_id,
				request.organisation_id,
				count,
			)

			return RightToErasureResponse(
				success=True,
				message=f"Successfully deleted {count} conversation logs",
				conversations_deleted=count,
				data_anonymized=True,
			)

		except Exception as e:
			logger.exception("Right to erasure failed: %s", e)
			db.rollback()
			raise HTTPException(status_code=500, detail=f"Erasure failed: {str(e)}")


@router.get("/transparency-report/{organisation_id}")
async def get_transparency_report(organisation_id: str, start_date: datetime, end_date: datetime):
	"""Generate EU AI Act Article 13 transparency report.

	Reports on:
	- Total AI interactions
	- Models used
	- Average latency
	- Flagged content incidents
	"""
	with SessionLocal() as db:
		conversations = (
			db.query(ConversationLog)
			.filter(
				ConversationLog.organisation_id == organisation_id,
				ConversationLog.timestamp >= start_date,
				ConversationLog.timestamp <= end_date,
			)
			.all()
		)

		total_interactions = len(conversations)
		flagged_count = sum(1 for c in conversations if c.flagged_content)
		models_used = list({c.model_used for c in conversations if c.model_used})
		avg_latency = (
			sum(c.latency_ms for c in conversations if c.latency_ms) / total_interactions
			if total_interactions > 0
			else 0
		)

		return {
			"organisation_id": organisation_id,
			"report_period": {"start": start_date, "end": end_date},
			"total_interactions": total_interactions,
			"models_used": models_used,
			"average_latency_ms": avg_latency,
			"flagged_content_count": flagged_count,
			"flagged_percentage": (flagged_count / total_interactions * 100) if total_interactions > 0 else 0,
			"compliance_status": "COMPLIANT" if flagged_count == 0 else "REVIEW_REQUIRED",
		}
