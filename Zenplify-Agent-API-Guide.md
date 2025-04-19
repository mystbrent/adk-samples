# Zenplify-Agent API Guide

This document explains how to use and test the Zenplify-Agent APIs for integration with a custom Chrome extension. It provides a comprehensive inventory of available endpoints, their functionality, required parameters, and examples of request/response formats.

## Table of Contents

1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Response Standards](#response-standards)
4. [ADK Sessions and API Integration](#adk-sessions-and-api-integration)
5. [How to Test APIs](#how-to-test-apis)
6. [Common Integration Scenarios](#common-integration-scenarios)
7. [Troubleshooting](#troubleshooting)

## Overview

The Zenplify-Agent provides several REST API endpoints to support its Chrome extension integration. The core functionality includes:

- User profile management
- Form autofill data retrieval
- Handling unidentified form fields
- Saving Q&A pairs for future use

The backend is built using FastAPI and integrates with Google's Agent Development Kit (ADK) to power intelligent field suggestions and form filling.

## Response Standards

All API endpoints in the Zenplify-Agent follow these standard response guidelines:

### Success Responses (200 OK)

A successful API response will:
- Return HTTP status code 200
- Contain a properly formatted JSON body with required fields
- Never return empty strings for required fields
- Use null values (not empty strings) for optional fields that don't have data
- Include all fields specified in the response schema, even if null

Example of a proper 200 OK response:
```json
{
  "first_name": "Gen",
  "last_name": "Mak",
  "email": "smith231@test.com",
  "phone": "0155812581",
  "address_json": {
    "street2": "string",
    "street1": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "postal_code": "12345",
    "country": "USA"
  },
  "github_username": "testgithub",
  "gender": "Male",
  "date_of_birth": "1990-10-10",
  "linkedin_url": "https://linkedin.com/",
  "portfolio_url": "https://jake.com/",
  "website_url": "https://jakeweb.com/",
  "work_experiences": [{ "company_name": "Microsoft Inc", "role": "Sr. Software Engineer", "start_date": "2020-10-10", "end_date": "2021-10-10" }],
  "educations": [{"degree": "MBA", "institution_name": "Harvard University", "start_date": "2010-10-10"}],
  "skills": [{"skill_name": "Node.js"}]
  }
```

### Error Responses

If the API cannot successfully complete the request, it will:
- Return an appropriate HTTP status code (400, 404, 500, etc.)
- Include a clear error message that explains the issue
- Provide guidance on how to fix the problem when applicable

Example of an error response:
```json
{
  "status": "error",
  "message": "User profile not found or incomplete",
  "details": "Ensure the user has completed their profile setup before using autofill",
  "requestId": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f"
}
```

### Validation Requirements

The API implementation must adhere to these validation requirements:

1. **Required Fields**: The following fields must never be empty strings and must always be provided in a 200 OK response:
   - firstName
   - lastName
   - email
   
2. **Optional Fields**: The following fields may be null but should never be empty strings:
   - phone
   - address
   - city
   - state
   - zip
   - country
   - education
   - experience
   - skills
   - linkedin
   - github
   - portfolio
   - website
   - company
   - currentJob

3. **Data Quality**: All returned data must:
   - Be properly formatted (names capitalized, phone numbers in proper format)
   - Be checked for validity before returning 
   - Be populated from the most reliable source available (user profile takes precedence over inferred data)

## API Endpoints

### User Profile Endpoints

#### Create User Profile
- **URL**: `/api/users/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  
  ```
  > **Note**: `first_name`, `last_name`, and `email` are required fields.
  
- **Response (201 Created)**: 
  ```json
  {
  "first_name": "Gen",
  "last_name": "Mak",
  "email": "smith231@test.com",
  "phone": "0155812581",
  "address_json": {
    "street2": "string",
    "street1": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "postal_code": "12345",
    "country": "USA"
  },
  "github_username": "testgithub",
  "gender": "Male",
  "date_of_birth": "1990-10-10",
  "linkedin_url": "https://linkedin.com/",
  "portfolio_url": "https://jake.com/",
  "website_url": "https://jakeweb.com/",
  "work_experiences": [{ "company_name": "Microsoft Inc", "role": "Sr. Software Engineer", "start_date": "2020-10-10", "end_date": "2021-10-10" }],
  "educations": [{"degree": "MBA", "institution_name": "Harvard University", "start_date": "2010-10-10"}],
  "skills": [{"skill_name": "Node.js"}]
  }
  ```
- **Error Responses**:
  - 400 Bad Request: Invalid or missing required fields
  - 409 Conflict: User with email already exists
  - 500 Internal Server Error: Server processing error

#### Get User Profile
- **URL**: `/api/users/{user_id}`
- **Method**: `GET`
- **Response (200 OK)**: 
  ```json
  {
    "id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "555-123-4567",
    "github_username": "johndoe",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "created_at": "2023-06-01T12:00:00Z",
    "updated_at": "2023-06-02T15:30:00Z"
  }
  ```
- **Error Responses**:
  - 404 Not Found: User ID doesn't exist

#### Update User Profile
- **URL**: `/api/users/{user_id}`
- **Method**: `PUT`
- **Request Body**: 
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "555-987-6543",
    "github_username": "johndoe-updated"
  }
  ```
- **Response (200 OK)**: Updated user profile (same format as Get User Profile)
- **Error Responses**:
  - 400 Bad Request: Invalid field format
  - 404 Not Found: User ID doesn't exist

### Autofill Endpoints

#### Get Autofill Data
- **URL**: `/api/autofill/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "context": {
      "company_name": "Acme Inc",
      "job_title": "Software Engineer",
      "job_description": "We are looking for a talented software engineer...",
      "page_url": "https://acme.com/careers/apply",
      "form_fields": ["first_name", "last_name", "email", "phone", "education", "experience"]
    }
  }
  ```
  > **Note**: `user_id` must be a valid UUID string.
  
- **Response (200 OK)**: 
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
- **Error Responses**:
  - 400 Bad Request: Invalid user_id format or missing required fields
  - 404 Not Found: User profile not found
  - 422 Unprocessable Entity: Profile data incomplete for required fields
  - 500 Internal Server Error: Error generating autofill data

#### Suggest for Unidentified Field
- **URL**: `/api/unidentified-fields/suggest/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "field_label": "Why do you want to work for our company?",
    "field_type": "textarea",
    "surrounding_text": "Tell us more about yourself",
    "context": {
      "company": "Acme Inc",
      "job_title": "Software Engineer"
    }
  }
  ```
  > **Note**: `user_id` and `field_label` are required fields.
  
- **Response (200 OK)**: 
  ```json
  {
    "suggestion": "I'm interested in working for Acme Inc because of its innovative approach to software development and strong focus on user experience. The company's commitment to technological advancement aligns perfectly with my passion for building cutting-edge solutions that solve real-world problems.",
    "confidence": 0.85,
    "source": "qa_history",
    "alternative_suggestions": [
      "I've always admired Acme Inc's commitment to innovation and excellence in the software industry. Your recent work on AI-driven solutions particularly resonates with my background and interests.",
      "Acme Inc's work on AI systems is particularly exciting to me, and I believe my experience with machine learning algorithms would allow me to contribute meaningfully to your team."
    ]
  }
  ```
- **Error Responses**:
  - 400 Bad Request: Missing required fields or invalid format
  - 404 Not Found: User not found
  - 500 Internal Server Error: Failed to generate suggestion

#### Save Q&A Pair
- **URL**: `/api/qa/save/`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "question": "Why do you want to work for our company?",
    "answer": "I'm passionate about the innovative work Acme Inc is doing in the field of artificial intelligence, particularly your recent advances in natural language processing. My background in computational linguistics and machine learning makes this an exciting opportunity where I can both contribute and grow professionally.",
    "context": {
      "company": "Acme Inc",
      "job_title": "Software Engineer"
    }
  }
  ```
  > **Note**: `user_id`, `question`, and `answer` are required fields and cannot be empty.
  
- **Response (201 Created)**: 
  ```json
  {
    "status": "success",
    "message": "Q&A pair saved successfully",
    "qa_id": "5f8a3e2c-7b6d-4c5e-9f7a-8b2c3d4e5f6a"
  }
  ```
- **Error Responses**:
  - 400 Bad Request: Missing required fields or empty strings provided
  - 404 Not Found: User not found
  - 500 Internal Server Error: Failed to save Q&A pair

### ADK Session Endpoints

#### Create ADK Session
- **URL**: `/adk/sessions/{user_id}`
- **Method**: `POST`
- **Response (200 OK)**: 
  ```json
  {
    "session_id": "session-123456",
    "created_at": "2023-06-01T12:00:00Z",
    "expires_at": "2023-06-01T13:00:00Z"
  }
  ```
  > **Note**: Replace `{user_id}` with a valid UUID string.
  
- **Error Responses**:
  - 400 Bad Request: Invalid user ID format
  - 404 Not Found: User not found
  - 500 Internal Server Error: Error creating session

#### Run ADK Agent
- **URL**: `/adk/run`
- **Method**: `POST`
- **Request Body**: 
  ```json
  {
    "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "session_id": "session-123456",
    "message": "Suggest an answer for 'Describe a challenging project you've worked on'"
  }
  ```
- **Response (200 OK)**: 
  ```json
  {
    "events": [
      {
        "type": "thinking",
        "content": "Analyzing user profile and past project experiences..."
      },
      {
        "type": "response",
        "content": "During my time at TechCorp, I led the development of a real-time data processing pipeline that handled over 10 million events per day. The challenge was ensuring sub-second latency while maintaining data integrity across distributed systems. I implemented a microservice architecture using Kafka for message queuing and designed a custom throttling mechanism to handle traffic spikes. The solution reduced processing time by 60% and improved system reliability by implementing comprehensive error handling and recovery mechanisms."
      }
    ],
    "suggestions": [
      "I implemented a machine learning model to predict customer churn with 92% accuracy using Python and TensorFlow.",
      "I developed a cross-platform mobile application using React Native that synchronized data across multiple devices in real-time."
    ]
  }
  ```
- **Error Responses**:
  - 400 Bad Request: Missing required fields
  - 404 Not Found: User or session not found
  - 500 Internal Server Error: Agent execution error

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
   POST /adk/sessions/7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f
   Response: { "session_id": "session-123456" }
   ```

2. Extension requests autofill data:
   ```
   POST /api/autofill/
   {
     "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
     "context": { "company_name": "Acme Inc", "job_title": "Software Engineer" }
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

This will return a user ID that you'll use in subsequent requests. Make sure to save it.

#### 2. Create an ADK Session
```bash
curl -X POST "http://localhost:8000/adk/sessions/7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f"
```
> Replace the UUID with the actual user ID returned from step 1.

Save the returned `session_id` for later use.

#### 3. Test the Autofill API
```bash
curl -X POST http://localhost:8000/api/autofill/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "context": {
      "company_name": "Example Corp",
      "job_title": "Software Developer",
      "form_fields": ["first_name", "last_name", "email", "phone", "education", "experience"]
    }
  }'
```
> Replace the UUID with the actual user ID returned from step 1.

#### 4. Test Unidentified Field Handling
```bash
curl -X POST http://localhost:8000/api/unidentified-fields/suggest/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "field_label": "What makes you a good fit for this role?",
    "context": {
      "company": "Example Corp",
      "job_title": "Software Developer"
    }
  }'
```
> Replace the UUID with the actual user ID returned from step 1.

#### 5. Save a Q&A Pair
```bash
curl -X POST http://localhost:8000/api/qa/save/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f",
    "question": "What makes you a good fit for this role?",
    "answer": "My experience with similar technologies and collaborative approach make me well-suited for this position.",
    "context": {
      "company": "Example Corp",
      "job_title": "Software Developer"
    }
  }'
```
> Replace the UUID with the actual user ID returned from step 1.

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

## Troubleshooting

### Empty Fields in Response
If your API calls are returning empty strings instead of proper data, check the following:

1. **User Profile Completeness**: Ensure the user has completed their profile with all required data.
   ```bash
   curl -X GET http://localhost:8000/api/users/7f8d3e2c-9a6b-4c5d-8e7f-1a2b3c4d5e6f
   ```
   > Replace the UUID with the actual user ID.

2. **Database Connectivity**: Verify that the database connection is functioning correctly.

3. **Data Source Population**: Check if the resume parsing and GitHub data extraction have successfully populated the database.

4. **Server Logs**: Examine server logs for any errors or warnings during data retrieval.

5. **Default Values**: The implementation should use sensible defaults or null values (not empty strings) when data is unavailable.

### Common Errors and Solutions

1. **Invalid UUID Format**: Make sure all UUIDs are in the correct format (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
   ```
   "Invalid UUID format: Must be a valid UUID string"
   ```
   **Solution**: Use a proper UUID format or generate a new user and use the returned ID.

2. **Missing Required Fields**: Ensure all required fields are included in your requests.
   ```
   "field required: Question cannot be empty"
   ```
   **Solution**: Include all required fields with non-empty values.

3. **User Not Found**: Verify that the user ID exists in the database.
   ```
   "User not found"
   ```
   **Solution**: Create a new user or use an existing valid user ID.

### Error Code Reference
- **400**: Request format is invalid or missing required parameters
- **404**: The requested resource (user, session, etc.) was not found
- **409**: A conflict occurred (e.g., duplicate resource)
- **422**: Request format is valid but content cannot be processed
- **500**: Server-side error occurred during processing

For persistent issues, provide the following when contacting support:
- User ID
- Exact API endpoint called
- Request body used
- Response received
- Any error messages from the console 