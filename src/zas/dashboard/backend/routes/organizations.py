"""Organization management API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.zas.core.database import Organisation, SessionLocal

router = APIRouter()


class OrganisationResponse(BaseModel):
	"""Organisation response model."""

	organisation_id: str
	organisation_name: str
	organisation_url: Optional[str] = None
	created_at: Optional[str] = None

	class Config:
		from_attributes = True


@router.get("/", response_model=list[OrganisationResponse])
async def list_organisations(
	search: Optional[str] = Query(None, description="Search by name"),
	limit: int = Query(100, le=1000),
	offset: int = Query(0, ge=0),
):
	"""List all organisations."""
	with SessionLocal() as db:
		query = db.query(Organisation)

		if search:
			query = query.filter(Organisation.organisation_name.ilike(f"%{search}%"))

		query = query.limit(limit).offset(offset)
		organisations = query.all()
		return [OrganisationResponse.from_orm(org) for org in organisations]


@router.get("/{organisation_id}", response_model=OrganisationResponse)
async def get_organisation(organisation_id: str):
	"""Get a specific organisation."""
	with SessionLocal() as db:
		org = db.query(Organisation).filter(Organisation.organisation_id == organisation_id).first()
		if not org:
			raise HTTPException(status_code=404, detail="Organisation not found")
		return OrganisationResponse.from_orm(org)
