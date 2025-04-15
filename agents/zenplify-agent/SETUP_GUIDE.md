# Zenplify AI Agent Setup Guide

This guide provides instructions on how to set up and run the Zenplify AI Agent locally using Poetry for dependency management.

## Prerequisites

Before you begin, make sure you have the following installed:

- [Python 3.11+](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (optional, for containerized setup)
- [Git](https://git-scm.com/downloads)

## Setup Options

You can set up and run the Zenplify AI Agent in two ways:

1. Local development setup using Poetry
2. Containerized setup using Docker Compose

Choose the option that best suits your needs.

## Option 1: Local Development Setup (Poetry)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/zenplify-agent.git
cd zenplify-agent
```

### 2. Install Dependencies with Poetry

```bash
# Install all dependencies
poetry install

# Install spaCy language model
poetry run python -m spacy download en_core_web_md
```

### 3. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your specific configuration
```

Be sure to update the following key variables:
- `DATABASE_URL`: Database connection string
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google service account credentials
- `JWT_SECRET`: Secret key for JWT token generation

### 4. Run Database Migrations

If you're running the migrations for the first time, you need to initialize alembic:

```bash
# Initialize alembic configuration files
poetry run alembic init alembic
```

You can use the provided example configuration files:

```bash
# Copy example files to their expected locations
cp alembic.ini.example alembic.ini
mkdir -p alembic/versions
cp alembic/env.py.example alembic/env.py
```

Or customize your configuration:

```bash
# Edit alembic.ini to point to your database
# Replace sqlalchemy.url = driver://user:pass@localhost/dbname with your database URL
# For example: sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/zenplify_agent

# Edit alembic/env.py to import your models
# Add the following imports at the top:
# from src.database.session import Base
# target_metadata = Base.metadata
```

Then run the migrations:

```bash
# Create an initial migration
poetry run alembic revision --autogenerate -m "initial"

# Apply the migration
poetry run alembic upgrade head
```

If you've already set up alembic and just need to run migrations:

```bash
# Make sure your database is running
poetry run alembic upgrade head
```

### 5. Start the Application

```bash
# Start the application using Poetry
poetry run start
```

The API will be available at `http://localhost:8000`.

## Option 2: Containerized Setup (Docker Compose)

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/zenplify-agent.git
cd zenplify-agent
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your specific configuration
```

When using Docker Compose, make sure to set:
- `DATABASE_URL=postgresql://postgres:postgres@db:5432/zenplify_agent` (using the service name)
- Update all other required credentials

### 3. Start the Database Container

Note: The application container is currently commented out in docker-compose.yml. You will need to run the application locally while using the containerized database.

```bash
# Start the PostgreSQL database with pgvector extension
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

The PostgreSQL database will be available at `localhost:5432`.

### 4. Run the Application Locally with the Containerized Database

```bash
# Update your .env file to point to the containerized database:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/zenplify_agent

# Then run the application locally
poetry run start
```

The API will be available at `http://localhost:8000`.

### 5. Run Database Migrations

For the initial setup, you'll need to initialize alembic:

```bash
# Initialize alembic configuration files
poetry run alembic init alembic

# Copy example files to their expected locations
cp alembic.ini.example alembic.ini
mkdir -p alembic/versions
cp alembic/env.py.example alembic/env.py

# Make sure your DATABASE_URL in .env points to the containerized database
# postgresql://postgres:postgres@localhost:5432/zenplify_agent

# Create and apply migrations
poetry run alembic revision --autogenerate -m "initial"
poetry run alembic upgrade head
```

If alembic is already initialized:

```bash
# Make sure your database is running
poetry run alembic upgrade head
```

## Using the API

Once the application is running, you can interact with it using the following endpoints:

- API Documentation: `http://localhost:8000/docs`
- ADK Endpoints: `http://localhost:8000/adk`
- API Endpoints: `http://localhost:8000/api`

## Development Workflow

### Running Tests

```bash
# Run tests using Poetry
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src
```

### Adding New Dependencies

```bash
# Add a new production dependency
poetry add package-name

# Add a new development dependency
poetry add --group dev package-name
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update a specific package
poetry update package-name
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Ensure your database is running
2. Check the `DATABASE_URL` in your `.env` file
3. For Docker setup, check if the database container is healthy: `docker-compose ps`

### Docker Compose Configuration

The application service is currently commented out in docker-compose.yml:

1. This is intentional - you should run the application locally using Poetry
2. Only the database service will be started with `docker-compose up -d`
3. Make sure your DATABASE_URL points to localhost:5432 when using the containerized database

If you want to enable the container for the application as well:

```bash
# Uncomment the app section in docker-compose.yml, then run:
docker-compose up -d
# This will start both the database and application containers
```

### Poetry Environment Issues

If you encounter issues with Poetry:

1. Check if Poetry is installed correctly: `poetry --version`
2. Try to recreate the environment: `poetry env remove python && poetry install`

### Alembic Migration Issues

If you encounter the error `No config file 'alembic.ini' found`:

1. Make sure you're in the project root directory
2. Follow the initialization steps in the "Run Database Migrations" section
3. Check that the alembic.ini file exists and has the correct configuration

### Permissions for Google Credentials

Make sure the Google credentials file has the correct path and permissions:

```bash
# Check file permissions
chmod 600 /path/to/credentials.json
```

### Google ADK Version Compatibility Issues

If you encounter an error like:
```
ImportError: cannot import name 'api_server' from 'google.adk'
```

This is due to API changes in the Google ADK v0.1.0 release. To fix this issue:

1. Run the helper script to update imports and dependencies:
   ```bash
   python scripts/fix_adk_imports.py
   ```

2. Reinstall dependencies:
   ```bash
   poetry install
   ```

3. Ensure you're using the correct version of Google ADK (v0.1.0):
   ```bash
   poetry add google-adk@0.1.0
   ```

You can verify the release information at the [official GitHub repository](https://github.com/google/adk-python/releases).

## Additional Resources

- [Project Documentation](./README.md)
- [Development Phases](./DEVELOPMENT_PHASES.md)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Google ADK Documentation](https://developers.google.com/agent-development-kit)