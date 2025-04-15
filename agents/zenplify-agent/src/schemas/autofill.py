"""
Autofill and Q&A schemas.

This module defines Pydantic models for validating autofill requests and responses,
as well as Q&A operations between the agent and Zenplify extension.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field

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
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
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
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
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
        
        # Build Zenplify data structure
        zenplify_data = ZenplifyUserData(
            firstName=first_name,
            lastName=last_name,
            email=profile.email,
            phone=profile.phone,
            address=address_data.get('street1', ''),
            city=address_data.get('city', ''),
            state=address_data.get('state', ''),
            zip=address_data.get('postal_code', ''),
            country=address_data.get('country', ''),
            education=cls._format_education(profile.educations),
            experience=cls._format_experience(profile.work_experiences),
            skills=cls._format_skills(profile.skills),
            linkedin=str(profile.linkedin_url) if profile.linkedin_url else None,
            github=f"https://github.com/{profile.github_username}" if profile.github_username else None,
            portfolio=str(profile.portfolio_url) if profile.portfolio_url else None,
            website=str(profile.website_url) if profile.website_url else None,
            company=current_company,
            currentJob=current_job,
        )
        
        return cls(user_data=zenplify_data)
    
    @staticmethod
    def _format_education(educations):
        """Format education history for Zenplify."""
        # Implementation depends on Zenplify's expected format
        # This is a placeholder
        return ", ".join([f"{edu.degree} in {edu.field_of_study or 'N/A'} from {edu.institution_name}" 
                          for edu in educations])
    
    @staticmethod
    def _format_experience(experiences):
        """Format work experience for Zenplify."""
        # Implementation depends on Zenplify's expected format
        # This is a placeholder
        return ", ".join([f"{exp.role} at {exp.company_name}" for exp in experiences])
    
    @staticmethod
    def _format_skills(skills):
        """Format skills for Zenplify."""
        return ", ".join([skill.skill_name for skill in skills])

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

class SaveQAPairRequest(BaseModel):
    """Request model for saving a new Q&A pair."""
    user_id: UUID
    question: str  # The question or field label
    answer: str  # The user-provided or confirmed answer
    context: Optional[Dict[str, Any]] = None  # Additional context like company name, job title 