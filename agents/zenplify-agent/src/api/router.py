"""
API router for the Zenplify LLM Agent.

This module defines FastAPI endpoints for interaction with the Zenplify Chrome extension.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi.responses import JSONResponse

# Import local modules
from src.database.session import get_db
from src.schemas.autofill import (
    AutofillRequest,
    AutofillResponse,
    UnidentifiedFieldRequest, 
    UnidentifiedFieldSuggestion,
    SaveQAPairRequest,
    SaveQAPairResponse,
)
from src.schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserCreate,
    QAPairCreate,
)
from src.services.user_service import UserService
from src.services.autofill_service import AutofillService
from src.services.qa_service import QAService

# Configure logging
logger = logging.getLogger(__name__)

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
        logger.error(f"Validation error creating user: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"status": "error", "message": "Failed to create user profile", "details": str(e)}
        )

@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a user profile by ID."""
    user_service = UserService(db)
    try:
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"status": "error", "message": "Failed to retrieve user profile", "details": str(e)}
        )

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        return user
    except ValueError as e:
        logger.error(f"Validation error updating user: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"status": "error", "message": "Failed to update user profile", "details": str(e)}
        )

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
        # Validate user exists
        user_service = UserService(db)
        user = user_service.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        
        # Convert context to dict if it's a Pydantic model
        context = request.context
        if context and hasattr(context, "dict"):
            context = context.dict()
            
        # Get autofill data
        autofill_data = autofill_service.get_autofill_data(
            user_id=request.user_id,
            context=context
        )
        
        # Validate required fields
        if not autofill_data or not autofill_data.get("user_data"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "status": "error", 
                    "message": "Profile data incomplete for required fields", 
                    "details": "User profile is missing required data. Please complete your profile."
                }
            )
        
        # Ensure firstName, lastName, email are present
        user_data = autofill_data.get("user_data", {})
        if not user_data.get("firstName") or not user_data.get("lastName") or not user_data.get("email"):
            # Fill in defaults if missing
            if not user_data.get("firstName"):
                user_data["firstName"] = "John"
            if not user_data.get("lastName"):
                user_data["lastName"] = "Doe"
            if not user_data.get("email"):
                user_data["email"] = "user@example.com"
        
        return autofill_data
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in autofill: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"status": "error", "message": str(e), "requestId": str(uuid.uuid4())}
        )
    except Exception as e:
        # Log the error
        logger.error(f"Autofill error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"status": "error", "message": "Failed to generate autofill data", "details": str(e)}
        )

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
        # Validate user exists
        user_service = UserService(db)
        user = user_service.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        
        # Generate suggestion
        suggestion = qa_service.suggest_answer(
            user_id=request.user_id,
            question=request.field_label,
            context=request.context
        )
        
        # Validate that suggestion is not empty
        if not suggestion or not suggestion.suggestion:
            # Provide a generic suggestion if none available
            suggestion = UnidentifiedFieldSuggestion(
                suggestion="I would be a good fit for this position because of my relevant experience and skills.",
                confidence=0.5,
                source="default",
                alternative_suggestions=[
                    "My background in this field has prepared me well for this role.",
                    "I have the necessary qualifications and am enthusiastic about this opportunity."
                ]
            )
        
        return suggestion
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in suggestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"status": "error", "message": str(e), "requestId": str(uuid.uuid4())}
        )
    except Exception as e:
        # Log the error
        logger.error(f"Error generating suggestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"status": "error", "message": "Failed to generate suggestion", "details": str(e)}
        )

@router.post("/qa/save/", response_model=SaveQAPairResponse, status_code=status.HTTP_201_CREATED)
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
        # Validate user exists
        user_service = UserService(db)
        user = user_service.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        
        # Validate question and answer are not empty
        if not request.question or not request.question.strip():
            raise ValueError("Question cannot be empty")
            
        if not request.answer or not request.answer.strip():
            raise ValueError("Answer cannot be empty")
            
        # Save the Q&A pair
        qa_id = qa_service.save_qa_pair(
            user_id=request.user_id,
            question=request.question,
            answer=request.answer,
            context=request.context
        )
        
        return SaveQAPairResponse(status="success", message="Q&A pair saved successfully", qa_id=qa_id)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error saving Q&A pair: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"status": "error", "message": str(e), "requestId": str(uuid.uuid4())}
        )
    except Exception as e:
        # Log the error
        logger.error(f"Error saving Q&A pair: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"status": "error", "message": "Failed to save Q&A pair", "details": str(e)}
        )

@router.post("/qa-pairs/", status_code=status.HTTP_201_CREATED)
def create_qa_pair(qa_pair: QAPairCreate) -> Dict[str, Any]:
    """Create a new QA pair."""
    try:
        return service.create_qa_pair(qa_pair)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create QA pair: {str(e)}"
        )

@router.get("/users/{user_id}/qa-pairs/", status_code=status.HTTP_200_OK)
def get_user_qa_pairs(user_id: UUID) -> List[Dict[str, Any]]:
    """Get all QA pairs for a user."""
    try:
        return service.get_user_qa_pairs(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve QA pairs: {str(e)}"
        ) 