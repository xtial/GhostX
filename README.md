# GhostX - Professional Email Management System

![GhostX Logo](static/favicon_io/favicon-32x32.png)

A modern, secure, and feature-rich email management system built with Flask and modern web technologies.

## 🚀 Features

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

## 🛠️ Technical Stack

- **Backend**: Python/Flask
- **Database**: SQLAlchemy with SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: Flask-Login, Flask-WTF
- **UI Components**: Font Awesome, Tippy.js
- **Editor**: Ace Editor
- **Styling**: Custom CSS with CSS Variables

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/GhostRelayX/ghostx.git
cd ghostx
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python create_db.py --remake
```

5. Start the application:
```bash
python run.py
```

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:
```env
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=sqlite:///spoofer.db
MAX_EMAILS_PER_HOUR=10
MAX_EMAILS_PER_DAY=50
```

## 🔧 Usage

### User Dashboard
- View email statistics
- Monitor sending limits
- Access email templates
- Create custom emails
- Track success rates

### Template Management
- Browse pre-built templates
- Create custom templates
- Save favorite templates
- Filter by categories
- Search functionality

### Account Management
- Update profile settings
- Monitor account activity
- View usage statistics
- Track email history

## 🔐 Security Recommendations

1. Always use strong passwords
2. Enable two-factor authentication when available
3. Monitor account activity regularly
4. Keep the application and dependencies updated
5. Review security logs periodically

## 📱 Mobile Support

The application is fully responsive and supports:
- Mobile phones
- Tablets
- Desktop browsers

## 🌐 Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Opera

## 🛡️ Rate Limiting

- Hourly email sending limits
- Daily email sending limits
- API rate limiting
- Login attempt limiting

## 🔄 Updates

The application checks for updates automatically. To manually update:

1. Pull the latest changes:
```bash
git pull origin main
```

2. Update dependencies:
```bash
pip install -r requirements.txt --upgrade
```

3. Update database:
```bash
python create_db.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Users are responsible for complying with applicable laws and regulations.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🐛 Bug Reports

Report bugs through the GitHub issues page. Include:
- Browser and version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable

## 📚 Documentation

Additional documentation available in the `/docs` folder:
- API Documentation
- Security Guidelines
- Development Guide
- Deployment Guide

## 🙏 Acknowledgments

- Font Awesome for icons
- Ace Editor for the code editor
- Flask community for the framework
- All contributors and testers

---

Made with ❤️ by the GhostX Team 