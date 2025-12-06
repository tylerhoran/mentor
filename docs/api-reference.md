# API Reference

Mentor exposes a RESTful API for all operations. The API is documented with OpenAPI and available at `/docs` when running.

## Authentication

### Register User

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "role": "faculty"  // or "student"
}
```

Response:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "faculty"
}
```

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

## Courses

### Create Course

```http
POST /api/courses
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Introduction to Python",
  "code": "CS101",
  "description": "Learn Python programming",
  "pedagogy_config": {
    "teaching_style": "socratic",
    "difficulty_progression": "adaptive",
    "hint_frequency": "medium"
  }
}
```

### List Courses

```http
GET /api/courses
Authorization: Bearer {token}
```

### Get Course

```http
GET /api/courses/{course_id}
Authorization: Bearer {token}
```

### Update Course

```http
PUT /api/courses/{course_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Course Name"
}
```

## Concepts

### Create Concept

```http
POST /api/courses/{course_id}/concepts
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Variables",
  "description": "Understanding variables and data types",
  "bloom_level": "understand",
  "prerequisites": [],
  "learning_objectives": ["Declare variables", "Identify data types"]
}
```

### List Concepts

```http
GET /api/courses/{course_id}/concepts
Authorization: Bearer {token}
```

### Add Misconception

```http
POST /api/courses/{course_id}/concepts/{concept_id}/misconceptions
Authorization: Bearer {token}
Content-Type: application/json

{
  "misconception": "Variables are boxes",
  "correction": "Variables are references to objects",
  "detection_patterns": ["box", "container"]
}
```

## Materials

### Upload Material

```http
POST /api/materials/{course_id}
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <binary>
title: "Chapter 1 Notes"
material_type: "pdf"
```

### List Materials

```http
GET /api/materials/{course_id}
Authorization: Bearer {token}
```

### Process Material

Triggers chunking and embedding:

```http
POST /api/materials/{material_id}/process
Authorization: Bearer {token}
```

### Map Chunks to Concept

```http
POST /api/materials/chunks/{chunk_id}/map
Authorization: Bearer {token}
Content-Type: application/json

{
  "concept_id": "uuid"
}
```

## Tutoring

### Start Session

```http
POST /api/tutor/session/{course_id}
Authorization: Bearer {token}
```

Response:
```json
{
  "session_id": "uuid",
  "course_id": "uuid",
  "started_at": "2024-01-15T10:30:00Z"
}
```

### Send Message (Streaming)

```http
POST /api/tutor/message/{course_id}
Authorization: Bearer {token}
Content-Type: application/json
Accept: text/event-stream

{
  "message": "Can you explain variables?"
}
```

Response (Server-Sent Events):
```
data: {"content": "Of course! "}
data: {"content": "Let me ask you "}
data: {"content": "a question first..."}
data: {"done": true, "mastery_update": {"concept": "variables", "previous": 0.3, "current": 0.35}}
```

### End Session

```http
POST /api/tutor/session/{session_id}/end
Authorization: Bearer {token}
```

## Students

### Enroll in Course

```http
POST /api/students/enroll
Authorization: Bearer {token}
Content-Type: application/json

{
  "enrollment_code": "ABC123"
}
```

### Get Progress

```http
GET /api/students/progress/{course_id}
Authorization: Bearer {token}
```

Response:
```json
{
  "course_id": "uuid",
  "overall_mastery": 0.65,
  "concepts": [
    {
      "id": "uuid",
      "name": "Variables",
      "mastery_level": 0.85,
      "attempts": 12
    }
  ]
}
```

### Get Session History

```http
GET /api/students/sessions/{course_id}?page=1&page_size=10
Authorization: Bearer {token}
```

## Assessment

### Get Mastery Report

```http
GET /api/assessment/mastery/{course_id}/{student_id}
Authorization: Bearer {token}
```

### Get Learning Trajectory

```http
GET /api/assessment/trajectory/{course_id}/{student_id}
Authorization: Bearer {token}
```

### Generate Verification Report

```http
POST /api/assessment/verification/{course_id}/{student_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "start_date": "2024-01-01",
  "end_date": "2024-03-01"
}
```

Response:
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "course_id": "uuid",
  "period_start": "2024-01-01",
  "period_end": "2024-03-01",
  "summary": {
    "total_sessions": 23,
    "total_time_minutes": 510,
    "concepts_mastered": 5,
    "gaming_flags": 0
  },
  "concept_details": [...],
  "recommendation": "Credit recommended"
}
```

## Analytics

### Class Overview

```http
GET /api/analytics/class/{course_id}?range=30d
Authorization: Bearer {token}
```

### Student Summary

```http
GET /api/analytics/student/{course_id}/{student_id}
Authorization: Bearer {token}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

Common status codes:
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (business logic error)
- `500` - Internal Server Error

## Rate Limiting

API requests are rate limited:
- Authentication endpoints: 10 requests/minute
- Tutor message endpoint: 30 requests/minute
- Other endpoints: 100 requests/minute

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```
