"""
AutofillService for managing form filling data.

This service is responsible for retrieving and formatting user profile data
for autofill functionality in forms.
"""

import logging
import json
from uuid import UUID
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.database.models import User, UserProfile, QAPair, Job, Company
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
        Retrieve user profile data for autofill.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dict containing user profile data
        """
        try:
            # Query the user and their profile
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return {}
            
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            # Start with basic user data
            result = {
                "personal": {
                    "first_name": user.first_name or "John",  # Default if empty
                    "last_name": user.last_name or "Doe",     # Default if empty
                    "email": user.email or "user@example.com",  # Default if empty
                }
            }
            
            # Add profile data if available
            if profile:
                # Parse the JSON data from the profile
                profile_data = profile.data if isinstance(profile.data, dict) else json.loads(profile.data)
                
                # Add contact information
                if "contact" in profile_data:
                    result["contact"] = profile_data["contact"]
                
                # Add education information
                if "education" in profile_data:
                    result["education"] = profile_data["education"]
                
                # Add work experience
                if "experience" in profile_data:
                    result["experience"] = profile_data["experience"]
                
                # Add skills
                if "skills" in profile_data:
                    result["skills"] = profile_data["skills"]
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving user profile: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error retrieving user profile data: {e}")
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
            form_fields = []
            if context and isinstance(context, dict) and 'form_fields' in context and context['form_fields']:
                form_fields = context['form_fields']
            else:
                # Default set of common fields if none provided
                form_fields = [
                    "first_name", "last_name", "email", "phone", "address", "city", "state", 
                    "zip", "country", "education", "experience", "skills", "linkedin", "github",
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
        
        Args:
            user_id: UUID of the user
            form_fields: List of field names to populate
            context: Optional context for the form (company, job, etc.)
            
        Returns:
            Dict mapping field names to values
        """
        try:
            # Get all data sources
            profile_data = self.get_user_profile_data(user_id)
            job_data = self.get_job_data(user_id) if "job" in form_fields or "company" in form_fields else {}
            qa_data = self.get_qa_history(user_id, context=context, limit=50)
            
            # Initialize result with null values for all requested fields
            result = {field: None for field in form_fields}
            
            # Map form fields to data sources
            field_mapping = {
                # Personal information
                "name": lambda: f"{profile_data.get('personal', {}).get('first_name', '')} {profile_data.get('personal', {}).get('last_name', '')}".strip() or None,
                "first_name": lambda: profile_data.get('personal', {}).get('first_name') or None,
                "last_name": lambda: profile_data.get('personal', {}).get('last_name') or None,
                "email": lambda: profile_data.get('personal', {}).get('email') or None,
                "phone": lambda: profile_data.get('contact', {}).get('phone') or None,
                "address": lambda: profile_data.get('contact', {}).get('address') or None,
                "city": lambda: profile_data.get('contact', {}).get('city') or None,
                "state": lambda: profile_data.get('contact', {}).get('state') or None,
                "zip": lambda: profile_data.get('contact', {}).get('zip') or None,
                
                # Education
                "education": lambda: self._format_list_to_string(profile_data.get('education', [])),
                "degree": lambda: profile_data.get('education', [{}])[0].get('degree') if profile_data.get('education') else None,
                "school": lambda: profile_data.get('education', [{}])[0].get('school') if profile_data.get('education') else None,
                "graduation_year": lambda: profile_data.get('education', [{}])[0].get('year') if profile_data.get('education') else None,
                
                # Experience
                "experience": lambda: self._format_list_to_string(profile_data.get('experience', [])),
                "current_role": lambda: profile_data.get('experience', [{}])[0].get('title') if profile_data.get('experience') else None,
                "current_company": lambda: profile_data.get('experience', [{}])[0].get('company') if profile_data.get('experience') else None,
                
                # Skills
                "skills": lambda: ", ".join(profile_data.get('skills', [])) or None,
                
                # Job information
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
    
    def _format_list_to_string(self, items: List) -> Optional[str]:
        """
        Format a list of items to a string, handling empty lists.
        
        Args:
            items: List of items to format
            
        Returns:
            Formatted string or None if empty
        """
        if not items:
            return None
            
        if isinstance(items, list) and len(items) > 0:
            if all(isinstance(item, dict) for item in items):
                # Handle list of dictionaries
                formatted = ", ".join([self._format_dict_to_string(item) for item in items])
                return formatted if formatted else None
            else:
                # Handle list of strings or other simple types
                formatted = ", ".join([str(item) for item in items if item])
                return formatted if formatted else None
        return None
        
    def _format_dict_to_string(self, item: Dict) -> str:
        """
        Format a dictionary to a string representation.
        
        Args:
            item: Dictionary to format
            
        Returns:
            Formatted string
        """
        if not item:
            return ""
            
        # Try to extract the most relevant fields
        if "title" in item and "company" in item:
            return f"{item['title']} at {item['company']}"
        elif "role" in item and "company_name" in item:
            return f"{item['role']} at {item['company_name']}"
        elif "degree" in item and "institution_name" in item:
            field = item.get("field_of_study", "")
            return f"{item['degree']} in {field} from {item['institution_name']}"
        else:
            # Generic approach - just concatenate key values
            return ", ".join([f"{k}: {v}" for k, v in item.items() if v]) 