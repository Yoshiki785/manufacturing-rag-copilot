# Contributing

Thank you for your interest in contributing to Manufacturing RAG Copilot!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment:
   ```bash
   cp .env.example .env
   pip install -e ".[dev]"
   docker-compose up -d
   ```

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest`
4. Run linting: `ruff check . && ruff format .`
5. Commit with clear messages
6. Push and open a Pull Request

## Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public functions
- Maintain test coverage above 80%

## Pull Request Process

1. Update documentation for any new features
2. Add tests for new functionality
3. Ensure all CI checks pass
4. Request review from maintainers

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Check existing issues before creating new ones

## Code of Conduct

Be respectful and constructive in all interactions.
