"""
GitHubProfileAgent implementation.

This agent is responsible for interacting with the GitHub API
to extract useful profile information for the user.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from google.adk import Agent
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, tool_context
from google.adk.models.google_llm import Gemini
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# LLM model configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

def fetch_github_profile_tool(
    tool_context: tool_context,
    username: str
) -> Dict[str, Any]:
    """
    Tool to fetch GitHub profile information.
    
    Args:
        tool_context: Context for the tool execution
        username: GitHub username
        
    Returns:
        Dict: GitHub profile data
    """
    logger.info(f"Fetching GitHub profile for username: {username}")
    
    # In a real implementation, you would:
    # 1. Use PyGithub or direct API calls to fetch user data
    # 2. Handle authentication with PAT if needed
    # 3. Structure the response
    
    # Placeholder response
    return {
        "username": username,
        "name": "John Doe",
        "bio": "Software engineer passionate about open source",
        "location": "San Francisco, CA",
        "website": "https://johndoe.com",
        "email": "john.doe@example.com",
        "followers": 42,
        "following": 57,
        "public_repos": 15,
        "created_at": "2015-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
    }

def fetch_github_repositories_tool(
    tool_context: tool_context,
    username: str,
    limit: Optional[int] = 10,
    include_forks: bool = False
) -> Dict[str, Any]:
    """
    Tool to fetch a user's GitHub repositories.
    
    Args:
        tool_context: Context for the tool execution
        username: GitHub username
        limit: Maximum number of repositories to return
        include_forks: Whether to include forked repositories
        
    Returns:
        Dict: Repository data
    """
    logger.info(f"Fetching repositories for username: {username}")
    
    # In a real implementation, you would:
    # 1. Use PyGithub or direct API calls to fetch repositories
    # 2. Filter based on include_forks
    # 3. Limit the results
    # 4. Extract useful information from each repository
    
    # Placeholder response
    return {
        "repositories": [
            {
                "name": "awesome-project",
                "description": "A really awesome project",
                "language": "Python",
                "stars": 123,
                "forks": 45,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "is_fork": False,
            },
            {
                "name": "cool-library",
                "description": "A cool utility library",
                "language": "JavaScript",
                "stars": 67,
                "forks": 12,
                "created_at": "2021-03-15T00:00:00Z",
                "updated_at": "2023-02-01T00:00:00Z",
                "is_fork": False,
            }
        ],
        "languages": {
            "Python": 5,
            "JavaScript": 3,
            "TypeScript": 2,
            "HTML/CSS": 3,
            "Java": 1,
            "Go": 1,
        }
    }

def extract_skills_from_github_tool(
    tool_context: tool_context,
    username: str
) -> Dict[str, Any]:
    """
    Tool to extract skills from GitHub profile and repositories.
    
    Args:
        tool_context: Context for the tool execution
        username: GitHub username
        
    Returns:
        Dict: Extracted skills and technologies
    """
    logger.info(f"Extracting skills from GitHub for username: {username}")
    
    # In a real implementation, you would:
    # 1. Fetch repositories and profile
    # 2. Analyze languages used
    # 3. Extract technologies from repository descriptions and READMEs
    # 4. Possibly analyze code to identify frameworks and libraries
    
    # Placeholder response
    return {
        "languages": ["Python", "JavaScript", "TypeScript", "HTML", "CSS", "Java", "Go"],
        "frameworks": ["React", "Django", "Flask", "Express"],
        "technologies": ["Docker", "Kubernetes", "AWS", "Git"],
        "confidence_score": 0.85,
    }

def get_github_agent() -> Agent:
    """
    Create and configure the GitHubProfileAgent.
    
    This agent is responsible for interacting with the GitHub API
    to extract useful profile information for the user.
    
    Returns:
        Agent: Configured GitHubProfileAgent
    """
    # Define tools
    profile_tool = FunctionTool(fetch_github_profile_tool)
    repositories_tool = FunctionTool(fetch_github_repositories_tool)
    skills_tool = FunctionTool(extract_skills_from_github_tool)
    
    # System prompt
    system_prompt = """
    You are a GitHub Profile Agent, specialized in extracting meaningful information from GitHub profiles.
    Your goal is to gather relevant data from a user's GitHub account, including:
    
    - Profile information (name, bio, location, etc.)
    - Repository data (names, descriptions, languages, stars, etc.)
    - Skills and technologies (programming languages, frameworks, tools)
    
    You should focus on identifying information that would be valuable for job applications,
    such as demonstrating technical skills, project experience, and activity level.
    """
    
    # Create and return the agent
    return LlmAgent(
        llm=Gemini(model_name=GEMINI_MODEL),
        system_prompt=system_prompt,
        tools=[profile_tool, repositories_tool, skills_tool]
    ) 