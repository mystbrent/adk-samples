"""
User profile schemas.

This module defines Pydantic models for validating user profile data.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, HttpUrl, validator, Field

# Base models for reuse
class WorkExperienceBase(BaseModel):
    """Base model for work experience data."""
    company_name: str
    role: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None
    location: Optional[str] = None
    is_current: bool = False
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end_date is not before start_date."""
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('End date cannot be before start date')
        return v

class EducationBase(BaseModel):
    """Base model for education data."""
    institution_name: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    grade: Optional[str] = None
    description: Optional[str] = None
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end_date is not before start_date."""
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('End date cannot be before start date')
        return v

class UserSkillBase(BaseModel):
    """Base model for user skill data."""
    skill_name: str
    category: Optional[str] = None

class AddressBase(BaseModel):
    """Base model for address data."""
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

# Request models
class UserProfileCreate(BaseModel):
    """Model for creating a new user profile."""
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[AddressBase] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    work_experiences: Optional[List[WorkExperienceBase]] = []
    educations: Optional[List[EducationBase]] = []
    skills: Optional[List[UserSkillBase]] = []
    
class UserProfileUpdate(BaseModel):
    """Model for updating an existing user profile."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[AddressBase] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    work_experiences: Optional[List[WorkExperienceBase]] = None
    educations: Optional[List[EducationBase]] = None
    skills: Optional[List[UserSkillBase]] = None

# Response models
class WorkExperienceResponse(WorkExperienceBase):
    """Response model for work experience data."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class EducationResponse(EducationBase):
    """Response model for education data."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class UserSkillResponse(UserSkillBase):
    """Response model for user skill data."""
    id: UUID
    created_at: datetime
    
    class Config:
        orm_mode = True

class UserProfileResponse(BaseModel):
    """Response model for user profile data."""
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    address_json: Optional[Dict[str, Any]] = Field(None, alias="address")
    github_username: Optional[str] = None
    github_profile_json: Optional[Dict[str, Any]] = Field(None, alias="github_profile")
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    work_experiences: List[WorkExperienceResponse] = []
    educations: List[EducationResponse] = []
    skills: List[UserSkillResponse] = []
    
    @property
    def full_name(self) -> str:
        """Combine first_name and last_name into full_name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True 