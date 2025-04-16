"""
Database models for the Zenplify LLM Agent.

This module defines SQLAlchemy models for storing user profiles,
work experience, education, skills, and Q&A history.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, ForeignKey,
    Text, Date, JSON, func, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict

# Import base class
from src.database.session import Base

# Try to import pgvector if available (for vector embeddings)
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    VECTOR_AVAILABLE = False

# Define embedding dimension (based on the model used)
# e.g., 768 for BERT, 1536 for OpenAI's ada-002
EMBEDDING_DIMENSION = 768


class User(Base):
    """User model for storing profile information."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    address_json = Column(JSONB, nullable=True)  # Structured address components
    github_username = Column(String(255), nullable=True)
    github_profile_json = Column(JSONB, nullable=True)  # Cached GitHub profile data
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_experiences = relationship("WorkExperience", back_populates="user", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    qa_history = relationship("QAHistory", back_populates="user", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    qa_pairs = relationship("QAPair", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name}>"


class UserProfile(Base):
    """Extended user profile data stored as JSON."""
    
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    data = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile for User {self.user_id}>"


class WorkExperience(Base):
    """Work experience model for storing job history."""
    
    __tablename__ = "work_experiences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null for current jobs
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="work_experiences")

    def __repr__(self):
        return f"<WorkExperience {self.company_name} - {self.role}>"


class Education(Base):
    """Education model for storing educational history."""
    
    __tablename__ = "educations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    institution_name = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null for ongoing education
    grade = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="educations")

    def __repr__(self):
        return f"<Education {self.institution_name} - {self.degree}>"


class UserSkill(Base):
    """Skills model for storing user skills."""
    
    __tablename__ = "user_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "Programming Language", "Framework", "Soft Skill"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="skills")
    
    # Constraints
    __table_args__ = (
        Index('idx_user_skill_unique', user_id, skill_name, unique=True),
    )

    def __repr__(self):
        return f"<UserSkill {self.skill_name}>"


class QAHistory(Base):
    """Question and answer history for storing previously answered application questions."""
    
    __tablename__ = "qa_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    context_json = Column(JSONB, nullable=True)  # Additional context like company, job title
    source = Column(String(100), nullable=True)  # e.g., "Zenplify Capture", "Manual Entry"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Vector embedding for semantic search (only if pgvector is available)
    if VECTOR_AVAILABLE:
        question_embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)
        
        # Add vector index for fast similarity search
        __table_args__ = (
            Index('idx_question_embedding', question_embedding, postgresql_using='ivfflat'),
        )
    
    # Relationships
    user = relationship("User", back_populates="qa_history")

    def __repr__(self):
        return f"<QAHistory {self.question_text[:30]}...>"


class SavedJob(Base):
    """Saved job listings for tracking job applications."""
    
    __tablename__ = "saved_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=True)
    job_url = Column(String(512), nullable=True)
    application_date = Column(DateTime, nullable=True)  # Null if not applied yet
    status = Column(String(50), nullable=False, default="Saved")  # "Saved", "Applied", "Interviewing", etc.
    saved_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="saved_jobs")

    def __repr__(self):
        return f"<SavedJob {self.company_name} - {self.job_title}>"


class QAPair(Base):
    """Question and answer pairs for application forms."""
    
    __tablename__ = "qa_pairs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context = Column(JSONB, nullable=True)  # Context info like company, job
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="qa_pairs")
    
    def __repr__(self):
        return f"<QAPair {self.question[:30]}...>"


class Company(Base):
    """Company information for job applications."""
    
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    website = Column(String(512), nullable=True)
    industry = Column(String(255), nullable=True)
    size = Column(String(100), nullable=True)  # E.g., "1-10", "11-50", "51-200", etc.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company {self.name}>"


class Job(Base):
    """Job listing information."""
    
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    status = Column(String(50), nullable=False, default="Saved")  # "Saved", "Applied", "Interviewing", etc.
    applied_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")
    
    def __repr__(self):
        return f"<Job {self.title}>" 