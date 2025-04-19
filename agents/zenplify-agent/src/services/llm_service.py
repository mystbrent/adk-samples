"""
LLM service for direct language model interactions using the standard Vertex AI client.

This module provides functions for generating responses 
directly from a language model without relying on semantic search.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import json
from pathlib import Path

# --- Use Standard Vertex AI Client ---
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content, GenerationConfig
from google.cloud import aiplatform
from google.oauth2 import service_account
# --- Removed ADK Imports ---
# from google.adk.models.google_llm import Gemini
# from google.adk.models import LlmRequest

# Configure logging
logger = logging.getLogger(__name__)

# LLM model configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

class LLMService:
    """Service for direct LLM interactions using vertexai.GenerativeModel."""
    
    def __init__(self):
        """
        Initialize the LLM service using the standard Vertex AI client.
        Ensures Vertex AI is initialized.
        """
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.credentials = self._load_credentials()
        self._initialize_vertex_ai() # Ensure vertexai is initialized
        
        try:
            # Use the standard Vertex AI GenerativeModel
            self.model = GenerativeModel(model_name=GEMINI_MODEL)
            logger.info(f"Initialized Vertex AI GenerativeModel: {GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI GenerativeModel: {e}")
            # Re-raise to indicate service failure
            raise
            
    def _load_credentials(self):
        """Load GCP credentials from file if available."""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and Path(credentials_path).exists():
            try:
                logger.info(f"Loading credentials from {credentials_path}")
                return service_account.Credentials.from_service_account_file(
                    credentials_path
                )
            except Exception as e:
                logger.error(f"Failed to load credentials from {credentials_path}: {e}")
        logger.info("Using default application credentials.")
        return None # Use default credentials if path not found or loading fails
        
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI SDK with proper credentials."""
        try:
            init_params = {
                "project": self.project_id,
                "location": self.location
            }
            
            # Add credentials if explicitly loaded
            if self.credentials:
                init_params["credentials"] = self.credentials
                
            vertexai.init(**init_params)
            logger.info(f"Vertex AI SDK initialized with: project={self.project_id}, location={self.location}, credentials_loaded={self.credentials is not None}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI SDK: {e}")
            # We'll let this propagate since we can't fall back for LLM
            raise
    
    async def generate_contextual_response(
        self,
        user_id: UUID,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        generate_alternatives: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a contextual response using the standard Vertex AI client.
        
        Args:
            user_id: User ID
            question: Question text
            context: Additional context (company, job description, etc.)
            user_profile: User profile data for personalization
            generate_alternatives: Whether to generate alternative suggestions
            
        Returns:
            Dict with generated response and metadata
        """
        if not hasattr(self, 'model') or self.model is None:
             logger.error("LLMService model not initialized.")
             raise RuntimeError("LLMService model not initialized.")
             
        try:
            # Combine system instructions and user prompt into one string
            system_instruction_text = """
            You are an AI assistant helping with job applications. Your task is to generate
            a personalized and contextually appropriate response to a job application question.
            
            The response should:
            1. Be professional and well-formatted
            2. Directly address the question being asked
            3. Incorporate the user's background and experience when relevant
            4. Consider the specific job and company context provided
            5. Be concise and to the point, between 2-4 sentences unless more detail is clearly needed
            
            ---
            
            """
            
            user_prompt_text = system_instruction_text # Start with system instructions
            user_prompt_text += f"Question: {question}\n\n"
            if context:
                user_prompt_text += "Context:\n"
                if isinstance(context, str):
                    user_prompt_text += context + "\n"
                else:
                    for key, value in context.items():
                        if value and isinstance(value, str):
                            user_prompt_text += f"- {key}: {value}\n"
                        elif value:
                            user_prompt_text += f"- {key}: {json.dumps(value)}\n"
            if user_profile:
                user_prompt_text += "\nUser Profile:\n"
                for key, value in user_profile.items():
                    if value and isinstance(value, str):
                        user_prompt_text += f"- {key}: {value}\n"
                    elif value:
                        user_prompt_text += f"- {key}: {json.dumps(value)}\n"
            user_prompt_text += "\nPlease generate a professional response to this question."
            
            # Create Content object for the combined prompt
            combined_content = [Part.from_text(user_prompt_text)] # Single part with combined text

            # Generation configuration
            generation_config = GenerationConfig(
                temperature=0.7,  # Adjust as needed
                top_p=0.9,
                max_output_tokens=512
            )
            
            # Generate the response using the standard client
            logger.info(f"Generating response for question using Vertex AI model: {self.model._model_name}")
            response = await self.model.generate_content_async(
                contents=combined_content, # Pass single Content object
                generation_config=generation_config
            )
            
            # Process the response from the standard client
            if not response.candidates or not response.candidates[0].content.parts:
                logger.error("LLM response was empty or invalid.")
                raise ValueError("LLM response was empty or invalid.")
            
            main_suggestion = response.candidates[0].content.parts[0].text.strip()
                            
            # Generate alternative suggestions only if requested
            alternatives = []
            if generate_alternatives:
                alternatives = await self._generate_alternatives(question, main_suggestion)
            
            return {
                "suggestion": main_suggestion,
                "confidence": 0.8,  # Fixed confidence for LLM generations
                "source": "llm_generation",
                "alternative_suggestions": alternatives
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response with Vertex AI client: {str(e)}", exc_info=True)
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
        Generate alternative suggestions using the standard Vertex AI client.
        """
        if not hasattr(self, 'model') or self.model is None:
             logger.error("LLMService model not initialized for generating alternatives.")
             return [
                "My background has prepared me well for this role.",
                "I have the necessary qualifications for this position."
            ]
             
        try:
            # Combine system instructions and user prompt into one string
            system_instruction_text = """
            Generate two alternative formulations of the provided answer.
            The alternatives should:
            1. Convey essentially the same message and information
            2. Use different wording and structure
            3. Be concise and professional
            4. Not repeat the original answer verbatim
            
            ---
            
            """
            
            user_prompt_text = system_instruction_text # Start with system instructions
            user_prompt_text += f"""
            Question: {question}
            
            Original Answer: {main_answer}
            
            Please provide two alternative formulations of this answer.
            """
            
            # Create Content object for the combined prompt
            combined_content = [Part.from_text(user_prompt_text)] # Single part with combined text
            
            # Generation configuration
            generation_config = GenerationConfig(
                temperature=0.7, 
                max_output_tokens=256
            )

            # Generate alternatives
            logger.info(f"Generating alternatives using Vertex AI model: {self.model._model_name}")
            response = await self.model.generate_content_async(
                contents=combined_content, # Pass single Content object
                generation_config=generation_config
            )
            
            # Process the response
            if not response.candidates or not response.candidates[0].content.parts:
                 logger.warning("Alternative generation response was empty.")
                 return []
                 
            alternatives_text = response.candidates[0].content.parts[0].text.strip()
            
            # Split the response into separate alternatives
            alternatives = [
                alt.strip() for alt in alternatives_text.split("\n\n")
                if alt.strip() and alt.strip() != main_answer
            ]
            
            # Limit to 2 alternatives
            return alternatives[:2]
            
        except Exception as e:
            logger.error(f"Error generating alternative suggestions with Vertex AI client: {str(e)}", exc_info=True)
            return [
                "My background has prepared me well for this role.",
                "I have the necessary qualifications for this position."
            ] 