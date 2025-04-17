"""
Main application entry point for the Zenplify LLM Agent.

This module initializes the FastAPI application, configures the ADK agent,
and sets up the API endpoints.
"""

import os
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk import Agent

# Import local modules
from src.api.router import router as api_router
from src.database.session import engine, Base

# Load environment variables
load_dotenv()

# Configure logging
logging_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
logging.basicConfig(
    level=logging_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Zenplify LLM Agent",
    description="AI agent for automated job application form filling",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Create database tables
    logger.info("Creating database tables if they don't exist")
    Base.metadata.create_all(bind=engine)
    
    # Initialize the root agent
    logger.info("Initializing ADK agent")
    # Additional agent initialization can go here

# Create a simple agent for now
def get_simple_agent() -> Agent:
    """Create a simple agent for testing."""
    return Agent(
        name="zenplify_agent",
        description="AI agent for automated job application form filling"
    )

# Create ADK Runner with in-memory session service
session_service = InMemorySessionService()
adk_runner = Runner(
    app_name="zenplify-agent",
    agent=get_simple_agent(),
    session_service=session_service
)

# Create FastAPI endpoints for ADK
@app.post("/adk/run")
async def run_agent(user_id: str, session_id: str, message: str):
    """Run the agent with a new message."""
    events = []
    async for event in adk_runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message={"role": "user", "parts": [{"text": message}]}
    ):
        events.append(event)
    return {"events": events}

@app.post("/adk/sessions/{user_id}")
async def create_session(user_id: str):
    """Create a new session for the user."""
    session = session_service.create_session(
        app_name="zenplify-agent",
        user_id=user_id,
    )
    return {"session_id": session.session_id}

def run_app():
    """Entry point for Poetry script to run the application."""
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting Zenplify LLM Agent on {host}:{port}")
    uvicorn.run("src.main:app", host=host, port=port, reload=True)

# Run the server if executed directly
if __name__ == "__main__":
    run_app() 