import os
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_URL = os.getenv("ZAS_DB_URL", "sqlite:///./zas.db")
engine = create_engine(DB_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class Organisation(Base):
	__tablename__ = "organisations"

	organisation_id = Column(String, primary_key=True)
	name = Column(String, nullable=True)
	last_request_url = Column(String, nullable=True)
	users = relationship("User", back_populates="organisation")
	requests = relationship("RequestLog", back_populates="organisation")


class User(Base):
	__tablename__ = "users"

	user_id = Column(String, primary_key=True)
	name = Column(String, nullable=True)
	organisation_id = Column(String, ForeignKey("organisations.organisation_id"), nullable=True)

	organisation = relationship("Organisation", back_populates="users")
	requests = relationship("RequestLog", back_populates="user")


class RequestLog(Base):
	__tablename__ = "request_logs"

	request_id = Column(String, primary_key=True)
	user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
	organisation_id = Column(String, ForeignKey("organisations.organisation_id"), nullable=True)
	conversation_id = Column(String, nullable=True)
	tenant_id = Column(String, nullable=True)
	page_url = Column(String, nullable=True)
	message = Column(Text, nullable=True)
	reply = Column(Text, nullable=True)
	tokens_used = Column(Integer, nullable=True)
	salesforce_org_id = Column(String, nullable=True)
	salesforce_user_id = Column(String, nullable=True)
	salesforce_user_name = Column(String, nullable=True)
	error = Column(Text, nullable=True)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

	user = relationship("User", back_populates="requests")
	organisation = relationship("Organisation", back_populates="requests")


class SalesforceSession(Base):
	__tablename__ = "salesforce_sessions"

	organisation_id = Column(String, ForeignKey("organisations.organisation_id"), primary_key=True)
	access_token = Column(Text, nullable=False)
	refresh_token = Column(Text, nullable=True)
	instance_url = Column(String, nullable=False)
	issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	expires_at = Column(DateTime, nullable=True)

	organisation = relationship("Organisation")


class SalesforceOAuthCredential(Base):
	__tablename__ = "salesforce_oauth_credentials"

	organisation_id = Column(String, ForeignKey("organisations.organisation_id"), primary_key=True)
	client_id = Column(String, nullable=False)
	client_secret = Column(String, nullable=False)
	refresh_token = Column(Text, nullable=False)
	instance_url = Column(String, nullable=True)
	issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	expires_at = Column(DateTime, nullable=True)

	organisation = relationship("Organisation")


class ConversationLog(Base):
	"""EU AI Act compliant conversation logging"""
	__tablename__ = "conversation_logs"

	id = Column(String, primary_key=True, default=lambda: str(uuid4()))
	organisation_id = Column(String, ForeignKey("organisations.organisation_id"), nullable=True)
	user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
	session_id = Column(String, nullable=False, index=True)
	timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
	input_prompt = Column(Text, nullable=False)  # Encrypted in production
	output_response = Column(Text, nullable=False)  # Encrypted in production
	tool_calls = Column(Text, nullable=True)  # JSON string of tools invoked
	input_tokens = Column(Integer, default=0)
	output_tokens = Column(Integer, default=0)
	total_tokens = Column(Integer, default=0)
	model_used = Column(String, default="gpt-4.1-mini")
	latency_ms = Column(Integer, nullable=True)
	flagged_content = Column(Boolean, default=False)
	flagged_reason = Column(String, nullable=True)
	ip_address = Column(String, nullable=True)  # Anonymized after retention period
	user_agent = Column(String, nullable=True)

	organisation = relationship("Organisation")
	user = relationship("User")


class TokenUsage(Base):
	"""Aggregated token usage for billing and monitoring"""
	__tablename__ = "token_usage"

	id = Column(Integer, primary_key=True, autoincrement=True)
	organisation_id = Column(String, ForeignKey("organisations.organisation_id"), nullable=False)
	user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
	date = Column(Date, nullable=False, index=True)
	model = Column(String, nullable=False)
	input_tokens = Column(Integer, default=0)
	output_tokens = Column(Integer, default=0)
	total_tokens = Column(Integer, default=0)
	total_requests = Column(Integer, default=0)
	average_latency_ms = Column(Float, nullable=True)
	cost_estimate = Column(Numeric(10, 4), default=Decimal("0.0000"))

	organisation = relationship("Organisation")
	user = relationship("User")


class AuditLog(Base):
	"""System-level audit trail"""
	__tablename__ = "audit_logs"

	id = Column(String, primary_key=True, default=lambda: str(uuid4()))
	timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
	user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
	action = Column(String, nullable=False)  # CRUD operation
	resource_type = Column(String, nullable=False)  # e.g., "conversation", "user", "organization"
	resource_id = Column(String, nullable=True)
	old_value = Column(Text, nullable=True)  # JSON
	new_value = Column(Text, nullable=True)  # JSON
	ip_address = Column(String, nullable=True)
	success = Column(Boolean, default=True)
	error_message = Column(Text, nullable=True)

	user = relationship("User")


class DataRetentionPolicy(Base):
	"""Configurable data retention per organization"""
	__tablename__ = "data_retention_policies"

	organisation_id = Column(String, ForeignKey("organisations.organisation_id"), primary_key=True)
	conversation_logs_days = Column(Integer, default=90)  # EU AI Act minimum
	token_usage_days = Column(Integer, default=365)
	audit_logs_days = Column(Integer, default=730)  # 2 years
	anonymize_after_days = Column(Integer, default=30)

	organisation = relationship("Organisation")


def init_db() -> None:
	"""Create tables if they don't exist."""
	Base.metadata.create_all(bind=engine)


def set_salesforce_session(
	session,
	organisation_id: str,
	access_token: str,
	instance_url: str,
	refresh_token: str | None = None,
	expires_at: datetime | None = None,
) -> None:
	"""Persist or update a Salesforce session for an organisation."""
	if not organisation_id:
		raise ValueError("organisation_id is required")
	if not access_token:
		raise ValueError("access_token is required")
	if not instance_url:
		raise ValueError("instance_url is required")

	org = session.get(Organisation, organisation_id)
	if not org:
		org = Organisation(organisation_id=organisation_id, name=organisation_id)
		session.add(org)

	row = session.get(SalesforceSession, organisation_id)
	if not row:
		row = SalesforceSession(organisation_id=organisation_id)
		session.add(row)

	row.access_token = access_token
	row.refresh_token = refresh_token
	row.instance_url = instance_url
	row.issued_at = datetime.utcnow()
	row.expires_at = expires_at
	session.commit()


def get_salesforce_session(session, organisation_id: str) -> SalesforceSession | None:
	"""Fetch the Salesforce session for an organisation if present."""
	if not organisation_id:
		return None
	return session.get(SalesforceSession, organisation_id)


def list_salesforce_sessions(session):
	"""List all stored Salesforce sessions (metadata only, no tokens)."""
	rows = session.query(SalesforceSession).all()
	return [
		{
			"organisation_id": r.organisation_id,
			"instance_url": r.instance_url,
			"issued_at": r.issued_at.isoformat() if r.issued_at else None,
			"expires_at": r.expires_at.isoformat() if r.expires_at else None,
		}
		for r in rows
	]


def set_salesforce_oauth_credentials(
	session,
	organisation_id: str,
	client_id: str,
	client_secret: str,
	refresh_token: str,
	instance_url: str | None = None,
	expires_at: datetime | None = None,
) -> None:
	"""Store OAuth client + refresh token for an organisation."""
	if not organisation_id:
		raise ValueError("organisation_id is required")
	if not client_id or not client_secret or not refresh_token:
		raise ValueError("client_id, client_secret and refresh_token are required")

	org = session.get(Organisation, organisation_id)
	if not org:
		org = Organisation(organisation_id=organisation_id, name=organisation_id)
		session.add(org)

	row = session.get(SalesforceOAuthCredential, organisation_id)
	if not row:
		row = SalesforceOAuthCredential(organisation_id=organisation_id)
		session.add(row)

	row.client_id = client_id
	row.client_secret = client_secret
	row.refresh_token = refresh_token
	row.instance_url = instance_url
	row.issued_at = datetime.utcnow()
	row.expires_at = expires_at
	session.commit()


def get_salesforce_oauth_credentials(
	session, organisation_id: str
) -> SalesforceOAuthCredential | None:
	"""Fetch OAuth client + refresh token for an organisation."""
	if not organisation_id:
		return None
	return session.get(SalesforceOAuthCredential, organisation_id)


def upsert_entities(
	session,
	organisation_id: str | None,
	organisation_name: str | None,
	user_id: str | None,
	user_name: str | None,
	organisation_url: str | None = None,
) -> None:
	"""Ensure organisation and user records exist and are updated."""
	if organisation_id:
		org = session.get(Organisation, organisation_id)
		if not org:
			org = Organisation(
				organisation_id=organisation_id,
				name=organisation_name or organisation_id,
				last_request_url=organisation_url,
			)
			session.add(org)
		elif organisation_name and org.name != organisation_name:
			org.name = organisation_name

		if organisation_url and org.last_request_url != organisation_url:
			org.last_request_url = organisation_url

	if user_id:
		usr = session.get(User, user_id)
		if not usr:
			usr = User(user_id=user_id, name=user_name or user_id, organisation_id=organisation_id)
			session.add(usr)
		else:
			if user_name and usr.name != user_name:
				usr.name = user_name
			if organisation_id and usr.organisation_id != organisation_id:
				usr.organisation_id = organisation_id

	session.commit()
