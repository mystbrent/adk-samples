"""
API router for the Zenplify LLM Agent.

This module defines FastAPI endpoints for interaction with the Zenplify Chrome extension.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

# Import local modules
from src.database.session import get_db
from src.schemas.autofill import (
    AutofillRequest,
    AutofillResponse,
    UnidentifiedFieldRequest, 
    UnidentifiedFieldSuggestion,
    SaveQAPairRequest,
)
from src.schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
)
from src.services.user_service import UserService
from src.services.autofill_service import AutofillService
from src.services.qa_service import QAService

# Create API router
router = APIRouter()

# User profile endpoints
@router.post("/users/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    user_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new user profile."""
    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a user profile by ID."""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: UUID,
    user_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update a user profile."""
    user_service = UserService(db)
    try:
        user = user_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Autofill endpoints
@router.post("/autofill/", response_model=AutofillResponse)
async def get_autofill_data(
    request: AutofillRequest,
    db: Session = Depends(get_db)
):
    """
    Get data for autofilling a job application form.
    
    This endpoint is called by the Zenplify extension when the user
    initiates an autofill action on a job application page.
    """
    autofill_service = AutofillService(db)
    try:
        autofill_data = autofill_service.get_autofill_data(
            user_id=request.user_id,
            context=request.context
        )
        return autofill_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the error
        raise HTTPException(status_code=500, detail="Failed to generate autofill data")

@router.post("/unidentified-fields/suggest/", response_model=UnidentifiedFieldSuggestion)
async def suggest_for_unidentified_field(
    request: UnidentifiedFieldRequest,
    db: Session = Depends(get_db)
):
    """
    Suggest an answer for an unidentified form field.
    
    This endpoint is called when Zenplify encounters a field it cannot
    map to the provided user data.
    """
    qa_service = QAService(db)
    try:
        suggestion = qa_service.suggest_answer(
            user_id=request.user_id,
            question=request.field_label,
            context=request.context
        )
        return suggestion
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the error
        raise HTTPException(status_code=500, detail="Failed to generate suggestion")

@router.post("/qa/save/", status_code=status.HTTP_201_CREATED)
async def save_qa_pair(
    request: SaveQAPairRequest,
    db: Session = Depends(get_db)
):
    """
    Save a new question-answer pair.
    
    This endpoint is called when a user provides or confirms an answer
    for an unidentified field.
    """
    qa_service = QAService(db)
    try:
        qa_service.save_qa_pair(
            user_id=request.user_id,
            question=request.question,
            answer=request.answer,
            context=request.context
        )
        return {"status": "success", "message": "Q&A pair saved successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the error
        raise HTTPException(status_code=500, detail="Failed to save Q&A pair") 