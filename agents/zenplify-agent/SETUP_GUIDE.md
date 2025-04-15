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

### 3. Build and Start the Containers

```bash
# Build and start all services
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

The API will be available at `http://localhost:8000`.

### 4. Run Database Migrations (First Time Only)

```bash
# Run migrations inside the container
docker-compose exec app poetry run alembic upgrade head
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

### Poetry Environment Issues

If you encounter issues with Poetry:

1. Check if Poetry is installed correctly: `poetry --version`
2. Try to recreate the environment: `poetry env remove python && poetry install`

### Permissions for Google Credentials

Make sure the Google credentials file has the correct path and permissions:

```bash
# Check file permissions
chmod 600 /path/to/credentials.json
```

## Additional Resources

- [Project Documentation](./README.md)
- [Development Phases](./DEVELOPMENT_PHASES.md)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Google ADK Documentation](https://developers.google.com/agent-development-kit) 