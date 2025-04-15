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

from src.database.models import User, QAHistory
from src.services.user_service import UserService
from src.services.embedding_service import EmbeddingService

# Configure logging
logger = logging.getLogger(__name__)

# Check if pgvector is available
try:
    from pgvector.sqlalchemy import Vector
    from pgvector.sqlalchemy.functions import cosine_distance
    VECTOR_AVAILABLE = True
except ImportError:
    Vector = None
    cosine_distance = None
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
    
    def suggest_answer(
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
        
        if similar_qa and len(similar_qa) > 0:
            # Found a similar question, return its answer
            best_match = similar_qa[0]
            return {
                "suggestion": best_match["answer"],
                "confidence": best_match["similarity"],
                "source": "qa_history",
                "alternative_suggestions": None
            }
        else:
            # No similar question found, generate an answer
            # In a real implementation, this would use an LLM to generate
            # a personalized answer based on the user's profile and context
            
            # Placeholder answer generator
            generated_answer = self._generate_answer_from_profile(user, question, context)
            return {
                "suggestion": generated_answer,
                "confidence": 0.6,  # Lower confidence for generated answers
                "source": "profile_data",
                "alternative_suggestions": None
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
                # Calculate cosine similarity (1 - cosine_distance)
                (1 - func.cosine_distance(QAHistory.question_embedding, embedding)).label("similarity")
            )
            .filter(QAHistory.user_id == user_id)
            .filter((1 - func.cosine_distance(QAHistory.question_embedding, embedding)) >= min_similarity)
            .order_by((1 - func.cosine_distance(QAHistory.question_embedding, embedding)).desc())
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
    
    def _generate_answer_from_profile(
        self, 
        user: User, 
        question: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an answer based on user profile.
        
        In a real implementation, this would use an LLM.
        
        Args:
            user: User object with profile data
            question: Question text
            context: Additional context
            
        Returns:
            str: Generated answer
        """
        # Very basic placeholder implementation that returns canned responses
        # based on question keywords
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["experience", "work history", "job history"]):
            experiences = user.work_experiences
            if experiences:
                latest = next((exp for exp in experiences if exp.is_current), experiences[0])
                return f"I have {len(experiences)} years of work experience, most recently as a {latest.role} at {latest.company_name}."
            return "I have experience in various roles throughout my career."
            
        elif any(word in question_lower for word in ["education", "degree", "university", "college"]):
            educations = user.educations
            if educations:
                highest = educations[0]  # Assuming sorted by recency
                return f"I have a {highest.degree} in {highest.field_of_study or 'my field'} from {highest.institution_name}."
            return "I have completed my education with focus on relevant coursework."
            
        elif any(word in question_lower for word in ["skill", "technology", "programming", "language"]):
            skills = user.skills
            skill_list = ", ".join([skill.skill_name for skill in skills[:5]]) if skills else "various technical skills"
            return f"My key skills include {skill_list}."
            
        elif any(word in question_lower for word in ["strength", "quality", "good at"]):
            return "My key strengths include problem-solving, teamwork, and attention to detail."
            
        elif any(word in question_lower for word in ["weakness", "improve", "challenge"]):
            return "I continuously work on improving my time management skills by prioritizing tasks effectively."
            
        elif any(word in question_lower for word in ["salary", "compensation", "pay", "expect"]):
            return "My salary expectations are flexible and based on the overall compensation package, responsibilities, and growth opportunities."
        
        # Generic fallback response
        return "I would be happy to discuss this further in an interview." 