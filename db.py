import os
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_URL = os.getenv("ZAS_DB_URL", "sqlite:///./zas.db")
engine = create_engine(DB_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class Organisation(Base):
    __tablename__ = "organisations"

    organisation_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
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


def init_db() -> None:
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def upsert_entities(session, organisation_id: Optional[str], organisation_name: Optional[str], user_id: Optional[str], user_name: Optional[str]) -> None:
    """Ensure organisation and user records exist and are updated."""
    if organisation_id:
        org = session.get(Organisation, organisation_id)
        if not org:
            org = Organisation(organisation_id=organisation_id, name=organisation_name or organisation_id)
            session.add(org)
        elif organisation_name and org.name != organisation_name:
            org.name = organisation_name

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
