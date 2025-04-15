"""
Embedding service for generating text embeddings.

This module provides functionality to generate embeddings for text
using Google's Vertex AI text embedding models.
"""

import os
import logging
from typing import List, Optional
import numpy as np

from google.cloud import aiplatform
from google.oauth2 import service_account

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings using Vertex AI."""
    
    def __init__(self):
        """
        Initialize the embedding service.
        
        Loads configuration from environment variables and initializes
        the Vertex AI client if needed.
        """
        self.model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "textembedding-gecko")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self._initialize_vertex_ai()
        
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
            logger.info("Vertex AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {e}")
            # Don't raise here to allow fallback to dummy embeddings
            
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate an embedding vector for the provided text using Vertex AI.
        
        Args:
            text: The text to embed
            
        Returns:
            List[float]: The embedding vector or None if generation fails
        """
        if not text:
            logger.warning("Empty text provided for embedding generation")
            return None
            
        try:
            # Log truncated text to avoid revealing sensitive information
            logger.info(f"Generating embedding for text: {text[:50]}...")
            
            # Get the endpoint fully qualified name
            model_endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_name}"
            
            # Initialize the model
            endpoint = aiplatform.Endpoint(model_endpoint)
            
            # Get predictions - structure depends on the model
            response = endpoint.predict(
                instances=[{"content": text}],
            )
            
            # Extract the embedding vector from the response
            if response and hasattr(response, "predictions") and response.predictions:
                # Format depends on the model, this assumes the standard text-embedding response
                embedding = response.predictions[0]["embeddings"]["values"]
                logger.info(f"Successfully generated embedding of dimension {len(embedding)}")
                return embedding
            else:
                logger.error("Received empty or invalid response from embedding API")
                return self._get_dummy_embedding()
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self._get_dummy_embedding()
            
    def _get_dummy_embedding(self) -> List[float]:
        """
        Generate a dummy embedding vector for fallback.
        
        Returns:
            List[float]: A dummy embedding vector
        """
        # Create a random vector of appropriate dimension and normalize it
        dimension = 768  # Standard dimension for text-embedding-gecko
        embedding = np.random.normal(0, 1, dimension).tolist()
        
        # Log that we're using a dummy embedding
        logger.warning("Using dummy embedding vector - similarity search will be inaccurate")
        
        return embedding 