"""
QnAManagerAgent implementation.

This agent is responsible for managing the storage and retrieval of
question-answer pairs using semantic search capabilities.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from google.adk import Agent, AgentBuilder, LlmAgent, FunctionTool, VertexAiLlm, ToolContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# LLM model configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "textembedding-gecko")

def search_qa_history_tool(
    tool_context: ToolContext,
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
    
    # In a real implementation, you would:
    # 1. Generate an embedding for the question
    # 2. Search the database for similar question embeddings
    # 3. Return matches above the similarity threshold
    
    # Placeholder response
    return {
        "matches": [
            {
                "question": "What are your strongest technical skills?",
                "answer": "My strongest technical skills are Python programming, machine learning, and cloud infrastructure.",
                "similarity": 0.92,
                "context": {"company": "Example Corp", "job_title": "ML Engineer"}
            },
            {
                "question": "Describe your technical expertise.",
                "answer": "I have expertise in Python, JavaScript, SQL, AWS, and machine learning, with 5+ years of professional experience.",
                "similarity": 0.85,
                "context": {"company": "Tech Innovators", "job_title": "Senior Developer"}
            }
        ]
    }

def generate_question_embedding_tool(
    tool_context: ToolContext,
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
    
    # In a real implementation, you would:
    # 1. Call an embedding model API (e.g., Vertex AI text embeddings)
    # 2. Process the response
    # 3. Return the embedding vector
    
    # Placeholder response (just a few random values representing a vector)
    return {
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],  # This would normally be a much larger vector
        "model": GEMINI_EMBEDDING_MODEL,
        "dimension": 768,  # Example dimension, depends on the model
    }

def store_qa_pair_tool(
    tool_context: ToolContext,
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
    
    # In a real implementation, you would:
    # 1. Generate an embedding for the question
    # 2. Store the Q&A pair and embedding in the database
    
    # Placeholder response
    return {
        "status": "success",
        "message": "Q&A pair stored successfully",
        "qa_id": "123e4567-e89b-12d3-a456-426614174000",  # Example UUID
    }

def generate_answer_tool(
    tool_context: ToolContext,
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
    
    # In a real implementation, you would:
    # 1. Retrieve relevant user profile data
    # 2. Use the LLM to generate a personalized answer
    # 3. Possibly check against previous answers for consistency
    
    # Placeholder response
    return {
        "answer": "I have 5 years of experience with Python development, including work on machine learning projects and web applications.",
        "confidence": 0.8,
        "source": "llm_generation",
    }

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
    search_tool = FunctionTool(
        name="search_qa_history",
        description="Search Q&A history for similar questions using semantic search",
        function=search_qa_history_tool
    )
    
    embedding_tool = FunctionTool(
        name="generate_question_embedding",
        description="Generate an embedding vector for a question",
        function=generate_question_embedding_tool
    )
    
    store_tool = FunctionTool(
        name="store_qa_pair",
        description="Store a new question-answer pair in the database",
        function=store_qa_pair_tool
    )
    
    generate_tool = FunctionTool(
        name="generate_answer",
        description="Generate an answer for a question based on user profile data",
        function=generate_answer_tool
    )
    
    # Create the agent
    qna_agent = AgentBuilder.create()
    
    # Add tools
    qna_agent.with_tools([
        search_tool,
        embedding_tool,
        store_tool,
        generate_tool,
    ])
    
    # Configure LLM
    qna_agent.with_llm(VertexAiLlm(model_name=GEMINI_MODEL))
    
    # Set system prompt
    qna_agent.with_system_prompt("""
    You are a Q&A Manager Agent, specialized in managing question-answer pairs for job applications.
    Your responsibilities include:
    
    - Storing new question-answer pairs with appropriate embeddings
    - Searching for similar questions using semantic search
    - Generating personalized answers based on user profile data when no existing answer is found
    
    Always prioritize finding exact or close matches in the existing Q&A history, 
    as these represent answers the user has already approved. Only generate new answers
    when no suitable match is found.
    """)
    
    # Build and return the agent
    return qna_agent.build() 