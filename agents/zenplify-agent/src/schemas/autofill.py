"""
Autofill and Q&A schemas.

This module defines Pydantic models for validating autofill requests and responses,
as well as Q&A operations between the agent and Zenplify extension.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator

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
    education: Optional[str] = None  # Formatted as expected by Zenplify
    experience: Optional[str] = None  # Formatted as expected by Zenplify
    skills: Optional[str] = None  # Comma-separated list
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

class AutofillResponse(BaseModel):
    """Response model for autofill requests."""
    user_data: ZenplifyUserData
    
    @classmethod
    def from_user_profile(cls, profile, context=None):
        """
        Convert a user profile to Zenplify-compatible format.
        
        Args:
            profile: User profile data
            context: Optional context about the job
            
        Returns:
            AutofillResponse: Formatted data for Zenplify
        """
        # Name splitting logic (simple approach, can be enhanced)
        name_parts = profile.full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else "Doe"  # Default last name
        
        # Get current job if available
        current_job = None
        current_company = None
        for exp in profile.work_experiences:
            if exp.is_current:
                current_job = exp.role
                current_company = exp.company_name
                break
        
        # Format address components
        address_data = profile.address_json or {}
        
        # Build Zenplify data structure with proper handling of empty strings
        # For required fields, ensure they have non-empty values
        # For optional fields, use None instead of empty strings
        zenplify_data = ZenplifyUserData(
            firstName=first_name or "John",  # Default value if empty
            lastName=last_name or "Doe",     # Default value if empty
            email=profile.email or "user@example.com",  # Default value if empty
            phone=profile.phone if profile.phone else None,
            address=address_data.get('street1') or None,
            city=address_data.get('city') or None,
            state=address_data.get('state') or None,
            zip=address_data.get('postal_code') or None,
            country=address_data.get('country') or None,
            education=cls._format_education(profile.educations) or None,
            experience=cls._format_experience(profile.work_experiences) or None,
            skills=cls._format_skills(profile.skills) or None,
            linkedin=str(profile.linkedin_url) if profile.linkedin_url else None,
            github=f"https://github.com/{profile.github_username}" if profile.github_username else None,
            portfolio=str(profile.portfolio_url) if profile.portfolio_url else None,
            website=str(profile.website_url) if profile.website_url else None,
            company=current_company or None,
            currentJob=current_job or None,
        )
        
        return cls(user_data=zenplify_data)
    
    @staticmethod
    def _format_education(educations):
        """Format education history for Zenplify."""
        if not educations:
            return None
        formatted = ", ".join([f"{edu.degree} in {edu.field_of_study or 'N/A'} from {edu.institution_name}" 
                              for edu in educations])
        return formatted if formatted else None
    
    @staticmethod
    def _format_experience(experiences):
        """Format work experience for Zenplify."""
        if not experiences:
            return None
        formatted = ", ".join([f"{exp.role} at {exp.company_name}" for exp in experiences])
        return formatted if formatted else None
    
    @staticmethod
    def _format_skills(skills):
        """Format skills for Zenplify."""
        if not skills:
            return None
        formatted = ", ".join([skill.skill_name for skill in skills])
        return formatted if formatted else None

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