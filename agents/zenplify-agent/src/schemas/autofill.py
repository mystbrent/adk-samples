"""
Autofill and Q&A schemas.

This module defines Pydantic models for validating autofill requests and responses,
as well as Q&A operations between the agent and Zenplify extension.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator

# Import the detailed response schemas for embedding
from src.schemas.user import (
    WorkExperienceResponse,
    EducationResponse,
    UserSkillResponse,
)

class AutofillContext(BaseModel):
    """Context data for autofill requests."""
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    page_url: Optional[str] = None
    form_fields: Optional[List[str]] = None  # List of detected field names/labels

class AutofillRequest(BaseModel):
    """Request model for getting autofill data."""
    user_id: UUID
    context: Optional[AutofillContext] = None

class ZenplifyUserData(BaseModel):
    """
    Data structure expected by the Zenplify extension for autofill.
    
    This follows the format documented in the Zenplify API specification.
    """
    # Required fields - these should never be empty strings
    firstName: str
    lastName: str
    email: str
    
    # Optional fields - these can be null but not empty strings
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    education: Optional[List[EducationResponse]] = None  # Now a list of objects
    experience: Optional[List[WorkExperienceResponse]] = None  # Now a list of objects
    skills: Optional[List[UserSkillResponse]] = None  # Now a list of objects
    resume: Optional[str] = None  # URL to resume if available
    coverLetter: Optional[str] = None  # Text content if available
    linkedin: Optional[str] = None  # LinkedIn profile URL
    github: Optional[str] = None  # GitHub profile URL
    portfolio: Optional[str] = None  # Portfolio website URL
    website: Optional[str] = None  # Personal website URL
    company: Optional[str] = None  # Current company
    gender: Optional[str] = None  # If provided by user
    dateOfBirth: Optional[str] = None  # If provided by user, formatted as YYYY-MM-DD
    currentJob: Optional[str] = None  # Current job title
    
    @validator('*')
    def prevent_empty_strings(cls, v):
        """Validate that no field is an empty string."""
        if v == "":
            return None
        return v
    
    @validator('firstName', 'lastName', 'email')
    def validate_required_fields(cls, v):
        """Validate that required fields have values."""
        if v is None or v == "":
            raise ValueError("This field is required and cannot be empty")
        return v

    @staticmethod
    def _parse_education(educations: List[Any]) -> Optional[List[EducationResponse]]:
        """Convert DB Education models to EducationResponse schemas."""
        try:
            if not educations:
                return None
            return [EducationResponse.from_orm(edu) for edu in educations]
        except Exception as e:
            print(f"Error converting education data: {e}") # Replace with proper logging
            return None

    @staticmethod
    def _parse_experience(experiences: List[Any]) -> Optional[List[WorkExperienceResponse]]:
        """Convert DB WorkExperience models to WorkExperienceResponse schemas."""
        try:
            if not experiences:
                return None
            return [WorkExperienceResponse.from_orm(exp) for exp in experiences]
        except Exception as e:
            print(f"Error converting experience data: {e}") # Replace with proper logging
            return None

    @staticmethod
    def _parse_skills(skills: List[Any]) -> Optional[List[UserSkillResponse]]:
        """Convert DB UserSkill models to UserSkillResponse schemas."""
        try:
            if not skills:
                return None
            return [UserSkillResponse.from_orm(skill) for skill in skills]
        except Exception as e:
            print(f"Error converting skill data: {e}") # Replace with proper logging
            return None

class AutofillResponse(BaseModel):
    """Response model for autofill requests containing structured user data."""
    user_data: ZenplifyUserData

    class Config:
        # Ensure ORM mode is enabled if passing ORM objects directly to ZenplifyUserData
        orm_mode = True

class UnidentifiedFieldRequest(BaseModel):
    """Request model for unidentified field suggestions."""
    user_id: UUID
    field_label: str  # The label or name of the unidentified form field
    field_type: Optional[str] = None  # e.g., "text", "textarea", "select"
    surrounding_text: Optional[str] = None  # Text near the field to provide context
    context: Optional[Dict[str, Any]] = None  # Additional context like company name, job title

class UnidentifiedFieldSuggestion(BaseModel):
    """Response model for unidentified field suggestions."""
    suggestion: str
    confidence: float = Field(..., ge=0.0, le=1.0)  # Confidence score from 0 to 1
    source: str  # e.g., "qa_history", "profile_data", "llm_generation"
    alternative_suggestions: Optional[List[str]] = None
    
    @validator('suggestion')
    def suggestion_not_empty(cls, v):
        """Validate that suggestion is not empty."""
        if not v:
            raise ValueError("Suggestion cannot be empty")
        return v
    
    @validator('alternative_suggestions')
    def validate_alternatives(cls, v):
        """Validate that alternative suggestions are not empty."""
        if v is not None:
            return [alt for alt in v if alt]  # Filter out empty strings
        return v

class SaveQAPairRequest(BaseModel):
    """Request model for saving a new Q&A pair."""
    user_id: UUID
    question: str  # The question or field label
    answer: str  # The user-provided or confirmed answer
    context: Optional[Dict[str, Any]] = None  # Additional context like company name, job title
    
    @validator('question', 'answer')
    def fields_not_empty(cls, v):
        """Validate that question and answer are not empty."""
        if not v:
            raise ValueError("This field cannot be empty")
        return v

class SaveQAPairResponse(BaseModel):
    """Response model for saving a new Q&A pair."""
    status: str
    message: str
    qa_id: Optional[UUID] = None

class BatchUnidentifiedFieldItem(BaseModel):
    """Represents a single item in the batch suggestion request."""
    field_label: str
    context: Optional[Dict[str, Any]] = None

class BatchUnidentifiedFieldRequest(BaseModel):
    """Request model for batch unidentified field suggestions."""
    user_id: UUID
    requests: List[BatchUnidentifiedFieldItem]
    generate_alternatives: bool = False # Optional flag applies to all requests in the batch

class SuggestionError(BaseModel):
    """Model for representing an error during suggestion generation for a specific field."""
    field_label: str # To identify which request failed
    error: str
    details: Optional[str] = None

class BatchUnidentifiedFieldResponse(BaseModel):
    """Response model for batch unidentified field suggestions.
    
    Contains a list of results, where each item is either a successful 
    suggestion (UnidentifiedFieldSuggestion) or an error (SuggestionError).
    """
    results: List[Union[UnidentifiedFieldSuggestion, SuggestionError]]

class DirectLLMRequest(BaseModel):
    """Request model for LLM-based direct answer generation."""
    user_id: UUID
    question: str  # The question to be answered
    context: Optional[Dict[str, Any]] = None  # Additional context like company name, job title
    
    @validator('question')
    def question_not_empty(cls, v):
        """Validate that question is not empty."""
        if not v:
            raise ValueError("Question cannot be empty")
        return v

# --- Batch Direct LLM Schemas --- 

class BatchDirectLLMItem(BaseModel):
    """Represents a single item in the batch direct LLM suggestion request."""
    question: str
    context: Optional[Dict[str, Any]] = None
    
    @validator('question')
    def question_not_empty(cls, v):
        if not v:
            raise ValueError("Question cannot be empty")
        return v

class BatchDirectLLMRequest(BaseModel):
    """Request model for batch direct LLM suggestions."""
    user_id: UUID
    requests: List[BatchDirectLLMItem]
    generate_alternatives: bool = False # Optional flag applies to all requests in the batch

# We can reuse BatchUnidentifiedFieldResponse and SuggestionError for the response 