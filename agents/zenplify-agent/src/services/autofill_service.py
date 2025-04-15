"""
Autofill service for managing form filling data.

This module provides functions for retrieving and formatting user data
for autofilling application forms with Zenplify.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from src.database.models import User, WorkExperience, Education, UserSkill
from src.schemas.autofill import AutofillResponse, AutofillContext
from src.services.user_service import UserService

# Configure logging
logger = logging.getLogger(__name__)

class AutofillService:
    """Service for autofill data management."""
    
    def __init__(self, db: Session):
        """
        Initialize the autofill service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.user_service = UserService(db)
    
    def get_autofill_data(
        self, 
        user_id: UUID, 
        context: Optional[Dict[str, Any]] = None
    ) -> AutofillResponse:
        """
        Get formatted data for autofilling a form.
        
        Args:
            user_id: User ID
            context: Optional context about the job/company
            
        Returns:
            AutofillResponse: Formatted data for Zenplify
            
        Raises:
            ValueError: If user not found
        """
        # Get user profile
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Create context object if provided
        autofill_context = None
        if context:
            autofill_context = AutofillContext(**context)
        
        # Convert user profile to Zenplify format
        return AutofillResponse.from_user_profile(user, autofill_context)
    
    def tailor_for_job(
        self,
        user_id: UUID,
        company_name: str,
        job_title: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tailor user data for a specific job application.
        
        This function could be used to prioritize certain experiences or skills
        based on the job requirements.
        
        Args:
            user_id: User ID
            company_name: Target company name
            job_title: Job title being applied for
            job_description: Optional job description
            
        Returns:
            Dict: Tailored user data
            
        Raises:
            ValueError: If user not found
        """
        # Get user profile
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # In a real implementation, this could use NLP to match experiences and skills
        # to the job description and prioritize the most relevant ones
        
        # For now, just return the basic profile data with context
        return {
            "user_profile": {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                # ... other basic profile fields ...
            },
            "context": {
                "company_name": company_name,
                "job_title": job_title,
                "job_description": job_description,
            },
            "tailored": False,  # Indicate this is not actually tailored yet
        } 