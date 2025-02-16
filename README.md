# GhostX - Modern Email Management System

GhostX is a secure, feature-rich email management system built with Flask and modern Python practices.

## ⚠️ Important: SMTP Requirements

To use GhostX, you need a spoofable SMTP server. Standard SMTP servers won't work due to security measures like SPF, DKIM, and DMARC.

### Recommended SMTP Provider
- Get a spoofable SMTP from trusted providers (e.g., https://spamir.fr/shop?prod=smtps)

### Email Security Overview
1. **SPF**: Defines which servers can send emails for a domain
2. **DKIM**: Adds digital signatures to verify sender authenticity
3. **DMARC**: Combines SPF and DKIM checks for enhanced security

### Spoofing Methods & Client Compatibility
1. **Punycode Method** (Gmail)
   - Using: coínbase.com
   - Best for: International domain variants

2. **Non-TLD Method** (All Clients)
   - Using: help@coinbase
   - Best for: Simple domain spoofing

3. **Alternative TLD** (Most Clients)
   - Using: service@coinbase.co
   - Works when domain is unregistered

4. **Subdirectory Method** (Gmail)
   - Using: support@coinbase.com/help
   - Best for: Complex domain structures

Client Support:
- Gmail: All methods
- iCloud: Non-TLD, Alt-TLD
- ProtonMail: Non-TLD, sometimes Alt-TLD
- Yahoo: Sometimes Alt-TLD

### Setup & Configuration
1. Configure SMTP in `.env`:
   ```
   SMTP_HOST=your_smtp_host
   SMTP_PORT=your_smtp_port
   SMTP_USER=your_smtp_username
   SMTP_PASS=your_smtp_password
   ```
2. Test configuration by sending a test email from the admin dashboard.

### Best Practices
- Secure credential storage
- Regular credential rotation
- Monitor sending patterns
- Space out sending intervals
- Verify domain formats

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

## 📫 Contact

- GitHub Issues: For bug reports and feature requests
- Discussions: For questions and community discussions
- Security: See our [Security Policy](SECURITY.md)

---

<div align="center">
Made with ❤️ by the GhostX Team
</div> 