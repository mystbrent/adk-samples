"""
LLM service for direct language model interactions.

This module provides functions for generating responses 
directly from a language model without relying on semantic search.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import json

from google.adk.models.google_llm import Gemini
from google.adk.models import LlmRequest
from google.cloud import aiplatform
from google.oauth2 import service_account

# Configure logging
logger = logging.getLogger(__name__)

# LLM model configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

class LLMService:
    """Service for direct LLM interactions."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self._initialize_vertex_ai()
        self.model = Gemini(model_name=GEMINI_MODEL)
        
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI client with proper credentials."""
        try:
            # Check if credential path exists, if so use it
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                aiplatform.init(
                    project=self.project_id,
                    location=self.location,
                    credentials=credentials
                )
            else:
                # Use default credentials
                aiplatform.init(
                    project=self.project_id,
                    location=self.location
                )
            logger.info("Vertex AI client initialized successfully for LLM service")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {e}")
            # We'll let this propagate since we can't fall back for LLM
            raise
    
    async def generate_contextual_response(
        self,
        user_id: UUID,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a contextual response using an LLM for a question.
        
        Args:
            user_id: User ID
            question: Question text
            context: Additional context (company, job description, etc.)
            user_profile: User profile data for personalization
            
        Returns:
            Dict with generated response and metadata
        """
        try:
            # Prepare complete prompt including system instructions
            system_instruction = """
            You are an AI assistant helping with job applications. Your task is to generate
            a personalized and contextually appropriate response to a job application question.
            
            The response should:
            1. Be professional and well-formatted
            2. Directly address the question being asked
            3. Incorporate the user's background and experience when relevant
            4. Consider the specific job and company context provided
            5. Be concise and to the point, between 2-4 sentences unless more detail is clearly needed
            """
            
            # Build the user prompt with all context
            user_prompt = f"Question: {question}\n\n"
            
            # Add context information if available
            if context:
                user_prompt += "Context:\n"
                if isinstance(context, str):
                    user_prompt += context
                else:
                    # Format each context item
                    for key, value in context.items():
                        if value and isinstance(value, str):
                            user_prompt += f"- {key}: {value}\n"
                        elif value:
                            user_prompt += f"- {key}: {json.dumps(value)}\n"
            
            # Add user profile information if available
            if user_profile:
                user_prompt += "\nUser Profile:\n"
                for key, value in user_profile.items():
                    if value and isinstance(value, str):
                        user_prompt += f"- {key}: {value}\n"
                    elif value:
                        user_prompt += f"- {key}: {json.dumps(value)}\n"
            
            user_prompt += "\nPlease generate a professional response to this question."
            
            # Create LLM request
            llm_request = LlmRequest(
                user_prompt=user_prompt,
                system_prompt=system_instruction
            )
            
            # Generate the response
            logger.info(f"Generating response for question: {question}")
            async for response in self.model.generate_content_async(llm_request):
                # We only need the first response
                main_suggestion = response.text.strip()
                break
            
            # Generate alternative suggestions (simplified implementation)
            # In a real implementation, this could be more sophisticated
            alternatives = await self._generate_alternatives(question, main_suggestion)
            
            return {
                "suggestion": main_suggestion,
                "confidence": 0.8,  # Fixed confidence for LLM generations
                "source": "llm_generation",
                "alternative_suggestions": alternatives
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            # Return a generic response in case of error
            return {
                "suggestion": "I would be a good fit for this position based on my experience and skills.",
                "confidence": 0.5,
                "source": "fallback",
                "alternative_suggestions": [
                    "My background has prepared me well for this role.",
                    "I have the necessary qualifications for this position."
                ]
            }
    
    async def _generate_alternatives(self, question: str, main_answer: str) -> List[str]:
        """
        Generate alternative suggestions for the same question.
        
        Args:
            question: The original question
            main_answer: The main answer already generated
            
        Returns:
            List of alternative suggestions
        """
        try:
            system_instruction = """
            Generate two alternative formulations of the provided answer.
            The alternatives should:
            1. Convey essentially the same message and information
            2. Use different wording and structure
            3. Be concise and professional
            4. Not repeat the original answer verbatim
            """
            
            user_prompt = f"""
            Question: {question}
            
            Original Answer: {main_answer}
            
            Please provide two alternative formulations of this answer.
            """
            
            # Create LLM request
            llm_request = LlmRequest(
                user_prompt=user_prompt,
                system_prompt=system_instruction
            )
            
            # Generate alternatives
            alternatives_text = ""
            async for response in self.model.generate_content_async(llm_request):
                # We only need the first response
                alternatives_text = response.text.strip()
                break
            
            # Split the response into separate alternatives
            # This is a simple implementation - could be more sophisticated
            alternatives = [
                alt.strip() for alt in alternatives_text.split("\n\n")
                if alt.strip() and alt.strip() != main_answer
            ]
            
            # Limit to 2 alternatives
            return alternatives[:2]
            
        except Exception as e:
            logger.error(f"Error generating alternative suggestions: {str(e)}")
            return [
                "My background has prepared me well for this role.",
                "I have the necessary qualifications for this position."
            ] 