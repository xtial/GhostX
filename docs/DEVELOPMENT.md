# GhostX Development Guide

## Project Overview

GhostX is a professional email management system built with Flask and modern web technologies. This guide will help you set up your development environment and understand the project structure.

## Technology Stack

- **Backend**
  - Python 3.11+
  - Flask (Web Framework)
  - SQLAlchemy (ORM)
  - Flask-Login (Authentication)
  - Flask-WTF (Forms and CSRF)
  - Bleach (Security)
  - Waitress (Production Server)

- **Frontend**
  - HTML5/CSS3
  - JavaScript (ES6+)
  - Font Awesome (Icons)
  - Custom CSS Framework

- **Database**
  - SQLite (Development)
  - PostgreSQL (Production)

## Project Structure

```
ghostx/
├── docs/                    # Documentation
├── src/                     # Source code
│   ├── models/             # Database models
│   ├── routes/             # Route handlers
│   ├── utils/              # Utility functions
│   └── __init__.py         # Application factory
├── static/                 # Static files
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── favicon_io/        # Favicon files
├── templates/             # HTML templates
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── .env.template         # Environment template
├── .gitignore           # Git ignore file
├── create_db.py         # Database initialization
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

## Development Setup

### Prerequisites

1. Python 3.11 or higher
2. Git
3. pip (Python package manager)
4. virtualenv or venv

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/GhostX.git
   cd GhostX
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```

5. **Initialize Database**
   ```bash
   python create_db.py --remake
   ```

6. **Run Development Server**
   ```bash
   python run.py
   ```

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Run Tests**
   ```bash
   pytest                 # All tests
   pytest tests/unit/    # Unit tests only
   pytest -k "test_name" # Specific test
   ```

3. **Code Formatting**
   ```bash
   black src/            # Format Python code
   flake8 src/          # Check style
   mypy src/            # Type checking
   ```

4. **Database Migrations**
   ```bash
   flask db migrate -m "migration message"
   flask db upgrade
   ```

## Code Style Guide

### Python

1. **Follow PEP 8**
   ```python
   # Good
   def calculate_total(items):
       return sum(item.price for item in items)

   # Bad
   def calculateTotal(items):
       return sum([item.price for item in items])
   ```

2. **Use Type Hints**
   ```python
   from typing import List, Optional

   def get_user(user_id: int) -> Optional[User]:
       return User.query.get(user_id)
   ```

3. **Write Docstrings**
   ```python
   def validate_email(email: str) -> bool:
       """
       Validate email format and domain.

       Args:
           email: String containing email address

       Returns:
           bool: True if email is valid, False otherwise
       """
       # Implementation
   ```

### JavaScript

1. **Use ES6+ Features**
   ```javascript
   // Good
   const getUser = async (userId) => {
       try {
           const response = await fetch(`/api/users/${userId}`);
           return response.json();
       } catch (error) {
           console.error('Error fetching user:', error);
           throw error;
       }
   };

   // Bad
   function getUser(userId) {
       return fetch('/api/users/' + userId)
           .then(function(response) {
               return response.json();
           })
           .catch(function(error) {
               console.error('Error fetching user:', error);
               throw error;
           });
   }
   ```

2. **Error Handling**
   ```javascript
   try {
       await sendEmail(templateId, recipient);
   } catch (error) {
       if (error instanceof RateLimitError) {
           showNotification('Rate limit exceeded');
       } else {
           logError(error);
       }
   }
   ```

## Testing

### Unit Tests

```python
def test_user_creation():
    """Test user creation with valid data."""
    user = User(
        username="testuser",
        email="user@domain.com"
    )
    user.set_password("password123")
    
    assert user.username == "testuser"
    assert user.check_password("password123")
```

### Integration Tests

```python
def test_login_endpoint(client):
    """Test login endpoint with valid credentials."""
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    assert response.json['success'] is True
```

## Debugging

1. **Flask Debug Mode**
   ```bash
   export FLASK_DEBUG=1  # Unix
   set FLASK_DEBUG=1     # Windows
   ```

2. **Logging**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   
   logger.debug("Debug message")
   logger.info("Info message")
   logger.error("Error message")
   ```

3. **Database Debugging**
   ```python
   # Enable SQLAlchemy logging
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

## Common Issues

1. **Database Migrations**
   - Issue: Migration conflicts
   - Solution: Delete migration files and recreate

2. **Environment Variables**
   - Issue: Missing configuration
   - Solution: Check .env file against template

3. **Dependencies**
   - Issue: Version conflicts
   - Solution: Use `pip freeze > requirements.txt`

## Performance Optimization

1. **Database Queries**
   ```python
   # Good - Eager loading
   users = User.query.options(
       joinedload(User.posts)
   ).all()

   # Bad - N+1 problem
   users = User.query.all()
   for user in users:
       print(user.posts)  # Separate query for each user
   ```

2. **Caching**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def get_user_stats(user_id: int) -> dict:
       # Expensive computation
       return stats
   ```

## Security Best Practices

1. **Input Validation**
   ```python
   from src.utils import sanitize_input

   @app.route('/api/message', methods=['POST'])
   def create_message():
       content = sanitize_input(request.json.get('content'))
       # Process sanitized content
   ```

2. **CSRF Protection**
   ```python
   from flask_wtf.csrf import CSRFProtect

   csrf = CSRFProtect()
   csrf.init_app(app)
   ```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## Support

For development support:
- Discord: xtxry
- Documentation: http://localhost:5000/docs