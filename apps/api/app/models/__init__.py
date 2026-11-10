"""
SQLAlchemy ORM Models
Defines all primary tables matching the OpenTrace database design specification.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Text,
    Integer,
    Index,
)
from sqlalchemy.orm import relationship
from apps.api.app.database.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_inv_id() -> str:
    return f"inv_{uuid.uuid4().hex[:12]}"


def datetime_now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime_now_utc, nullable=False)

    investigations = relationship("Investigation", back_populates="user", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="user")


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String(64), primary_key=True, default=generate_inv_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    search_type = Column(String(32), default="username", nullable=False)
    target_value = Column(String(255), nullable=False)
    status = Column(String(32), default="queued", nullable=False, index=True)
    options_json = Column(Text, nullable=True)
    total_sites_checked = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    inconclusive_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime_now_utc, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="investigations")
    search_inputs = relationship("SearchInput", back_populates="investigation", cascade="all, delete-orphan")
    profiles = relationship("Profile", back_populates="investigation", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="investigation", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="investigation")

    __table_args__ = (
        Index("ix_investigations_user_created", "user_id", "created_at"),
    )


class SearchInput(Base):
    __tablename__ = "search_inputs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(64), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    encrypted_value = Column(Text, nullable=False)
    input_type = Column(String(32), default="username", nullable=False)

    investigation = relationship("Investigation", back_populates="search_inputs")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(64), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(64), nullable=False, index=True)
    category = Column(String(32), default="other", nullable=False)
    username = Column(String(128), nullable=False, index=True)
    profile_url = Column(String(512), nullable=False)
    display_name = Column(String(255), nullable=True)
    biography = Column(Text, nullable=True)
    public_website = Column(String(512), nullable=True)
    profile_image_url = Column(String(512), nullable=True)
    location = Column(String(255), nullable=True)
    
    # 3 Independent confidence dimensions
    confidence_existence = Column(Float, default=0.0, nullable=False)
    confidence_data = Column(Float, default=0.0, nullable=False)
    identity_confidence = Column(Float, default=0.0, nullable=False)
    
    first_seen_at = Column(DateTime, default=datetime_now_utc, nullable=False)
    last_checked_at = Column(DateTime, default=datetime_now_utc, nullable=False)

    investigation = relationship("Investigation", back_populates="profiles")
    evidence_records = relationship("Evidence", back_populates="profile", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    source_url = Column(String(512), nullable=False)
    evidence_type = Column(String(64), default="profile_probe", nullable=False)
    detection_method = Column(String(64), nullable=False)
    verification_status = Column(String(32), nullable=False)
    confidence_score = Column(Float, default=0.0, nullable=False)
    adapter_version = Column(String(32), default="1.0.0", nullable=False)
    observed_at = Column(DateTime, default=datetime_now_utc, nullable=False)
    match_evidence = Column(Text, nullable=True)
    raw_data_json = Column(Text, nullable=True)

    profile = relationship("Profile", back_populates="evidence_records")


class Identifier(Base):
    __tablename__ = "identifiers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    identifier_type = Column(String(32), nullable=False) # username, email, phone, domain
    identifier_value = Column(String(255), nullable=False, index=True)
    visibility = Column(String(32), default="public", nullable=False)
    created_at = Column(DateTime, default=datetime_now_utc, nullable=False)


class ProfileIdentifier(Base):
    __tablename__ = "profile_identifiers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    identifier_id = Column(String(36), ForeignKey("identifiers.id", ondelete="CASCADE"), nullable=False)
    evidence_id = Column(String(36), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(64), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_profile_id = Column(String(64), nullable=False)
    target_profile_id = Column(String(64), nullable=False)
    relationship_type = Column(String(64), nullable=False)
    confidence_tier = Column(String(32), default="possible", nullable=False)
    confidence_score = Column(Float, default=0.0, nullable=False)
    evidence_reason = Column(Text, nullable=False)

    investigation = relationship("Investigation", back_populates="relationships")


class SiteModule(Base):
    __tablename__ = "site_modules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    platform = Column(String(64), unique=True, nullable=False)
    module_name = Column(String(64), nullable=False)
    category = Column(String(32), default="other", nullable=False)
    enabled = Column(Boolean, default=True)
    version = Column(String(32), default="1.0.0")
    last_tested_at = Column(DateTime, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    investigation_id = Column(String(64), ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime_now_utc, nullable=False)

    user = relationship("User", back_populates="audit_events")
    investigation = relationship("Investigation", back_populates="audit_events")

