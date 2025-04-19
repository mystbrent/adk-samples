"""
User service for managing user profiles.

This module provides functions for creating, retrieving, updating,
and deleting user profiles and related data.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import datetime

from src.database.models import User, WorkExperience, Education, UserSkill
from src.schemas.user import (
    UserProfileCreate,
    UserProfileUpdate,
    WorkExperienceBase,
    EducationBase,
    UserSkillBase,
)
from ..api.schemas import User as ApiUser, UserCreate
# Remove the MongoDB import since it's not available
# from ..database import users_collection

# Configure logging
logger = logging.getLogger(__name__)

class UserService:
    """Service for user profile management."""
    
    def __init__(self, db: Session):
        """
        Initialize the user service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User: User object if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User: User object if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user_data: UserProfileCreate) -> User:
        """
        Create a new user profile.
        
        Args:
            user_data: User profile data
            
        Returns:
            User: Created user object
            
        Raises:
            ValueError: If a user with the same email already exists
        """
        # Check if user with email already exists
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Log the received address_json for debugging
        logger.info(f"Received address_json in create_user: {user_data.address_json}")
        
        # Create address JSON if provided
        address_json = user_data.address_json if user_data.address_json else None
        
        # Split full_name into first_name and last_name
        first_name = user_data.first_name
        last_name = user_data.last_name
        
        # Create user object
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=user_data.email,
            phone=user_data.phone,
            address_json=address_json,
            github_username=user_data.github_username,
            linkedin_url=str(user_data.linkedin_url) if user_data.linkedin_url else None,
            portfolio_url=str(user_data.portfolio_url) if user_data.portfolio_url else None,
            website_url=str(user_data.website_url) if user_data.website_url else None,
            gender=user_data.gender,
            date_of_birth=user_data.date_of_birth,
        )
        
        try:
            # Add and commit user to get ID
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Add work experiences if provided
            if user_data.work_experiences:
                self._add_work_experiences(user.id, user_data.work_experiences)
            
            # Add education if provided
            if user_data.educations:
                self._add_educations(user.id, user_data.educations)
            
            # Add skills if provided
            if user_data.skills:
                self._add_skills(user.id, user_data.skills)
            
            # Refresh user to include relationships
            self.db.refresh(user)
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise ValueError("Failed to create user profile")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating user: {e}")
            raise
    
    def update_user(self, user_id: UUID, user_data: UserProfileUpdate) -> Optional[User]:
        """
        Update a user profile.
        
        Args:
            user_id: User ID
            user_data: Updated user profile data
            
        Returns:
            User: Updated user object, or None if user not found
            
        Raises:
            ValueError: If update fails due to constraint violation
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update basic fields if provided
        if user_data.full_name is not None:
            name_parts = user_data.full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ""
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.phone is not None:
            user.phone = user_data.phone
        if user_data.address_json is not None:
            # Directly assign the dictionary
            user.address_json = user_data.address_json
        if user_data.github_username is not None:
            user.github_username = user_data.github_username
        if user_data.linkedin_url is not None:
            user.linkedin_url = str(user_data.linkedin_url) if user_data.linkedin_url else None
        if user_data.portfolio_url is not None:
            user.portfolio_url = str(user_data.portfolio_url) if user_data.portfolio_url else None
        if user_data.website_url is not None:
            user.website_url = str(user_data.website_url) if user_data.website_url else None
        
        try:
            # Update work experiences if provided
            if user_data.work_experiences is not None:
                self._update_work_experiences(user.id, user_data.work_experiences)
            
            # Update educations if provided
            if user_data.educations is not None:
                self._update_educations(user.id, user_data.educations)
            
            # Update skills if provided
            if user_data.skills is not None:
                self._update_skills(user.id, user_data.skills)
            
            # Commit changes
            self.db.commit()
            self.db.refresh(user)
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update user: {e}")
            raise ValueError("Failed to update user profile")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating user: {e}")
            raise
    
    def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if user was deleted, False if user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user: {e}")
            raise
    
    def _add_work_experiences(self, user_id: UUID, experiences: List[WorkExperienceBase]):
        """Add work experiences for a user."""
        for exp_data in experiences:
            experience = WorkExperience(
                user_id=user_id,
                company_name=exp_data.company_name,
                role=exp_data.role,
                start_date=exp_data.start_date,
                end_date=exp_data.end_date,
                description=exp_data.description,
                location=exp_data.location,
                is_current=exp_data.is_current,
            )
            self.db.add(experience)
        self.db.commit()
    
    def _update_work_experiences(self, user_id: UUID, experiences: List[WorkExperienceBase]):
        """Update work experiences for a user."""
        # Delete existing experiences
        self.db.query(WorkExperience).filter(WorkExperience.user_id == user_id).delete()
        # Add new ones
        self._add_work_experiences(user_id, experiences)
    
    def _add_educations(self, user_id: UUID, educations: List[EducationBase]):
        """Add educations for a user."""
        for edu_data in educations:
            education = Education(
                user_id=user_id,
                institution_name=edu_data.institution_name,
                degree=edu_data.degree,
                field_of_study=edu_data.field_of_study,
                start_date=edu_data.start_date,
                end_date=edu_data.end_date,
                grade=edu_data.grade,
                description=edu_data.description,
            )
            self.db.add(education)
        self.db.commit()
    
    def _update_educations(self, user_id: UUID, educations: List[EducationBase]):
        """Update educations for a user."""
        # Delete existing educations
        self.db.query(Education).filter(Education.user_id == user_id).delete()
        # Add new ones
        self._add_educations(user_id, educations)
    
    def _add_skills(self, user_id: UUID, skills: List[UserSkillBase]):
        """Add skills for a user."""
        for skill_data in skills:
            skill = UserSkill(
                user_id=user_id,
                skill_name=skill_data.skill_name,
                category=skill_data.category,
            )
            self.db.add(skill)
        self.db.commit()
    
    def _update_skills(self, user_id: UUID, skills: List[UserSkillBase]):
        """Update skills for a user."""
        # Delete existing skills
        self.db.query(UserSkill).filter(UserSkill.user_id == user_id).delete()
        # Add new ones
        self._add_skills(user_id, skills)

    # Comment out MongoDB functions since they're not compatible with current database setup
    """
    @staticmethod
    async def create_user(user_data: UserCreate) -> ApiUser:
        # MongoDB implementation removed
        pass
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[ApiUser]:
        # MongoDB implementation removed
        pass
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[ApiUser]:
        # MongoDB implementation removed
        pass
    
    @staticmethod
    async def get_all_users() -> List[ApiUser]:
        # MongoDB implementation removed
        pass
    """ 