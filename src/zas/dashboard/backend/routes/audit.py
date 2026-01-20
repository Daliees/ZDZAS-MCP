"""Audit log API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc

from src.zas.core.database import AuditLog, SessionLocal

router = APIRouter()


class AuditLogResponse(BaseModel):
	"""Audit log response model."""

	id: str
	timestamp: datetime
	user_id: Optional[str] = None
	action: str
	resource_type: str
	resource_id: Optional[str] = None
	old_value: Optional[dict] = None
	new_value: Optional[dict] = None
	ip_address: Optional[str] = None
	success: bool
	error_message: Optional[str] = None

	class Config:
		from_attributes = True


@router.get("/", response_model=list[AuditLogResponse])
async def list_audit_logs(
	user_id: Optional[str] = Query(None, description="Filter by user"),
	action: Optional[str] = Query(None, description="Filter by action type"),
	resource_type: Optional[str] = Query(None, description="Filter by resource type"),
	start_date: Optional[datetime] = Query(None, description="Filter from date"),
	end_date: Optional[datetime] = Query(None, description="Filter to date"),
	limit: int = Query(100, le=1000),
	offset: int = Query(0, ge=0),
):
	"""List audit logs with filters. Audit logs are immutable."""
	with SessionLocal() as db:
		query = db.query(AuditLog)

		if user_id:
			query = query.filter(AuditLog.user_id == user_id)
		if action:
			query = query.filter(AuditLog.action == action)
		if resource_type:
			query = query.filter(AuditLog.resource_type == resource_type)
		if start_date:
			query = query.filter(AuditLog.timestamp >= start_date)
		if end_date:
			query = query.filter(AuditLog.timestamp <= end_date)

		query = query.order_by(desc(AuditLog.timestamp))
		query = query.limit(limit).offset(offset)

		logs = query.all()
		return [AuditLogResponse.from_orm(log) for log in logs]


@router.get("/{audit_id}", response_model=AuditLogResponse)
async def get_audit_log(audit_id: str):
	"""Get a specific audit log entry."""
	with SessionLocal() as db:
		log = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
		if not log:
			raise HTTPException(status_code=404, detail="Audit log not found")
		return AuditLogResponse.from_orm(log)
