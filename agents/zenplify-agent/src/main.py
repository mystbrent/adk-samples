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
from google.adk import api_server

# Import local modules
from src.api.router import router as api_router
from src.database.session import engine, Base
from src.agents.orchestrator import get_root_agent

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

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down application")
    # Clean up any resources here

# Direct ADK API server initialization
adk_app = api_server.initialize(get_root_agent())

# Mount ADK app endpoints under '/adk' path
app.mount("/adk", adk_app)

# Run the server if executed directly
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"Starting Zenplify LLM Agent on {host}:{port}")
    uvicorn.run("src.main:app", host=host, port=port, reload=True) 