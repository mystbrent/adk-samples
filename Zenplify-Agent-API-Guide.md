# Zenplify-Agent API Guide

This document explains how to use and test the Zenplify-Agent APIs for integration with a custom Chrome extension. It provides a comprehensive inventory of available endpoints, their functionality, required parameters, and examples of request/response formats.

## Table of Contents

1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [ADK Sessions and API Integration](#adk-sessions-and-api-integration)
4. [How to Test APIs](#how-to-test-apis)
5. [Common Integration Scenarios](#common-integration-scenarios)

## Overview

The Zenplify-Agent provides several REST API endpoints to support its Chrome extension integration. The core functionality includes:

- User profile management
- Form autofill data retrieval
- Handling unidentified form fields
- Saving Q&A pairs for future use

The backend is built using FastAPI and integrates with Google's Agent Development Kit (ADK) to power intelligent field suggestions and form filling.

## API Endpoints

### User Profile Endpoints

#### Create User Profile
- **URL**: `/api/users/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "resume_url": "https://example.com/resume.pdf",
    "github_username": "johndoe",
    "linkedin_url": "https://linkedin.com/in/johndoe"
  }
  ```
- **Response**: 
  ```json
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "created_at": "2023-06-01T12:00:00Z"
  }
  ```

#### Get User Profile
- **URL**: `/api/users/{user_id}`
- **Method**: `GET`
- **Response**: User profile data

#### Update User Profile
- **URL**: `/api/users/{user_id}`
- **Method**: `PUT`
- **Request Body**: Updated profile data
- **Response**: Updated user profile

### Autofill Endpoints

#### Get Autofill Data
- **URL**: `/api/autofill/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "context": {
      "company_name": "Acme Inc",
      "job_title": "Software Engineer",
      "job_description": "We are looking for a talented software engineer...",
      "page_url": "https://acme.com/careers/apply",
      "form_fields": ["first_name", "last_name", "email", "phone", "education", "experience"]
    }
  }
  ```
- **Response**: 
  ```json
  {
    "user_data": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@example.com",
      "phone": "555-123-4567",
      "address": "123 Main St",
      "city": "Anytown",
      "state": "CA",
      "zip": "12345",
      "country": "USA",
      "education": "Bachelor's in Computer Science from Stanford University",
      "experience": "Senior Developer at TechCorp, Software Engineer at StartupXYZ",
      "skills": "Python, JavaScript, React, Machine Learning",
      "linkedin": "https://linkedin.com/in/johndoe",
      "github": "https://github.com/johndoe",
      "company": "TechCorp",
      "currentJob": "Senior Developer"
    }
  }
  ```

#### Suggest for Unidentified Field
- **URL**: `/api/unidentified-fields/suggest/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "field_label": "Why do you want to work for our company?",
    "field_type": "textarea",
    "surrounding_text": "Tell us more about yourself",
    "context": {
      "company": "Acme Inc",
      "job_title": "Software Engineer"
    }
  }
  ```
- **Response**: 
  ```json
  {
    "suggestion": "I'm interested in working for Acme Inc because of its innovative approach to software development and strong focus on user experience...",
    "confidence": 0.85,
    "source": "qa_history",
    "alternative_suggestions": ["I've always admired Acme Inc's commitment to...", "Acme Inc's work on AI systems is particularly exciting..."]
  }
  ```

#### Save Q&A Pair
- **URL**: `/api/qa/save/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "question": "Why do you want to work for our company?",
    "answer": "I'm passionate about the innovative work Acme Inc is doing...",
    "context": {
      "company": "Acme Inc",
      "job_title": "Software Engineer"
    }
  }
  ```
- **Response**: 
  ```json
  {
    "status": "success",
    "message": "Q&A pair saved successfully"
  }
  ```

### ADK Session Endpoints

#### Create ADK Session
- **URL**: `/adk/sessions/{user_id}`
- **Method**: `POST`
- **Response**: 
  ```json
  {
    "session_id": "session-123456"
  }
  ```

#### Run ADK Agent
- **URL**: `/adk/run`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "session_id": "session-123456",
    "message": "Suggest an answer for 'Describe a challenging project you've worked on'"
  }
  ```
- **Response**: Array of ADK events

## ADK Sessions and API Integration

### How ADK Sessions Correlate with the Autofill API

The ADK (Agent Development Kit) session system is used to maintain context and state for conversations between the user and the LLM agents. Here's how it relates to the autofill API:

1. **Session Creation**: 
   - When a user starts using the Zenplify extension, an ADK session is created via the `/adk/sessions/{user_id}` endpoint
   - The returned `session_id` should be stored by the Chrome extension for subsequent requests

2. **Autofill Flow**:
   - When the user triggers an autofill action, the Chrome extension calls the `/api/autofill/` endpoint
   - While this endpoint doesn't require a session_id parameter, internally the service associates the request with the user's ADK session to maintain context
   - The `FormFillingOrchestratorAgent` uses this session context to provide more accurate autofill data

3. **Unidentified Fields**:
   - When encountering an unidentified field, the `/api/unidentified-fields/suggest/` endpoint is called
   - The agent uses the ADK session context to improve suggestions based on previous interactions

4. **Behind the Scenes**:
   - The `AutofillService` connects to the ADK session service to access user context
   - Previous interactions stored in the session help the agent make better decisions
   - The session maintains information about the current job application context

5. **Session State Persistence**:
   - The ADK's `InMemorySessionService` or other persistent session services store:
     - Previous questions and answers
     - User profile information
     - Job context information
     - Agent state

### Example Flow

1. Chrome extension creates a session:
   ```
   POST /adk/sessions/123e4567-e89b-12d3-a456-426614174000
   Response: { "session_id": "session-123456" }
   ```

2. Extension requests autofill data:
   ```
   POST /api/autofill/
   {
     "user_id": "123e4567-e89b-12d3-a456-426614174000",
     "context": { "company_name": "Acme Inc", ... }
   }
   ```

3. Backend processes:
   - Retrieves/creates ADK session
   - Calls orchestrator agent with context
   - Returns formatted user data

## How to Test APIs

### Prerequisites
- API endpoint URL (e.g., `http://localhost:8000` for local development)
- User ID (create one using the `/api/users/` endpoint)
- API testing tool (Postman, curl, or similar)

### Testing Steps

#### 1. Create a User
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "github_username": "johndoe"
  }'
```

#### 2. Create an ADK Session
```bash
curl -X POST http://localhost:8000/adk/sessions/YOUR_USER_ID
```
Save the returned `session_id` for later use.

#### 3. Test the Autofill API
```bash
curl -X POST http://localhost:8000/api/autofill/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "context": {
      "company_name": "Example Corp",
      "job_title": "Software Developer",
      "form_fields": ["first_name", "last_name", "email", "phone", "education", "experience"]
    }
  }'
```

#### 4. Test Unidentified Field Handling
```bash
curl -X POST http://localhost:8000/api/unidentified-fields/suggest/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "field_label": "What makes you a good fit for this role?",
    "context": {
      "company": "Example Corp",
      "job_title": "Software Developer"
    }
  }'
```

#### 5. Save a Q&A Pair
```bash
curl -X POST http://localhost:8000/api/qa/save/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "YOUR_USER_ID",
    "question": "What makes you a good fit for this role?",
    "answer": "My experience with similar technologies and collaborative approach...",
    "context": {
      "company": "Example Corp",
      "job_title": "Software Developer"
    }
  }'
```

## Common Integration Scenarios

### Scenario 1: Initial Form Detection
1. Extension detects a job application form
2. Create a new ADK session
3. Call the autofill API with detected form fields
4. Fill the form with returned data

### Scenario 2: Handling Unidentified Fields
1. Extension encounters a field it cannot map
2. Call the unidentified field suggestion API
3. Display suggestion to user
4. Save final answer as a Q&A pair

### Scenario 3: Learning from User Input
1. User manually fills a field
2. Extension captures the field label and value
3. Save as a Q&A pair for future reference
4. Subsequent autofill operations will use this learned data

### Scenario 4: Context-Aware Suggestions
1. Extension provides job context (company, role, description)
2. Autofill and suggestion APIs use this context to tailor responses
3. ADK session maintains this context for the duration of the application 