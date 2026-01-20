# tools_admin.py - Admin utilities for org URLs and request pages

from datetime import datetime

from src.zas.core.database import Organisation, RequestLog, SessionLocal
from sqlalchemy import desc

from src.zas.core.helpers import mcp


@mcp.tool
def org_list_with_urls(limit: int = 100):
	"""List organisations with last known request URL.
	Returns: [{organisation_id, name, last_request_url}].
	"""
	with SessionLocal() as db:
		rows = db.query(Organisation).order_by(Organisation.organisation_id).limit(limit).all()
		return [
			{
				"organisation_id": r.organisation_id,
				"name": r.name,
				"last_request_url": r.last_request_url,
			}
			for r in rows
		]


@mcp.tool
def org_recent_pages(organisation_id: str, limit: int = 20):
	"""List recent request pages for an organisation from RequestLog.
	Returns: [{created_at, page_url, conversation_id}].
	"""
	if not organisation_id:
		return {"ok": False, "error": "organisation_id is required"}
	with SessionLocal() as db:
		rows = (
			db.query(RequestLog)
			.filter(RequestLog.organisation_id == organisation_id)
			.order_by(desc(RequestLog.created_at))
			.limit(limit)
			.all()
		)
		return [
			{
				"created_at": (
					r.created_at.isoformat()
					if isinstance(r.created_at, datetime) and r.created_at
					else None
				),
				"page_url": r.page_url,
				"conversation_id": r.conversation_id,
			}
			for r in rows
		]
