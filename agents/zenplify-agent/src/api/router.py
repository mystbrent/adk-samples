"""
API router for the Zenplify LLM Agent.

This module defines FastAPI endpoints for interaction with the Zenplify Chrome extension.
"""

import uuid
import logging
import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    ZenplifyUserData,
    DirectLLMRequest
)
from src.schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
)
from src.api.schemas import (
    UserCreate,
    QAPairCreate,
)
from src.services.user_service import UserService
from src.services.autofill_service import AutofillService
from src.services.qa_service import QAService
from src.services.llm_service import LLMService

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
            
        # Get autofill data (now returns a validated AutofillResponse object)
        autofill_data: AutofillResponse = autofill_service.get_autofill_data(
            user_id=request.user_id,
            context=context
        )
        
        # --- Simplified Validation ---
        # The service now returns a validated object.
        # Check if the object or its user_data is None (e.g., if service raised ValueError)
        if not autofill_data or not autofill_data.user_data:
             # This case might be less likely now if the service raises exceptions properly,
             # but it's good practice to check.
             logger.error(f"Autofill service returned empty data for user {request.user_id}")
             raise HTTPException(
                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                 detail={
                     "status": "error", 
                     "message": "Profile data incomplete or service error", 
                     "details": "User profile might be missing required data or an internal error occurred."
                 }
             )

        # Pydantic validation for required fields (firstName, lastName, email) 
        # happened inside the service when creating AutofillResponse. 
        # No need for redundant checks or defaulting here.
        
        # No need to convert empty strings or re-validate.
        
        # Return the fully validated AutofillResponse object directly
        return autofill_data
        
    except HTTPException:
        # Re-raise HTTPExceptions directly (e.g., 404 User not found)
        raise
    except ValueError as e:
        # Handle potential ValueErrors raised by the service (e.g., profile incomplete)
        logger.error(f"Validation error during autofill data generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"status": "error", "message": str(e), "requestId": str(uuid.uuid4())}
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected autofill error: {str(e)}", exc_info=True)
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
        
        # Generate suggestion (Add await here)
        suggestion = await qa_service.suggest_answer(
            user_id=request.user_id,
            question=request.field_label,
            context=request.context
        )
        
        # Validate that suggestion is not empty
        if not suggestion or not suggestion.get("suggestion"):
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
        else:
            # Convert the dict to UnidentifiedFieldSuggestion object
            suggestion = UnidentifiedFieldSuggestion(
                suggestion=suggestion.get("suggestion"),
                confidence=suggestion.get("confidence", 0.5),
                source=suggestion.get("source", "generated"),
                alternative_suggestions=suggestion.get("alternative_suggestions")
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
def create_qa_pair(qa_pair: QAPairCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Create a new QA pair."""
    qa_service = QAService(db)
    try:
        # Validate user exists
        user_service = UserService(db)
        user = user_service.get_user_by_id(qa_pair.userId)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        
        # Validate question and answer are not empty
        if not qa_pair.question or not qa_pair.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Question cannot be empty", "requestId": str(uuid.uuid4())}
            )
            
        if not qa_pair.answer or not qa_pair.answer.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "Answer cannot be empty", "requestId": str(uuid.uuid4())}
            )
        
        # Parse context properly
        context_dict = None
        if qa_pair.context:
            try:
                if isinstance(qa_pair.context, str) and qa_pair.context.strip():
                    # If it's a JSON string, try to parse it
                    if qa_pair.context[0] in ['{', '[']:
                        context_dict = json.loads(qa_pair.context)
                    else:
                        # Just a plain string, use as context
                        context_dict = {"context": qa_pair.context}
                elif isinstance(qa_pair.context, dict):
                    context_dict = qa_pair.context
            except json.JSONDecodeError:
                # If not valid JSON, use as plain text
                context_dict = {"context": qa_pair.context}
        
        # Create QA pair
        qa_data = qa_service.save_qa_pair(
            user_id=qa_pair.userId,
            question=qa_pair.question,
            answer=qa_pair.answer,
            context=context_dict
        )
        
        # Return in the format expected by the API Guide
        return {
            "status": "success",
            "message": "Q&A pair saved successfully",
            "qa_id": qa_data.get("id")
        }
        
    except ValueError as e:
        logger.error(f"Validation error creating QA pair: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": str(e), "requestId": str(uuid.uuid4())}
        )
    except Exception as e:
        logger.error(f"Error creating QA pair: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": f"Failed to create QA pair: {str(e)}", "requestId": str(uuid.uuid4())}
        )

@router.get("/users/{user_id}/qa-pairs/", status_code=status.HTTP_200_OK)
def get_user_qa_pairs(
    user_id: UUID, 
    question: Optional[str] = Query(None, description="Optional filter for similar questions"),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score for matching questions"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get QA pairs for a user with optional similarity search."""
    qa_service = QAService(db)
    try:
        # Validate user exists
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        
        # Get QA pairs from database
        if question:
            # If a question is provided, perform similarity search
            qa_pairs_result = qa_service.find_similar_questions(
                user_id=user_id, 
                question=question, 
                min_similarity=min_similarity, 
                limit=limit
            )
        else:
            # Otherwise get all QA pairs for the user (with a reasonable limit)
            qa_pairs_result = qa_service.find_similar_questions(
                user_id=user_id, 
                question="", 
                min_similarity=0, 
                limit=limit
            )
        
        # Format response according to API Guide
        return {
            "status": "success",
            "data": qa_pairs_result,
            "count": len(qa_pairs_result)
        }
        
    except ValueError as e:
        logger.error(f"Validation error retrieving QA pairs: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": str(e), "requestId": str(uuid.uuid4())}
        )
    except Exception as e:
        logger.error(f"Error retrieving QA pairs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": f"Failed to retrieve QA pairs: {str(e)}", "requestId": str(uuid.uuid4())}
        )

@router.post("/unidentified-fields/direct-suggest/", response_model=UnidentifiedFieldSuggestion)
async def direct_llm_suggestion(
    request: DirectLLMRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a direct LLM-based answer for a question.
    
    This endpoint completely relies on LLM to generate a response and doesn't
    attempt to find existing answers. Used for new questions where the user
    has context that can be used in generating a unique answer.
    """
    try:
        # Validate user exists
        user_service = UserService(db)
        user = user_service.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail={"status": "error", "message": "User not found", "requestId": str(uuid.uuid4())}
            )
        
        # Convert user to dict for LLM context
        user_dict = {
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "skills": [skill.skill_name for skill in user.skills] if user.skills else [],
            "experiences": [
                {
                    "role": exp.role,
                    "company": exp.company_name,
                    "current": exp.is_current,
                    "duration": f"{exp.start_date.year if hasattr(exp, 'start_date') and exp.start_date else 'Unknown'} - {exp.end_date.year if hasattr(exp, 'end_date') and exp.end_date else 'Present'}"
                } 
                for exp in user.work_experiences
            ] if user.work_experiences else [],
            "education": [
                {
                    "degree": edu.degree,
                    "field": edu.field_of_study,
                    "institution": edu.institution_name,
                    "year": edu.end_date.year if hasattr(edu, 'end_date') and edu.end_date else None
                }
                for edu in user.educations
            ] if user.educations else []
        }
        
        # Add headline if it exists
        if hasattr(user, 'headline') and user.headline:
            user_dict["headline"] = user.headline
        elif hasattr(user, 'summary') and user.summary:
            user_dict["headline"] = user.summary
        
        # Initialize LLM service and generate response
        llm_service = LLMService()
        llm_response = await llm_service.generate_contextual_response(
            user_id=request.user_id,
            question=request.question,
            context=request.context,
            user_profile=user_dict
        )
        
        # Convert to response model
        suggestion = UnidentifiedFieldSuggestion(
            suggestion=llm_response.get("suggestion"),
            confidence=llm_response.get("confidence", 0.8),
            source=llm_response.get("source", "llm_generation"),
            alternative_suggestions=llm_response.get("alternative_suggestions")
        )
        
        return suggestion
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in direct LLM suggestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"status": "error", "message": str(e), "requestId": str(uuid.uuid4())}
        )
    except Exception as e:
        # Log the error
        logger.error(f"Error generating direct LLM suggestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"status": "error", "message": "Failed to generate suggestion", "details": str(e)}
        ) 