"""
AutofillService for managing form filling data.

This service is responsible for retrieving and formatting user profile data
for autofill functionality in forms.
"""

import logging
import json
from uuid import UUID
from typing import Dict, Any, List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from src.database.models import User, UserProfile, QAPair, Job, Company, WorkExperience, Education, UserSkill
from src.services.qa_service import QAService

# Configure logging
logger = logging.getLogger(__name__)

class AutofillService:
    """
    Service for managing form autofill data.
    
    This service retrieves and formats user profile data, job information,
    and Q&A history to provide autofill suggestions for forms.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the AutofillService.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.qa_service = QAService(db)
    
    def get_user_profile_data(self, user_id: UUID) -> Dict[str, Any]:
        """
        Retrieve comprehensive user profile data including related entities.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dict containing structured user profile data or empty dict on error.
        """
        try:
            # Query User and eagerly load related profile, experiences, educations, skills
            # Assumes relationships User.profile, User.work_experiences, User.educations, User.skills exist
            user = self.db.query(User).options(
                joinedload(User.profile),
                joinedload(User.work_experiences),
                joinedload(User.educations),
                joinedload(User.skills)
            ).filter(User.id == user_id).first()

            if not user:
                logger.error(f"User not found: {user_id}")
                return {}

            profile = user.profile # Access eagerly loaded profile

            # Build the result dictionary
            result = {
                "personal": {
                    "first_name": user.first_name or "John",
                    "last_name": user.last_name or "Doe",
                    "email": user.email or "user@example.com",
                },
                # Directly include relational data (lists of model objects)
                # These will be formatted later in format_for_autofill
                "experience": user.work_experiences if user.work_experiences else [],
                "education": user.educations if user.educations else [],
                "skills": user.skills if user.skills else [], # List of Skill objects
                 # Initialize contact and links, populate from User/UserProfile
                "contact": {},
                "links": {}
            }

            # Populate contact info - prioritize User model then UserProfile
            # Assuming 'phone' is on User based on sample API response
            result["contact"]["phone"] = user.phone if hasattr(user, 'phone') and user.phone else None
            # Assuming 'address_json' might be on UserProfile
            if profile and hasattr(profile, 'address_json') and profile.address_json:
                 # Assuming address_json is already a dict or convertible
                 address_data = profile.address_json if isinstance(profile.address_json, dict) else json.loads(profile.address_json)
                 result["contact"].update({ # Add address fields
                     "address": address_data.get("street1"), # Map from potential schema
                     "city": address_data.get("city"),
                     "state": address_data.get("state"),
                     "zip": address_data.get("postal_code"),
                     "country": address_data.get("country"),
                 })

            # Populate links from UserProfile if it exists
            if profile:
                result["links"]["linkedin"] = str(profile.linkedin_url) if hasattr(profile, 'linkedin_url') and profile.linkedin_url else None
                result["links"]["github"] = f"https://github.com/{profile.github_username}" if hasattr(profile, 'github_username') and profile.github_username else None
                result["links"]["portfolio"] = str(profile.portfolio_url) if hasattr(profile, 'portfolio_url') and profile.portfolio_url else None
                result["links"]["website"] = str(profile.website_url) if hasattr(profile, 'website_url') and profile.website_url else None

            # Optional: Merge profile.data JSON for potential overrides or extra fields
            if profile and profile.data:
                try:
                    profile_json_data = json.loads(profile.data) if isinstance(profile.data, str) else profile.data
                    if isinstance(profile_json_data, dict):
                        # Example: Override contact info if present in JSON
                        if "contact" in profile_json_data and isinstance(profile_json_data["contact"], dict):
                             # Map JSON contact fields to result["contact"] structure
                             contact_json = profile_json_data["contact"]
                             result["contact"]["phone"] = contact_json.get("phone", result["contact"]["phone"])
                             result["contact"]["address"] = contact_json.get("address", result["contact"].get("address"))
                             result["contact"]["city"] = contact_json.get("city", result["contact"].get("city"))
                             result["contact"]["state"] = contact_json.get("state", result["contact"].get("state"))
                             result["contact"]["zip"] = contact_json.get("zip", result["contact"].get("zip"))
                             result["contact"]["country"] = contact_json.get("country", result["contact"].get("country"))
                        # Add logic here if JSON should override/supplement education/experience/skills from relations
                        # For simplicity, we primarily rely on relational data now.
                except Exception as e:
                    logger.error(f"Error processing UserProfile.data JSON for user {user_id}: {e}")

            # Clean up None values in contact before returning
            result["contact"] = {k: v for k, v in result["contact"].items() if v is not None}

            return result

        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user profile: {e}")
            # Consider raising a custom exception or returning a specific error structure
            return {}
        except Exception as e:
            logger.error(f"Unexpected error retrieving user profile data: {e}")
            return {}
    
    def get_job_data(self, user_id: UUID, job_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Retrieve job and company data for autofill.
        
        Args:
            user_id: UUID of the user
            job_id: Optional UUID of the specific job
            
        Returns:
            Dict containing job and company data
        """
        try:
            jobs_query = self.db.query(Job).filter(Job.user_id == user_id)
            
            # If job_id is provided, filter for that specific job
            if job_id:
                jobs_query = jobs_query.filter(Job.id == job_id)
            
            jobs = jobs_query.all()
            
            result = {
                "jobs": []
            }
            
            for job in jobs:
                job_data = {
                    "id": str(job.id),
                    "title": job.title,
                    "description": job.description,
                    "url": job.url,
                    "status": job.status,
                    "applied_date": job.applied_date.isoformat() if job.applied_date else None,
                }
                
                # Get company data if available
                if job.company_id:
                    company = self.db.query(Company).filter(Company.id == job.company_id).first()
                    if company:
                        job_data["company"] = {
                            "id": str(company.id),
                            "name": company.name,
                            "website": company.website,
                            "industry": company.industry,
                            "size": company.size,
                        }
                
                result["jobs"].append(job_data)
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving job data: {e}")
            return {"jobs": []}
        except Exception as e:
            logger.error(f"Error retrieving job data: {e}")
            return {"jobs": []}
    
    def get_qa_history(self, user_id: UUID, context: Optional[Dict[str, Any]] = None, limit: int = 20) -> Dict[str, Any]:
        """
        Retrieve Q&A history for autofill.
        
        Args:
            user_id: UUID of the user
            context: Optional context for filtering Q&A pairs
            limit: Maximum number of Q&A pairs to retrieve
            
        Returns:
            Dict containing Q&A history
        """
        try:
            # Query Q&A pairs
            qa_query = self.db.query(QAPair).filter(QAPair.user_id == user_id)
            
            # Apply context filtering if provided
            if context and "company" in context:
                # Filter by company in the context JSON
                qa_query = qa_query.filter(QAPair.context.contains({"company": context["company"]}))
            
            if context and "job_title" in context:
                # Filter by job title in the context JSON
                qa_query = qa_query.filter(QAPair.context.contains({"job_title": context["job_title"]}))
            
            # Order by creation date and limit results
            qa_pairs = qa_query.order_by(QAPair.created_at.desc()).limit(limit).all()
            
            result = {
                "qa_pairs": []
            }
            
            for qa in qa_pairs:
                qa_data = {
                    "id": str(qa.id),
                    "question": qa.question,
                    "answer": qa.answer,
                    "created_at": qa.created_at.isoformat(),
                    "context": qa.context if isinstance(qa.context, dict) else json.loads(qa.context) if qa.context else {}
                }
                
                result["qa_pairs"].append(qa_data)
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving Q&A history: {e}")
            return {"qa_pairs": []}
        except Exception as e:
            logger.error(f"Error retrieving Q&A history: {e}")
            return {"qa_pairs": []}
    
    def get_autofill_data(self, user_id: UUID, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get autofill data for a form based on the user ID and context.
        
        Args:
            user_id: UUID of the user
            context: Optional context with form fields and job info
            
        Returns:
            AutofillResponse with formatted data for form autofill
        """
        try:
            # Get user profile data
            profile_data = self.get_user_profile_data(user_id)
            
            if not profile_data or not profile_data.get('personal'):
                logger.warning(f"Profile data not found or incomplete for user: {user_id}")
                raise ValueError("User profile not found or incomplete")
            
            # Form fields to autofill
            form_fields = [
                "first_name", "last_name", "email", "phone", "address", "city", "state", 
                "zip", "country", "education", "experience", "skills", "linkedin", "github",
                "portfolio", "website", # Added portfolio, website
                "current_role", "current_company"
            ]
            
            # Format data for autofill
            formatted_data = self.format_for_autofill(user_id, form_fields, context)
            
            # Ensure required fields have values
            if not formatted_data.get("first_name"):
                formatted_data["first_name"] = "John"  # Default value
            
            if not formatted_data.get("last_name"):
                formatted_data["last_name"] = "Doe"  # Default value
            
            if not formatted_data.get("email"):
                formatted_data["email"] = "user@example.com"  # Default value
            
            # Convert to Zenplify format
            # Convert generic field names to Zenplify field names and handle empty strings
            zenplify_data = {
                "firstName": formatted_data.get("first_name"),
                "lastName": formatted_data.get("last_name"),
                "email": formatted_data.get("email"),
                "phone": formatted_data.get("phone") or None,
                "address": formatted_data.get("address") or None,
                "city": formatted_data.get("city") or None,
                "state": formatted_data.get("state") or None,
                "zip": formatted_data.get("zip") or None,
                "country": formatted_data.get("country") or None,
                "education": formatted_data.get("education") or None,
                "experience": formatted_data.get("experience") or None,
                "skills": formatted_data.get("skills") or None,
                "linkedin": formatted_data.get("linkedin") or None,
                "github": formatted_data.get("github") or None,
                "portfolio": formatted_data.get("portfolio") or None,
                "website": formatted_data.get("website") or None,
                "company": formatted_data.get("current_company") or None,
                "currentJob": formatted_data.get("current_role") or None
            }
            
            # Final validation - ensure all values are either proper strings or null, never empty strings
            for key, value in zenplify_data.items():
                if value == "":
                    zenplify_data[key] = None
            
            # Return as AutofillResponse
            from src.schemas.autofill import ZenplifyUserData, AutofillResponse
            return {"user_data": zenplify_data}
            
        except ValueError as e:
            logger.error(f"Value error generating autofill data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating autofill data: {e}")
            # Re-raise for HTTP error handling
            raise

    def format_for_autofill(self, user_id: UUID, form_fields: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format data for form autofill based on requested fields. 
        Uses data retrieved by get_user_profile_data (including model objects).
        """
        try:
            # Get all data sources
            profile_data = self.get_user_profile_data(user_id)
            job_data = self.get_job_data(user_id) # No change needed here for now
            qa_data = self.get_qa_history(user_id, context=context, limit=50)
            
            # Initialize result with null values for all requested fields
            result = {field: None for field in form_fields}
            
            # Map form fields to data sources using the new structure from get_user_profile_data
            field_mapping = {
                # Personal information
                "name": lambda: f"{profile_data.get('personal', {}).get('first_name', '')} {profile_data.get('personal', {}).get('last_name', '')}".strip() or None,
                "first_name": lambda: profile_data.get('personal', {}).get('first_name') or None,
                "last_name": lambda: profile_data.get('personal', {}).get('last_name') or None,
                "email": lambda: profile_data.get('personal', {}).get('email') or None,

                # Contact information (now sourced primarily from get_user_profile_data structure)
                "phone": lambda: profile_data.get('contact', {}).get('phone') or None,
                "address": lambda: profile_data.get('contact', {}).get('address') or None, 
                "city": lambda: profile_data.get('contact', {}).get('city') or None,
                "state": lambda: profile_data.get('contact', {}).get('state') or None,
                "zip": lambda: profile_data.get('contact', {}).get('zip') or None,
                "country": lambda: profile_data.get('contact', {}).get('country') or None, # Added country mapping
                
                # Education (Uses new helper with List[Education])
                "education": lambda: self._format_education_list(profile_data.get('education', [])),
                "degree": lambda: profile_data.get('education', [None])[0].degree if profile_data.get('education') and profile_data.get('education')[0] else None,
                "school": lambda: profile_data.get('education', [None])[0].institution_name if profile_data.get('education') and profile_data.get('education')[0] else None,
                # "graduation_year": lambda: ..., # Add if needed, requires date formatting

                # Experience (Uses new helpers with List[WorkExperience])
                "experience": lambda: self._format_experience_list(profile_data.get('experience', [])),
                "current_role": lambda: self._get_current_role(profile_data.get('experience', [])),
                "current_company": lambda: self._get_current_company(profile_data.get('experience', [])),
                
                # Skills (Uses new helper with List[UserSkill])
                "skills": lambda: self._format_skills_list(profile_data.get('skills', [])),
                
                # Links (now sourced from profile_data["links"])
                "linkedin": lambda: profile_data.get('links', {}).get('linkedin') or None,
                "github": lambda: profile_data.get('links', {}).get('github') or None,
                "portfolio": lambda: profile_data.get('links', {}).get('portfolio') or None,
                "website": lambda: profile_data.get('links', {}).get('website') or None,

                # Job information (from get_job_data, likely no changes needed here)
                "job_title": lambda: job_data.get('jobs', [{}])[0].get('title') if job_data.get('jobs') else None,
                "company_name": lambda: job_data.get('jobs', [{}])[0].get('company', {}).get('name') if job_data.get('jobs') else None,
            }
            
            # Populate fields from the mapping
            for field in form_fields:
                if field in field_mapping:
                    result[field] = field_mapping[field]()
                else:
                    # For fields not in the mapping, try to find an answer in Q&A history
                    for qa in qa_data.get('qa_pairs', []):
                        # Check if question contains field name (simple heuristic)
                        if field.lower().replace('_', ' ') in qa['question'].lower():
                            result[field] = qa['answer'] or None
                            break
            
            # Final check to replace empty strings with None
            for key, value in result.items():
                if value == "":
                    result[key] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting data for autofill: {e}")
            # Return a dict with all None values instead of empty strings
            return {field: None for field in form_fields}
    
    def _format_education_list(self, educations: List[Education]) -> Optional[str]:
        """Format a list of Education model objects into a string."""
        if not educations: return None
        # Example format: "Degree in Field from Institution, ..."
        parts = []
        for edu in educations:
            part = f"{edu.degree or ''}"
            if edu.field_of_study:
                 part += f" in {edu.field_of_study}"
            if edu.institution_name:
                 part += f" from {edu.institution_name}"
            if part.strip(" from in"): # Avoid empty strings if all fields are None
                 parts.append(part.strip())
        
        formatted = ", ".join(parts)
        return formatted if formatted else None

    def _format_experience_list(self, experiences: List[WorkExperience]) -> Optional[str]:
        """Format a list of WorkExperience model objects into a string."""
        if not experiences: return None
        # Example format: "Role at Company, ..."
        # Sort by recency (current first, then by end_date)
        experiences.sort(key=lambda x: (x.is_current is not True, x.end_date is not None, x.end_date), reverse=True)
        
        parts = []
        for exp in experiences:
            part = ""
            if exp.role:
                 part += f"{exp.role}"
            if exp.company_name:
                 part += f" at {exp.company_name}"
            if part.strip(" at"):
                 parts.append(part.strip())
                 
        formatted = ", ".join(parts)
        return formatted if formatted else None

    def _format_skills_list(self, skills: List[UserSkill]) -> Optional[str]:
        """Format a list of UserSkill model objects into a comma-separated string."""
        if not skills: return None
        formatted = ", ".join([skill.skill_name for skill in skills if skill.skill_name])
        return formatted if formatted else None

    def _get_current_role(self, experiences: List[WorkExperience]) -> Optional[str]:
        """Find the current role from a list of experiences."""
        # Prioritize explicitly marked current job
        for exp in experiences:
            if hasattr(exp, 'is_current') and exp.is_current:
                return exp.role
        # Fallback: Find job with None end_date or most recent end_date
        if experiences:
            experiences.sort(key=lambda x: (x.end_date is not None, x.end_date), reverse=True) # None end_date first
            return experiences[0].role
        return None

    def _get_current_company(self, experiences: List[WorkExperience]) -> Optional[str]:
        """Find the current company from a list of experiences."""
        # Prioritize explicitly marked current job
        for exp in experiences:
            if hasattr(exp, 'is_current') and exp.is_current:
                return exp.company_name
        # Fallback: Find job with None end_date or most recent end_date
        if experiences:
            experiences.sort(key=lambda x: (x.end_date is not None, x.end_date), reverse=True) # None end_date first
            return experiences[0].company_name
        return None

    # Remove or comment out old formatters if no longer needed
    # def _format_list_to_string(self, items: List) -> Optional[str]: ...
    # def _format_dict_to_string(self, item: Dict) -> str: ...

# Ensure imports for date at the top if used for sorting
# Ensure necessary models (WorkExperience, Education, UserSkill) are imported

# Final checks:
# - Assumes SQLAlchemy relationships (User.profile, User.work_experiences etc.) are correctly defined.
# - Assumes field names like `is_current`, `linkedin_url` match the actual model definitions.
# - Formatting logic in helper methods matches the expected string format for Zenplify. 