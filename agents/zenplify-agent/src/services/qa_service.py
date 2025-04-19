"""
Q&A service for managing question-answer pairs.

This module provides functions for saving and retrieving Q&A pairs
with semantic search capabilities.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from datetime import datetime
import asyncio

from src.database.models import User, QAHistory
from src.services.user_service import UserService
from src.services.embedding_service import EmbeddingService
from src.services.llm_service import LLMService
from ..api.schemas import QAPair, QAPairCreate
# Remove the MongoDB imports since they're not available
# from ..database import qa_pairs_collection, users_collection

# Configure logging
logger = logging.getLogger(__name__)

# Check if pgvector is available
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    VECTOR_AVAILABLE = False

class QAService:
    """Service for Q&A management with semantic search."""
    
    def __init__(self, db: Session):
        """
        Initialize the Q&A service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.user_service = UserService(db)
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
    
    async def suggest_answer(
        self, 
        user_id: UUID, 
        question: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Suggest an answer for a question based on Q&A history or user profile.
        
        Args:
            user_id: User ID
            question: Question text
            context: Additional context (company, job, etc.)
            
        Returns:
            Dict: Suggested answer with confidence score
            
        Raises:
            ValueError: If user not found
        """
        # Check if user exists
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # First try to find a similar question in Q&A history
        similar_qa = self.find_similar_questions(user_id, question, min_similarity=0.7, limit=1)
        
        # Use the found similar Q&A if the list is not empty
        if similar_qa:
            logger.info(f"Found similar Q&A in history with similarity: {similar_qa[0]['similarity']:.2f}")
            return {
                "suggestion": similar_qa[0]["answer"],
                "confidence": similar_qa[0]['similarity'], # Use the actual similarity score
                "source": "qa_history",
                "alternative_suggestions": [] # Can be populated later if needed
            }
            
        # If no similar question found, generate an answer using the LLM
        logger.info("No similar question found, generating answer using LLM.")
        try:
            # Generate response using LLM, passing user profile
            generated_response = await self._generate_answer_from_profile(user, question, context)
            return generated_response
        except Exception as e:
            logger.error(f"Error generating answer using LLM: {e}")
            # Fallback response if LLM fails
            return {
                "suggestion": "Could not generate a suggestion at this time.",
                "confidence": 0.1,
                "source": "error_fallback",
                "alternative_suggestions": []
            }
    
    def find_similar_questions(
        self, 
        user_id: UUID, 
        question: str, 
        min_similarity: float = 0.7,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar questions in the Q&A history using semantic search.
        
        Args:
            user_id: User ID
            question: Question text
            min_similarity: Minimum similarity score
            limit: Maximum number of results
            
        Returns:
            List[Dict]: Similar Q&A pairs with similarity scores
        """
        if not VECTOR_AVAILABLE:
            logger.warning("Vector search not available, falling back to text search")
            return self._fallback_question_search(user_id, question, limit)
        
        # Generate embedding for the question
        embedding = self._get_embedding_for_text(question)
        if not embedding:
            logger.warning("Failed to generate embedding, falling back to text search")
            return self._fallback_question_search(user_id, question, limit)
        
        # Perform vector search
        # In a real implementation, this would use PostgreSQL's vector operations
        results = (
            self.db.query(
                QAHistory,
                # Calculate cosine similarity (1 - cosine_distance) using the vector column method
                (1 - QAHistory.question_embedding.cosine_distance(embedding)).label("similarity")
            )
            .filter(QAHistory.user_id == user_id)
            # Use the vector column method here too
            .filter((1 - QAHistory.question_embedding.cosine_distance(embedding)) >= min_similarity)
            # And here for ordering
            .order_by((1 - QAHistory.question_embedding.cosine_distance(embedding)).desc())
            .limit(limit)
            .all()
        )
        
        # Format results
        similar_questions = []
        for qa, similarity in results:
            context_dict = json.loads(qa.context_json) if qa.context_json else {}
            similar_questions.append({
                "id": str(qa.id),
                "question": qa.question_text,
                "answer": qa.answer_text,
                "similarity": float(similarity),
                "context": context_dict,
                "created_at": qa.created_at.isoformat()
            })
        
        return similar_questions
    
    def _fallback_question_search(self, user_id: UUID, question: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback to simple text search when vector search is not available."""
        # This is a very basic text search using SQL LIKE
        # In a real implementation, you might want to use a more sophisticated
        # text search approach, like PostgreSQL's full-text search
        results = (
            self.db.query(QAHistory)
            .filter(QAHistory.user_id == user_id)
            .filter(QAHistory.question_text.ilike(f"%{question}%"))
            .order_by(QAHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        
        # Format results with a placeholder similarity score
        similar_questions = []
        for qa in results:
            context_dict = json.loads(qa.context_json) if qa.context_json else {}
            similar_questions.append({
                "id": str(qa.id),
                "question": qa.question_text,
                "answer": qa.answer_text,
                "similarity": 0.8,  # Placeholder similarity
                "context": context_dict,
                "created_at": qa.created_at.isoformat()
            })
        
        return similar_questions
    
    def save_qa_pair(
        self, 
        user_id: UUID, 
        question: str, 
        answer: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a new question-answer pair.
        
        Args:
            user_id: User ID
            question: Question text
            answer: Answer text
            context: Additional context (company, job, etc.)
            
        Returns:
            Dict: Saved Q&A pair
            
        Raises:
            ValueError: If user not found or saving fails
        """
        # Check if user exists
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Generate embedding for the question
        embedding = self._get_embedding_for_text(question) if VECTOR_AVAILABLE else None
        
        # Prepare context JSON
        context_json = json.dumps(context) if context else None
        
        # Create Q&A entry
        qa_entry = QAHistory(
            user_id=user_id,
            question_text=question,
            answer_text=answer,
            context_json=context_json,
            source="user_input",
        )
        
        # Add embedding if available
        if VECTOR_AVAILABLE and embedding is not None:
            qa_entry.question_embedding = embedding
        
        try:
            # Save to database
            self.db.add(qa_entry)
            self.db.commit()
            self.db.refresh(qa_entry)
            
            # Return the saved Q&A pair
            return {
                "id": str(qa_entry.id),
                "question": qa_entry.question_text,
                "answer": qa_entry.answer_text,
                "context": context,
                "created_at": qa_entry.created_at.isoformat()
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save Q&A pair: {e}")
            raise ValueError("Failed to save Q&A pair")
    
    def _get_embedding_for_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text.
        
        Uses the EmbeddingService to get embeddings from Vertex AI.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector or None if generation fails
        """
        return self.embedding_service.get_embedding(text)
    
    async def _generate_answer_from_profile(
        self, 
        user: User, 
        question: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an answer based on user profile using the LLMService.
        
        Args:
            user: User object with profile data
            question: Question text
            context: Additional context
            
        Returns:
            Dict: Generated response dictionary from LLMService
        """
        logger.info(f"Generating answer for '{question[:50]}...' using LLM and profile for user {user.id}")
        
        # Format user profile data for the LLM
        # (Convert complex objects to simpler representations if needed)
        user_profile_data = {
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "phone": user.phone,
            "location": user.address_json,
            # "headline": user.headline,
            # "summary": user.summary,
            "work_experience": [
                {
                    "role": exp.role,
                    "company": exp.company_name,
                    "duration": f"{exp.start_date} to {exp.end_date or 'Present'}",
                    "description": exp.description
                } for exp in user.work_experiences
            ],
            "education": [
                {
                    "institution": edu.institution_name,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "duration": f"{edu.start_date} to {edu.end_date or 'Present'}"
                } for edu in user.educations
            ],
            "skills": [skill.skill_name for skill in user.skills]
            # Add other relevant profile fields if needed
        }
        
        try:
            # Call the LLM service
            response_dict = await self.llm_service.generate_contextual_response(
                user_id=user.id,
                question=question,
                context=context,
                user_profile=user_profile_data
            )
            return response_dict
            
        except Exception as e:
            logger.error(f"LLMService call failed during answer generation: {e}")
            # Re-raise or return a specific error structure
            raise # Re-raise the exception for the caller (suggest_answer) to handle

    # Comment out MongoDB functions since they're not compatible with current database setup
    """
    @staticmethod
    async def create_qa_pair(qa_pair_data: QAPairCreate) -> QAPair:
        # MongoDB implementation removed
        pass
    
    @staticmethod
    async def get_qa_pairs_by_user(user_id: str) -> List[QAPair]:
        # MongoDB implementation removed
        pass
    """ 