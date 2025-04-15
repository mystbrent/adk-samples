# Zenplify LLM Agent

An AI-powered agent built using Google's Python Agent Development Kit (ADK) to assist technology professionals in streamlining the job application process by intelligently filling out online application forms with personalized information.

## Overview

The Zenplify LLM Agent serves as the intelligent backend for the Zenplify Chrome extension. Its core responsibilities include:

- **Data Aggregation**: Source and consolidate user information from resumes, GitHub profiles, and previously answered application questions
- **Intelligent Retrieval & Generation**: Analyze form fields from job applications and provide appropriate answers based on user data
- **Data Persistence**: Store and manage user profiles, Q&A history, and job information
- **Learning Capability**: Capture and learn from new question-answer pairs to improve over time

## Architecture

The system follows a multi-agent architecture using Google's ADK framework:

- **FormFillingOrchestratorAgent**: Central coordinator that receives requests from Zenplify and orchestrates the response
- **ResumeParserAgent**: Handles parsing resume files (PDF, DOCX) into structured data
- **GitHubProfileAgent**: Interacts with GitHub API to fetch relevant profile information
- **QnAManagerAgent**: Manages storage and retrieval of historical question-answer pairs using semantic search

## Technology Stack

- **Framework**: Google Python Agent Development Kit (ADK)
- **Language**: Python 3.11+
- **Database**: PostgreSQL with pgvector for vector search capabilities
- **Key Libraries**: 
  - PyMuPDF (PDF parsing)
  - python-docx (DOCX parsing)
  - spaCy (NLP/NER)
  - PyGithub (GitHub API)
  - pgvector (Vector embeddings)
  - FastAPI (API framework)
- **LLM**: Google Gemini via Vertex AI
- **Deployment**: Docker containers running on Google Cloud Run/AWS Fargate/Azure Container Apps

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Docker (for containerization)
- Google Cloud account (for Vertex AI access)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/your-org/zenplify-agent.git
   cd zenplify-agent
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your configuration values
   ```

5. Run database migrations
   ```bash
   alembic upgrade head
   ```

6. Start the development server
   ```bash
   python -m src.main
   ```

## Project Structure

```
zenplify-agent/
├── alembic/                  # Database migration scripts
├── docker/                   # Docker configuration files
├── docs/                     # Documentation files
├── src/                      # Source code
│   ├── agents/               # ADK agents implementation
│   │   ├── orchestrator.py   # FormFillingOrchestratorAgent
│   │   ├── resume_parser.py  # ResumeParserAgent
│   │   ├── github.py         # GitHubProfileAgent
│   │   └── qna_manager.py    # QnAManagerAgent
│   ├── database/             # Database models and connections
│   ├── tools/                # Custom ADK tools implementation
│   ├── parsers/              # Resume and document parsing logic
│   ├── api/                  # API endpoints for Zenplify integration
│   ├── schemas/              # Pydantic schemas for data validation
│   ├── services/             # Business logic services
│   └── main.py              # Application entry point
├── tests/                    # Test suite
├── .env.example              # Example environment variables
├── Dockerfile                # Docker build configuration
├── docker-compose.yml        # Docker Compose configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## Development Workflow

1. Check `DEVELOPMENT_PHASES.md` for current project status and upcoming tasks
2. Create a feature branch for your work
3. Implement functionality following the established architecture
4. Write tests for new features
5. Submit a pull request for review

## Security Considerations

- All sensitive credentials are managed through secure secret management
- HTTPS is required for all API communication
- API endpoints are authenticated and authorized
- Container follows security best practices (non-root user, minimal base image)
- Regular vulnerability scanning for container images

## License

[MIT License](LICENSE) 