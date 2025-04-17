from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, validator, Field, EmailStr, UUID4
import uuid

class UserCreate(BaseModel):
    """Schema for creating a new user with validation."""
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    email: EmailStr = Field(...)
    githubUsername: Optional[str] = Field(None)
    linkedinUrl: Optional[str] = Field(None)

    @validator('firstName', 'lastName', 'githubUsername', 'linkedinUrl', pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    class Config:
        schema_extra = {
            "example": {
                "firstName": "Jane",
                "lastName": "Doe",
                "email": "jane.doe@example.com",
                "githubUsername": "janedoe",
                "linkedinUrl": "https://linkedin.com/in/janedoe"
            }
        }

class QAPairCreate(BaseModel):
    """Schema for creating a new QA pair with validation."""
    userId: UUID4
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    context: Optional[str] = None

    @validator('question', 'answer', 'context', pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    class Config:
        schema_extra = {
            "example": {
                "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "question": "What is your experience with Python?",
                "answer": "I have 5 years of experience with Python.",
                "context": "Technical skills section of resume"
            }
        }

class User(BaseModel):
    """Schema for a user."""
    id: UUID4
    firstName: str
    lastName: str
    email: EmailStr
    githubUsername: Optional[str] = None
    linkedinUrl: Optional[str] = None

class QAPair(BaseModel):
    """Schema for a QA pair."""
    id: UUID4
    userId: UUID4
    question: str
    answer: str
    context: Optional[str] = None 