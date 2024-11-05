# API Documentation

## Overview

The Movie Recommendation System API provides endpoints for user management, movie recommendations, and feedback collection. Built with FastAPI, it offers real-time recommendations and performance monitoring.

## Base URL

```
http://localhost:8000
```

## Authentication

### JWT Token Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

### Authentication Endpoints

#### 1. Register User

```http
POST /register
Content-Type: application/json

{
    "username": "string",
    "email": "string",
    "password": "string"
}
```

Response:
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

#### 2. Login

```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=string&password=string
```

Response:
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

## Recommendation Endpoints

### 1. Get Recommendations

```http
GET /recommendations/{user_id}
Authorization: Bearer <token>
```

Query Parameters:
- `n_recommendations` (optional): Number of recommendations to return (default: 10)

Response:
```json
{
    "recommendations": [
        {
            "movieId": "integer",
            "title": "string",
            "genres": "string",
            "score": "float"
        }
    ]
}
```

### 2. Get Similar Movies

```http
GET /similar_movies/{movie_id}
Authorization: Bearer <token>
```

Response:
```json
{
    "similar_movies": [
        {
            "movieId": "integer",
            "title": "string",
            "genres": "string",
            "similarity": "float"
        }
    ]
}
```

## Feedback Endpoints

### 1. Submit Feedback

```http
POST /feedback
Authorization: Bearer <token>
Content-Type: application/json

{
    "movie_id": "integer",
    "rating": "float"
}
```

Response:
```json
{
    "message": "Feedback submitted successfully"
}
```

### 2. Get User Feedback

```http
GET /feedback/{user_id}
Authorization: Bearer <token>
```

Response:
```json
{
    "feedback": [
        {
            "movie_id": "integer",
            "rating": "float",
            "timestamp": "string"
        }
    ]
}
```

## Movie Information Endpoints

### 1. Get Movie Details

```http
GET /movies/{movie_id}
Authorization: Bearer <token>
```

Response:
```json
{
    "movieId": "integer",
    "title": "string",
    "genres": "string",
    "year": "integer",
    "average_rating": "float",
    "rating_count": "integer"
}
```

### 2. Search Movies

```http
GET /movies/search
Authorization: Bearer <token>
```

Query Parameters:
- `query`: Search term
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 10)

Response:
```json
{
    "results": [
        {
            "movieId": "integer",
            "title": "string",
            "genres": "string"
        }
    ],
    "total": "integer",
    "page": "integer",
    "pages": "integer"
}
```

## User Profile Endpoints

### 1. Get User Profile

```http
GET /users/me
Authorization: Bearer <token>
```

Response:
```json
{
    "id": "integer",
    "username": "string",
    "email": "string",
    "preferences": {
        "favorite_genres": ["string"],
        "rating_count": "integer",
        "average_rating": "float"
    }
}
```

### 2. Update User Preferences

```http
PUT /users/me/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
    "favorite_genres": ["string"],
    "exclude_genres": ["string"]
}
```

Response:
```json
{
    "message": "Preferences updated successfully"
}
```

## Error Responses

### 401 Unauthorized
```json
{
    "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
    "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
    "detail": [
        {
            "loc": ["string"],
            "msg": "string",
            "type": "string"
        }
    ]
}
```

## Rate Limiting

- Rate limit: 100 requests per minute per user
- Rate limit headers included in response:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Monitoring

The API exposes Prometheus metrics at `/metrics`:

- Request latency
- Request count by endpoint
- Error count by type
- Active user count
- Recommendation quality metrics

## WebSocket Endpoints

### Real-time Recommendations

```websocket
ws://localhost:8000/ws/recommendations/{user_id}
```

Message format:
```json
{
    "type": "recommendation",
    "data": {
        "movieId": "integer",
        "title": "string",
        "score": "float"
    }
}
```

## Best Practices

1. **Authentication**
   - Store JWT tokens securely
   - Refresh tokens before expiration
   - Use HTTPS in production

2. **Error Handling**
   - Always check response status codes
   - Implement proper error handling
   - Log failed requests

3. **Performance**
   - Use connection pooling
   - Implement request caching
   - Monitor API usage

4. **Rate Limiting**
   - Implement exponential backoff
   - Cache responses when appropriate
   - Monitor rate limit headers 