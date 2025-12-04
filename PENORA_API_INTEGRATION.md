# Penora API Integration Guide for External Apps (ImageGene)

## Overview
Penora provides real-time API access for external applications to fetch user projects and workspace data. The API uses SSO authentication and proper user isolation to ensure data security.

## API Base URL
```
Production: https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev
```

## Authentication
All API calls require user authentication through URL parameters:
- `user_id`: The unique user identifier from SSO
- `jwt_token`: (Optional) JWT token for enhanced security
- `first_name`: User's first name
- `last_name`: User's last name
- `email`: User's email address

## API Endpoints

### 1. Get User Projects
```
GET /api/user-projects
```

**Parameters:**
- `user_id` (required): User's unique identifier
- `jwt_token` (optional): JWT authentication token
- `first_name` (optional): For user info
- `last_name` (optional): For user info
- `email` (optional): For user info

**Example Request:**
```bash
curl "https://penora.replit.dev/api/user-projects?user_id=101902121794505150000&first_name=developer&last_name=aim&email=developeraimw@gmail.com"
```

**Example Response:**
```json
{
  "success": true,
  "projects": [
    {
      "id": "6HDC8U",
      "title": "1 Page(s) - Enhanced workspace features te...",
      "content": "Your generated content here...",
      "created_at": "2025-08-11T08:09:00.000000",
      "updated_at": "2025-08-11T08:09:00.000000",
      "size": 1245,
      "word_count": 187,
      "type": "penora_project"
    }
  ],
  "total_count": 1,
  "user_info": {
    "user_id": "101902121794505150000",
    "username": "developer aim",
    "email": "developeraimw@gmail.com",
    "app": "penora"
  },
  "api_version": "1.0",
  "timestamp": "2025-08-20T04:57:56.650193"
}
```

### 2. Get Specific Project Details
```
GET /api/project/{project_code}
```

**Parameters:**
- `project_code` (in URL): The unique project code (e.g., "6HDC8U")
- `user_id` (required): User's unique identifier
- `jwt_token` (optional): JWT authentication token

**Example Request:**
```bash
curl "https://penora.replit.dev/api/project/6HDC8U?user_id=101902121794505150000"
```

**Example Response:**
```json
{
  "success": true,
  "project": {
    "id": "6HDC8U",
    "title": "1 Page(s) - Enhanced workspace features",
    "content": "Full project content here...",
    "created_at": "2025-08-11T08:09:00.000000",
    "updated_at": "2025-08-11T08:09:00.000000",
    "size": 1245,
    "word_count": 187,
    "type": "penora_project",
    "user_id": "101902121794505150000"
  },
  "api_version": "1.0",
  "timestamp": "2025-08-20T04:57:56.650193"
}
```

### 3. Cross-App Authentication
```
POST /api/cross-app/auth
```

**Request Body:**
```json
{
  "jwt_token": "your_jwt_token",
  "user_id": "101902121794505150000",
  "first_name": "developer",
  "last_name": "aim",
  "email": "developeraimw@gmail.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Authentication successful",
  "user_id": "101902121794505150000",
  "username": "developer aim",
  "email": "developeraimw@gmail.com"
}
```

## Integration for ImageGene

### Step 1: User Authentication
When a user accesses ImageGene from Penora, authenticate them using the cross-app auth endpoint.

### Step 2: Fetch User Projects
Use the `/api/user-projects` endpoint to populate dropdowns or project lists in ImageGene interface.

### Step 3: Access Project Content
When user selects a project, use `/api/project/{code}` to fetch full content for use in ImageGene.

### Error Handling
All endpoints return consistent error format:
```json
{
  "success": false,
  "error": "Error description",
  "details": "Detailed error information"
}
```

**Common Error Codes:**
- `401`: Missing or invalid user authentication
- `404`: Project not found or access denied
- `500`: Internal server error

## Security Features
- **User Isolation**: Each user can only access their own projects
- **Project Codes**: Unique 6-character codes for each project
- **Session Management**: Proper session handling for cross-app access
- **Data Validation**: Input validation and sanitization

## Testing the API

### Test User Projects API:
```bash
curl -s "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/user-projects?user_id=101902121794505150000" | jq .
```

### Test Specific Project:
```bash
curl -s "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev/api/project/6HDC8U?user_id=101902121794505150000" | jq .
```

## Rate Limiting
Currently no rate limiting is implemented, but recommend reasonable usage patterns.

## Support
For API integration support, ensure proper user_id and authentication parameters are included in all requests.