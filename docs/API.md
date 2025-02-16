# GhostX API Documentation

## Overview

The GhostX API provides programmatic access to email management functionality. This document describes the available endpoints, authentication methods, and example usage.

## Authentication

All API requests require authentication using a Bearer token:

```http
Authorization: Bearer <your_token>
```

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per user
- Email sending limits apply as per user tier

## API Endpoints

### Authentication

#### Login
```http
POST /api/login
```

Request body:
```json
{
    "username": "string",
    "password": "string"
}
```

Response:
```json
{
    "success": true,
    "token": "string",
    "user": {
        "id": "integer",
        "username": "string",
        "email_count": "integer",
        "is_admin": "boolean"
    }
}
```

#### Register
```http
POST /api/register
```

Request body:
```json
{
    "username": "string",
    "password": "string",
    "confirm_password": "string"
}
```

Response:
```json
{
    "success": true,
    "message": "string",
    "user": {
        "id": "integer",
        "username": "string"
    }
}
```

### Email Management

#### Get Templates
```http
GET /api/templates
```

Response:
```json
{
    "success": true,
    "templates": [
        {
            "id": "integer",
            "name": "string",
            "subject": "string",
            "html_content": "string"
        }
    ]
}
```

#### Get Template
```http
GET /api/templates/{template_id}
```

Response:
```json
{
    "success": true,
    "template": {
        "id": "integer",
        "name": "string",
        "subject": "string",
        "html_content": "string"
    }
}
```

#### Send Email
```http
POST /api/send-email
```

Request body:
```json
{
    "template_id": "integer",
    "recipient": "string",
    "subject": "string",
    "variables": {
        "key": "value"
    }
}
```

Response:
```json
{
    "success": true,
    "message": "string",
    "email_id": "string"
}
```

### User Management

#### Get User Limits
```http
GET /api/limits
```

Response:
```json
{
    "success": true,
    "email_count": "integer",
    "hourly_remaining": "integer",
    "daily_remaining": "integer"
}
```

### Admin Endpoints

#### Get System Status
```http
GET /api/admin/system-status
```

Response:
```json
{
    "success": true,
    "api_status": "string",
    "db_status": "string",
    "email_status": "string"
}
```

#### Get Active Sessions
```http
GET /api/admin/active-sessions
```

Response:
```json
{
    "success": true,
    "sessions": [
        {
            "id": "string",
            "username": "string",
            "ip": "string",
            "last_active": "string",
            "user_agent": "string"
        }
    ]
}
```

#### Get Security Metrics
```http
GET /api/admin/security-metrics
```

Response:
```json
{
    "success": true,
    "timestamps": ["string"],
    "login_attempts": ["integer"],
    "api_requests": ["integer"],
    "alerts": [
        {
            "id": "integer",
            "title": "string",
            "message": "string",
            "severity": "string",
            "timestamp": "string"
        }
    ]
}
```

## Error Handling

All endpoints return errors in a consistent format:

```json
{
    "success": false,
    "message": "string",
    "error_code": "string"
}
```

Common error codes:
- `auth_required`: Authentication required
- `invalid_credentials`: Invalid login credentials
- `rate_limited`: Rate limit exceeded
- `invalid_input`: Invalid request parameters
- `not_found`: Resource not found
- `permission_denied`: Insufficient permissions

## Websocket Events

The API supports real-time updates through WebSocket connections:

```javascript
const socket = new WebSocket('ws://localhost:5000/ws');

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle different event types
    switch(data.type) {
        case 'email_sent':
            // Handle email sent event
            break;
        case 'limit_updated':
            // Handle limit update event
            break;
    }
};
```

## Examples

### Python Example
```python
import requests

API_URL = 'http://localhost:5000'
TOKEN = 'your_token'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Send email using template
response = requests.post(
    f'{API_URL}/api/send-email',
    headers=headers,
    json={
        'template_id': 1,
        'recipient': 'recipient@domain.com',
        'subject': 'Test Email',
        'variables': {
            'user_name': 'John Doe',
            'verification_link': 'http://localhost:5000/verify'
        }
    }
)

print(response.json())
```

### JavaScript Example
```javascript
const API_URL = 'http://localhost:5000';
const TOKEN = 'your_token';

// Get user limits
async function getUserLimits() {
    const response = await fetch(`${API_URL}/api/limits`, {
        headers: {
            'Authorization': `Bearer ${TOKEN}`,
            'Content-Type': 'application/json'
        }
    });
    
    return response.json();
}

// Usage
getUserLimits()
    .then(data => console.log(data))
    .catch(error => console.error(error));
```

## Best Practices

1. **Rate Limiting**
   - Implement exponential backoff
   - Cache responses when appropriate
   - Monitor rate limit headers

2. **Error Handling**
   - Implement proper error handling
   - Log API errors appropriately
   - Display user-friendly error messages

3. **Security**
   - Store tokens securely
   - Use HTTPS for all requests
   - Validate server certificates
   - Implement token refresh logic

4. **Performance**
   - Minimize request frequency
   - Batch operations when possible
   - Use compression for large payloads

## Support

For API support:
- Discord: xtxry
- Documentation: http://localhost:5000/docs
- Status Page: http://localhost:5000/status 