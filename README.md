# GhostX - Modern Email Management System

GhostX is a secure, feature-rich email management system built with Flask and modern Python practices.

## Features

- 🔒 Secure Authentication System
- 📧 Email Template Management
- 📊 Campaign Analytics
- 🔄 Rate Limiting
- 👥 User Role Management
- 📈 Real-time Statistics
- 🛡️ Security Logging
- 🌐 API Access Control

## Requirements

- Python 3.13+
- Poetry (Python package manager)
- SQLite/PostgreSQL
- Redis (optional, for rate limiting)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/xtial/GhostX.git
cd GhostX
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up the database:
```bash
poetry run python create_db.py
```

4. Run the application:
```bash
poetry run python run.py
```

5. Access the application at `http://localhost:5000`

## Configuration

1. Copy `.env.template` to `.env`:
```bash
cp .env.template .env
```

2. Update the `.env` file with your settings:
```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///spoofer.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## Development Setup

1. Install development dependencies:
```bash
poetry install --with dev
```

2. Set up pre-commit hooks:
```bash
poetry run pre-commit install
```

## Project Structure

```
GhostX/
├── src/                    # Application source code
│   ├── models/            # Database models
│   ├── routes/            # Route handlers
│   ├── utils/             # Utility functions
│   ├── database/          # Database configuration
│   └── templates/         # HTML templates
├── static/                # Static files (CSS, JS)
├── tests/                 # Test suite
├── logs/                  # Application logs
└── docs/                  # Documentation
```

## Recent Changes

### Version 1.0.0 (2025-02-16)

#### Major Updates
- Added support for Python 3.13
- Implemented Flask-Limiter for rate limiting
- Enhanced security with improved session management
- Added comprehensive logging system

#### Dependencies
- Updated Flask to 3.0.0
- Updated SQLAlchemy to 2.0.23
- Added Flask-Session for better session handling
- Added Waitress for production WSGI server

#### Bug Fixes
- Fixed circular import issues in database models
- Resolved user authentication state management
- Fixed dashboard access control
- Corrected template loading issues

## API Documentation

The API documentation is available at `/docs` when running in development mode.

### Key Endpoints

- `/api/templates` - Template management
- `/api/campaigns` - Campaign operations
- `/api/admin/*` - Administrative functions
- `/api/limits` - Rate limit information

## Security Features

- Password hashing with bcrypt
- Rate limiting per user/IP
- CSRF protection
- Session security
- SQL injection prevention
- XSS protection
- Security logging

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers at xtial@github.com.

## Acknowledgments

- Flask team for the amazing framework
- SQLAlchemy team for the robust ORM
- All contributors who have helped shape this project

## 🌟 Features

### 📧 Email Management
- Custom email template creation and management
- Real-time email tracking and analytics
- Hourly and daily sending limits
- Success rate monitoring
- Template categorization and filtering

### 🎨 User Interface
- Modern, responsive design
- Dark/Light theme toggle
- Real-time statistics dashboard
- Interactive template editor
- Mobile-friendly interface

### 🔒 Security Features
- Secure user authentication
- Session management
- Rate limiting
- CSRF protection
- Password strength validation
- Secure password hashing
- IP tracking and monitoring

### 📊 Analytics
- Email success rates
- Sending statistics
- Usage tracking
- Real-time monitoring
- Performance metrics

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/xtial/GhostX.git
cd GhostX
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies with Poetry:
```bash
pip install poetry
poetry install
```

4. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with your settings
```

5. Initialize the database:
```bash
poetry run python create_db.py --remake
```

6. Start the application:
```bash
poetry run python run.py
```

## 📖 Documentation

- [API Documentation](docs/API.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

## 🛠️ Tech Stack

- **Backend**: Python/Flask
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: Flask-Login, Flask-WTF
- **UI**: Font Awesome, Custom CSS Framework
- **Code Quality**: Black, Flake8, MyPy
- **Security Scanning**: Bandit, Safety

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License with additional terms - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) for the web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for the ORM
- [Font Awesome](https://fontawesome.com/) for icons
- All our [contributors](CONTRIBUTORS.md)

## 📫 Contact

- GitHub Issues: For bug reports and feature requests
- Discussions: For questions and community discussions
- Security: See our [Security Policy](SECURITY.md)

---

<div align="center">
Made with ❤️ by the GhostX Team
</div> 