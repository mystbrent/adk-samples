"""
QnAManagerAgent implementation.

This agent is responsible for managing the storage and retrieval of
question-answer pairs using semantic search capabilities.
"""

import os
import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from google.adk import Agent
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, tool_context
from google.adk.models.google_llm import Gemini
from dotenv import load_dotenv

# Import local services
from src.database.session import get_db
from src.services.qa_service import QAService
from src.services.embedding_service import EmbeddingService

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# LLM model configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "textembedding-gecko")

def search_qa_history_tool(
    tool_context: tool_context,
    user_id: str,
    question: str,
    min_similarity: float = 0.7
) -> Dict[str, Any]:
    """
    Tool to search Q&A history for similar questions.
    
    Args:
        tool_context: Context for the tool execution
        user_id: ID of the user
        question: Question to search for
        min_similarity: Minimum similarity score to consider a match
        
    Returns:
        Dict: Matching Q&A pairs with similarity scores
    """
    logger.info(f"Searching Q&A history for question: {question}")
    
    # Convert string user_id to UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.error(f"Invalid user_id format: {user_id}")
        return {"matches": [], "error": "Invalid user_id format"}
    
    # Create a database session
    db = next(get_db())
    qa_service = QAService(db)
    
    try:
        # Find similar questions using the QA service
        similar_questions = qa_service.find_similar_questions(
            user_id=user_uuid,
            question=question,
            min_similarity=min_similarity,
            limit=5
        )
        
        # Convert to the expected format
        matches = [
            {
                "question": q["question"],
                "answer": q["answer"],
                "similarity": q["similarity"],
                "context": q["context"]
            }
            for q in similar_questions
        ]
        
        return {"matches": matches}
    except Exception as e:
        logger.error(f"Error searching QA history: {e}")
        return {"matches": [], "error": str(e)}
    finally:
        db.close()

def generate_question_embedding_tool(
    tool_context: tool_context,
    question: str
) -> Dict[str, Any]:
    """
    Tool to generate an embedding for a question.
    
    Args:
        tool_context: Context for the tool execution
        question: Question text to embed
        
    Returns:
        Dict: Embedding vector
    """
    logger.info(f"Generating embedding for question: {question}")
    
    # Initialize embedding service
    embedding_service = EmbeddingService()
    
    try:
        # Generate embedding
        embedding = embedding_service.get_embedding(question)
        
        if embedding:
            return {
                "embedding": embedding,
                "model": GEMINI_EMBEDDING_MODEL,
                "dimension": len(embedding)
            }
        else:
            logger.error("Failed to generate embedding")
            return {
                "embedding": None,
                "error": "Failed to generate embedding"
            }
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return {
            "embedding": None,
            "error": str(e)
        }

def store_qa_pair_tool(
    tool_context: tool_context,
    user_id: str,
    question: str,
    answer: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Tool to store a new question-answer pair.
    
    Args:
        tool_context: Context for the tool execution
        user_id: ID of the user
        question: Question text
        answer: Answer text
        context: Additional context (company, job, etc.)
        
    Returns:
        Dict: Status of the operation
    """
    logger.info(f"Storing Q&A pair: {question} -> {answer}")
    
    # Convert string user_id to UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.error(f"Invalid user_id format: {user_id}")
        return {
            "status": "error",
            "message": "Invalid user_id format"
        }
    
    # Create a database session
    db = next(get_db())
    qa_service = QAService(db)
    
    try:
        # Store Q&A pair using the QA service
        result = qa_service.save_qa_pair(
            user_id=user_uuid,
            question=question,
            answer=answer,
            context=context
        )
        
        return {
            "status": "success",
            "message": "Q&A pair stored successfully",
            "qa_id": result["id"]
        }
    except Exception as e:
        logger.error(f"Error storing QA pair: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()

def generate_answer_tool(
    tool_context: tool_context,
    user_id: str,
    question: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Tool to generate an answer for a question based on user profile data.
    
    Args:
        tool_context: Context for the tool execution
        user_id: ID of the user
        question: Question text
        context: Additional context (company, job, etc.)
        
    Returns:
        Dict: Generated answer
    """
    logger.info(f"Generating answer for question: {question}")
    
    # Convert string user_id to UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        logger.error(f"Invalid user_id format: {user_id}")
        return {
            "answer": None,
            "confidence": 0,
            "source": None,
            "error": "Invalid user_id format"
        }
    
    # Create a database session
    db = next(get_db())
    qa_service = QAService(db)
    
    try:
        # Generate answer using the QA service
        suggestion = qa_service.suggest_answer(
            user_id=user_uuid,
            question=question,
            context=context
        )
        
        return {
            "answer": suggestion["suggestion"],
            "confidence": suggestion["confidence"],
            "source": suggestion["source"]
        }
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return {
            "answer": None,
            "confidence": 0,
            "source": None,
            "error": str(e)
        }
    finally:
        db.close()

def get_qna_agent() -> Agent:
    """
    Create and configure the QnAManagerAgent.
    
    This agent is responsible for managing question-answer pairs,
    including storage, retrieval via semantic search, and generation
    of new answers.
    
    Returns:
        Agent: Configured QnAManagerAgent
    """
    # Define tools
    search_tool = FunctionTool(search_qa_history_tool)
    embedding_tool = FunctionTool(generate_question_embedding_tool)
    store_tool = FunctionTool(store_qa_pair_tool)
    generate_tool = FunctionTool(generate_answer_tool)
    
    # System prompt
    system_prompt = """
    You are a Q&A Manager Agent, specialized in managing question-answer pairs for job applications.
    Your responsibilities include:
    
    - Storing new question-answer pairs with appropriate embeddings
    - Searching for similar questions using semantic search
    - Generating personalized answers based on user profile data when no existing answer is found
    
    Always prioritize finding exact or close matches in the existing Q&A history, 
    as these represent answers the user has already approved. Only generate new answers
    when no suitable match is found.
    """
    
    # Create and return the agent
    return LlmAgent(
        llm=Gemini(model_name=GEMINI_MODEL),
        system_prompt=system_prompt,
        tools=[search_tool, embedding_tool, store_tool, generate_tool]
    ) 