# Changelog

All notable changes to GhostX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-03-XX

### Added
- Rate limiting functionality in admin dashboard
  - Added reset rate limits button in admin interface
  - Added visual feedback for rate limit operations
  - Implemented rate limit reset endpoint
- Enhanced security monitoring
  - Real-time rate limit status display
  - Improved error handling and user feedback
- New utility functions for notifications and API requests
- Dark mode support in admin interface

### Changed
- Reorganized admin dashboard JavaScript code
  - Moved shared functions to utils.js
  - Improved modular structure
- Enhanced admin interface styling
  - Updated notification system
  - Improved responsive design
  - Added new security card components
- Improved error handling across all admin endpoints

### Fixed
- Fixed duplicate `RegistrationAttempt` model definition
- Resolved CSRF token handling in admin API requests
- Fixed rate limit reset functionality
- Improved error messages and status updates

## [1.0.0] - Initial Release

### Features
- User authentication and authorization
- Admin dashboard
- Email template management
- Security monitoring
- User management
- Rate limiting

### Added
- Poetry package management integration
- Development and production server modes using Waitress
- Pre-commit hooks for code quality
- Comprehensive contributing guidelines
- Security enhancements for authentication
- Type hints throughout the codebase

### Changed
- Migrated to Poetry for dependency management
- Updated project structure for better organization
- Improved documentation and setup instructions
- Enhanced error handling and logging
- Modernized email template system

### Fixed
- Circular import issues with login_required decorator
- Package installation and dependency resolution
- Database creation and initialization process
- Security vulnerabilities in authentication system
- Static file serving in development mode

### Security
- Implemented proper session management
- Enhanced password hashing and verification
- Added rate limiting for API endpoints
- Improved CSRF protection
- Secure configuration handling

[Unreleased]: https://github.com/yourusername/GhostX/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/GhostX/releases/tag/v1.0.0 