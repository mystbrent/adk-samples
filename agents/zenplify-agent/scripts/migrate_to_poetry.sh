#!/bin/bash

# Script to migrate from pip-based setup to Poetry

set -e  # Exit on error

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Installing now..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Checking if we're in the right directory..."
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Make sure you're in the project root directory."
    exit 1
fi

# Check if requirements.txt exists and save a backup
if [ -f "requirements.txt" ]; then
    echo "Backing up requirements.txt..."
    cp requirements.txt requirements.txt.bak
fi

# Activate Poetry's virtual environment
echo "Installing dependencies with Poetry..."
poetry install

# Install spaCy model
echo "Installing spaCy model..."
poetry run python -m spacy download en_core_web_md

# Generate lock file
echo "Generating Poetry lock file..."
poetry lock

# Initialize alembic if needed
if [ ! -f "alembic.ini" ]; then
    echo "Initializing alembic..."
    poetry run alembic init alembic
    
    # Check if example files exist and copy them
    if [ -f "alembic.ini.example" ]; then
        echo "Copying alembic.ini.example to alembic.ini..."
        cp alembic.ini.example alembic.ini
    fi
    
    # Create alembic/versions directory if it doesn't exist
    mkdir -p alembic/versions
    
    # Check if env.py example exists and copy it
    if [ -f "alembic/env.py.example" ]; then
        echo "Copying alembic/env.py.example to alembic/env.py..."
        cp alembic/env.py.example alembic/env.py
    fi
    
    echo ""
    echo "IMPORTANT: Before running migrations:"
    echo "1. Check alembic.ini to ensure the database URL is correct"
    echo "2. Check alembic/env.py to ensure it correctly imports your models"
fi

echo "Migration completed!"
echo ""
echo "To run the application, use: poetry run start"
echo "To run database migrations: poetry run alembic upgrade head"
echo "For more details, see the SETUP_GUIDE.md file." 