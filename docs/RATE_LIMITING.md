# Rate Limiting Documentation

## Overview

GhostX implements a comprehensive rate limiting system to protect against abuse and ensure fair resource usage. This document details the rate limiting features and their configuration.

## Rate Limit Types

### 1. Registration Rate Limits

Controls new account creation attempts:

```python
REGISTRATION_LIMITS = {
    'hourly_per_ip': 3,        # Max registrations per hour from an IP
    'daily_per_ip': 5,         # Max registrations per day from an IP
    'monthly_per_ip': 10,      # Max successful registrations per month from an IP
    'daily_per_browser': 2     # Max accounts per browser fingerprint per day
}
```

### 2. API Rate Limits

Role-based API access limits:

```python
API_RATE_LIMITS = {
    'user': {
        'hourly': 20,
        'daily': 100,
        'concurrent': 2
    },
    'premium': {
        'hourly': 50,
        'daily': 200,
        'concurrent': 5
    },
    'admin': {
        'hourly': 1000,
        'daily': 5000,
        'concurrent': 10
    }
}
```

### 3. Authentication Rate Limits

Login attempt controls:

```python
AUTH_RATE_LIMITS = {
    'max_attempts': 5,         # Max failed attempts before lockout
    'lockout_duration': 900,   # Lockout duration in seconds (15 minutes)
    'attempt_window': 3600     # Time window for counting attempts (1 hour)
}
```

## Admin Controls

### Rate Limit Reset

Administrators can reset rate limits through:

1. Admin Dashboard UI:
   - Navigate to Security > Rate Limits
   - Use the "Reset All Rate Limits" button
   - Confirm the action

2. API Endpoint:
```http
POST /api/admin/rate-limits/reset
Authorization: Bearer <token>
X-CSRF-Token: <csrf_token>
```

### Monitoring

Monitor rate limit status through:

1. Real-time Dashboard:
   - Current usage statistics
   - Rate limit violations
   - User-specific quotas

2. API Endpoints:
```http
GET /api/admin/rate-limits/<user_id>
GET /api/admin/security/metrics
```

## Implementation Details

### Rate Limit Storage

1. **Redis Storage** (Primary):
   - Distributed rate limiting
   - Real-time counter updates
   - Automatic expiration

2. **Local Storage** (Fallback):
   - In-memory counters
   - Process-local tracking
   - Automatic cleanup

### Rate Limit Headers

API responses include rate limit headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635724800
```

### Error Responses

When limits are exceeded:

```json
{
    "success": false,
    "message": "Rate limit exceeded. Please try again later.",
    "retry_after": 3600
}
```

## Configuration

### Environment Variables

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
RATE_LIMIT_ENABLED=True
RATE_LIMIT_STRATEGY=fixed-window-elastic-expiry
```

### Custom Configuration

Create `rate_limit_config.py`:

```python
from src.config import Config

class RateLimitConfig(Config):
    CUSTOM_LIMITS = {
        'premium_plus': {
            'hourly': 100,
            'daily': 500,
            'concurrent': 10
        }
    }
```

## Best Practices

1. **Monitoring**
   - Regularly review rate limit logs
   - Monitor for abuse patterns
   - Adjust limits based on usage

2. **Reset Policy**
   - Document reset procedures
   - Maintain reset audit logs
   - Consider impact on users

3. **User Communication**
   - Clear limit documentation
   - Helpful error messages
   - Upgrade path information

## Troubleshooting

### Common Issues

1. **Redis Connection Failures**
   - Check Redis connection
   - Verify credentials
   - Ensure proper configuration

2. **Counter Desync**
   - Reset affected counters
   - Check for race conditions
   - Verify atomic operations

3. **Performance Impact**
   - Monitor Redis performance
   - Check network latency
   - Optimize counter storage

## API Reference

### Rate Limit Management

```python
from src.utils.rate_limiter import RateLimiter

# Check rate limit
success = rate_limiter.check_rate_limit(user_id)

# Get remaining quota
quota = rate_limiter.get_remaining_quota(user_id)

# Release concurrent limit
rate_limiter.release_concurrent_limit(user_id)
```

### Admin Operations

```python
# Reset all limits
success, message = RegistrationAttempt.reset_limits()

# Update user limits
success = rate_limiter.update_limits(user.role, hourly, daily, concurrent)
``` 