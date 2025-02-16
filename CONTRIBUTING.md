# Contributing to GhostX

Thank you for your interest in contributing to GhostX! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. **Check Existing Issues** - Search the [issue tracker](https://github.com/xtial/GhostX/issues) to avoid duplicates.
2. **Create a New Issue** - Use our bug report template when creating new issues.
3. **Provide Details**:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, browser, etc.)
   - Screenshots if applicable

### Suggesting Enhancements

1. **Check Existing Suggestions** - Review open issues and discussions.
2. **Create a Feature Request** - Use our feature request template.
3. **Provide Context**:
   - Use case and benefits
   - Potential implementation approach
   - Considerations and challenges

### Pull Requests

1. **Fork the Repository**
2. **Create a Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```

3. **Make Changes**:
   - Follow the coding style guide
   - Add tests for new features
   - Update documentation as needed

4. **Commit Changes**:
   ```bash
   git add .
   git commit -m "type: brief description"
   ```
   Commit types:
   - feat: New feature
   - fix: Bug fix
   - docs: Documentation
   - style: Formatting
   - refactor: Code restructuring
   - test: Adding tests
   - chore: Maintenance

5. **Push Changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**:
   - Use the pull request template
   - Link related issues
   - Provide clear description

## Development Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/GhostX.git
   cd GhostX
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Database**:
   ```bash
   python create_db.py --remake
   ```

5. **Run Tests**:
   ```bash
   pytest
   ```

## Code Style Guide

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Comment complex logic
- Use type hints where appropriate

## Testing Guidelines

1. **Write Tests For**:
   - New features
   - Bug fixes
   - Edge cases
   - Error conditions

2. **Test Structure**:
   - Unit tests in `tests/unit/`
   - Integration tests in `tests/integration/`
   - Use descriptive test names
   - Follow AAA pattern (Arrange, Act, Assert)

3. **Run Tests**:
   ```bash
   pytest  # All tests
   pytest tests/unit/  # Unit tests only
   pytest -k "test_name"  # Specific test
   ```

## Documentation

1. **Code Documentation**:
   - Clear docstrings
   - Inline comments for complex logic
   - Type hints for function parameters

2. **Project Documentation**:
   - README.md updates
   - API documentation
   - Configuration guides
   - Deployment instructions

## Security Guidelines

1. **Security Considerations**:
   - No hardcoded credentials
   - Proper input validation
   - XSS prevention
   - CSRF protection
   - Secure session handling

2. **Reporting Security Issues**:
   - Do not create public issues
   - Follow responsible disclosure
   - Contact maintainers directly

## Review Process

1. **Code Review Checklist**:
   - Follows style guide
   - Includes tests
   - Documentation updated
   - No security issues
   - Performance considerations
   - Error handling

2. **Review Timeline**:
   - Initial review within 48 hours
   - Address feedback promptly
   - Final review and merge

## License Compliance

- All contributions must comply with the [LICENSE](LICENSE)
- Include copyright notices
- Document third-party code usage
- Maintain attribution requirements

## Questions and Support

- Use GitHub Discussions for questions
- Join our community channels
- Check documentation first
- Be respectful and patient

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to GhostX! 