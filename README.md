# Ghostx - Professional Email Management System

## Overview
Ghostx is a powerful email management system built with Flask, offering advanced features for email template management, campaign handling, and user administration.

## Features
- 🚀 Advanced Email Template Management
- 📊 Real-time Analytics Dashboard
- 👥 User Role Management
- 🔒 Rate Limiting & Quota Management
- 📈 Campaign Statistics
- 🎨 Modern, Responsive UI

## Tech Stack
- Backend: Python/Flask
- Database: SQLAlchemy
- Frontend: HTML5, CSS3, JavaScript
- Authentication: Flask-Login
- Task Processing: Custom Email Worker
- Rate Limiting: Flask-Limiter

## Installation

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Setup
1. Clone the repository:
```bash
git clone https://github.com/GhostRelayX/spoofer.git
cd ghostx
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
```

5. Edit `.env` with your configuration:
```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///spoofer.db
```

6. Initialize database:
```bash
python create_db.py
```

7. Run the application:
```bash
python run.py
```

## Project Structure
```
ghostx/
├── src/
│   ├── models/
│   ├── routes/
│   ├── tasks/
│   ├── utils/
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── templates/
├── tests/
├── .env
├── .gitignore
├── requirements.txt
└── run.py
```

## Configuration
The application can be configured using environment variables in the `.env` file:
- `FLASK_ENV`: development/production
- `FLASK_DEBUG`: True/False
- `SECRET_KEY`: Application secret key
- `DATABASE_URL`: Database connection string
- `SMTP_*`: SMTP server configuration
- `MAX_EMAILS_*`: Rate limiting configuration

## Development
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Testing
Run tests using:
```bash
python -m pytest
```

## Security
- CSRF Protection enabled
- Rate limiting implemented
- Password hashing using werkzeug
- Session management with Flask-Login
- Input validation and sanitization

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support
For support, please open an issue in the GitHub repository or contact the maintainers.

## Contributing
Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests. 