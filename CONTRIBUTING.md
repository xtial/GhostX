# Contributing to GhostX

First off, thank you for considering contributing to GhostX! It's people like you that make GhostX such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible
* Include error messages and stack traces

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed feature
* Explain why this enhancement would be useful
* List any alternative solutions you've considered
* Include mockups if applicable

### Pull Requests

* Fill in the required template
* Follow the Python style guide (Black formatting)
* Include appropriate tests
* Update documentation as needed
* End all files with a newline

## Development Process

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Set up your development environment:
   ```bash
   poetry install --with dev
   poetry run pre-commit install
   ```
4. Make your changes
5. Run tests and linting:
   ```bash
   poetry run pytest
   poetry run black .
   poetry run flake8
   poetry run mypy .
   poetry run bandit -r .
   ```
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Environment Setup

1. Install Python 3.13 or higher
2. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Clone your fork:
   ```bash
   git clone https://github.com/your-username/GhostX.git
   cd GhostX
   ```
4. Install dependencies:
   ```bash
   poetry install --with dev
   ```
5. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```
6. Create and configure your `.env` file:
   ```bash
   cp .env.template .env
   # Edit .env with your settings
   ```

## Style Guide

* Follow PEP 8 guidelines
* Use Black for code formatting
* Use type hints
* Write descriptive commit messages
* Document new functions and classes
* Update tests for new features

## Testing

* Write tests for new features
* Ensure all tests pass before submitting PR
* Include both unit and integration tests
* Test edge cases
* Update existing tests as needed

## Documentation

* Update README.md if needed
* Add docstrings to new functions
* Update API documentation
* Include examples for new features
* Update CHANGELOG.md

## Security

* Never commit sensitive data
* Use environment variables for secrets
* Follow security best practices
* Report security issues privately
* Review code for security implications

## Questions?

Feel free to contact the maintainers if you have any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License. 