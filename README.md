# GhostX - Professional Email Management System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A modern, secure, and feature-rich email management system built with Flask and modern web technologies.

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
git clone https://github.com/yourusername/GhostX.git
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
- **Testing**: Pytest, Coverage
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