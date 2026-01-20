"""User management API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.zas.core.database import SessionLocal, User

router = APIRouter()


class UserResponse(BaseModel):
	"""User response model."""

	user_id: str
	user_name: str
	organisation_id: str
	created_at: Optional[str] = None

	class Config:
		from_attributes = True


@router.get("/", response_model=list[UserResponse])
async def list_users(
	organisation_id: Optional[str] = Query(None, description="Filter by organisation"),
	search: Optional[str] = Query(None, description="Search by name"),
	limit: int = Query(100, le=1000),
	offset: int = Query(0, ge=0),
):
	"""List all users with optional filters."""
	with SessionLocal() as db:
		query = db.query(User)

		if organisation_id:
			query = query.filter(User.organisation_id == organisation_id)
		if search:
			query = query.filter(User.user_name.ilike(f"%{search}%"))

		query = query.limit(limit).offset(offset)
		users = query.all()
		return [UserResponse.from_orm(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
	"""Get a specific user."""
	with SessionLocal() as db:
		user = db.query(User).filter(User.user_id == user_id).first()
		if not user:
			raise HTTPException(status_code=404, detail="User not found")
		return UserResponse.from_orm(user)
