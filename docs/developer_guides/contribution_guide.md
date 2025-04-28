# AccountDB Contribution Guide

## Introduction

Thank you for your interest in contributing to the AccountDB project! This guide will help you understand how to contribute to the project, including coding standards, pull request process, and best practices.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Code Review Process](#code-review-process)
9. [Issue Tracking](#issue-tracking)
10. [Release Process](#release-process)

## Code of Conduct

We expect all contributors to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

Before you start contributing, make sure you have set up your development environment. See the [Development Setup Guide](development_setup.md) for instructions.

### Finding Issues to Work On

1. Check the [Issues](https://github.com/your-organization/accountdb/issues) page for open issues.
2. Look for issues labeled with `good first issue` or `help wanted`.
3. Comment on the issue to let others know you're working on it.

## Development Workflow

### Git Workflow

We follow a feature branch workflow:

1. Fork the repository (if you're an external contributor).
2. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/your-bug-fix
   ```
3. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Add your feature"
   ```
4. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Create a pull request to the main repository.

### Branch Naming Convention

- `feature/your-feature-name`: For new features
- `fix/your-bug-fix`: For bug fixes
- `docs/your-documentation`: For documentation changes
- `refactor/your-refactoring`: For code refactoring
- `test/your-test`: For adding or updating tests

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `perf`: Code changes that improve performance
- `test`: Adding or updating tests
- `chore`: Changes to the build process or auxiliary tools

Example:
```
feat(accounts): add pagination to accounts list endpoint

- Add limit and offset parameters
- Add total count to response
- Add pagination links to response

Closes #123
```

## Coding Standards

### Python Code Style

We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use the following tools to enforce code style:

- **Black**: Code formatter
- **isort**: Import sorter
- **flake8**: Linter

To format your code:

```bash
black .
isort .
```

To check your code:

```bash
flake8 .
```

### SQL Code Style

- Use UPPER CASE for SQL keywords.
- Use snake_case for table and column names.
- Use indentation to make SQL queries more readable.
- Use meaningful names for tables and columns.

Example:
```sql
SELECT
    acc_id,
    acc_username,
    acc_email_address
FROM
    accounts
WHERE
    prime = TRUE
ORDER BY
    acc_created_at DESC
LIMIT 10;
```

### Type Hints

We use type hints for all Python code. This helps with code readability and enables better IDE support.

Example:
```python
def get_account(acc_id: str) -> Dict[str, Any]:
    """
    Get an account by ID.
    
    Args:
        acc_id: The account ID
        
    Returns:
        The account details
    """
    # ...
```

### Docstrings

We use Google-style docstrings for all Python code.

Example:
```python
def get_account(acc_id: str) -> Dict[str, Any]:
    """
    Get an account by ID.
    
    Args:
        acc_id: The account ID
        
    Returns:
        The account details
        
    Raises:
        HTTPException: If the account is not found
    """
    # ...
```

## Testing

### Writing Tests

We use pytest for testing. All code should be covered by tests. We aim for at least 80% code coverage.

Tests should be placed in the `tests` directory, following the same structure as the code being tested.

Example:
```python
def test_get_account():
    """Test getting an account by ID."""
    # Arrange
    acc_id = "76561199123456789"
    
    # Act
    account = get_account(acc_id)
    
    # Assert
    assert account["acc_id"] == acc_id
    assert "acc_username" in account
    assert "acc_email_address" in account
```

### Running Tests

To run the tests:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=.
```

### Test Coverage

We use pytest-cov to measure test coverage. We aim for at least 80% code coverage.

To generate a coverage report:

```bash
pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

## Documentation

### Code Documentation

All code should be documented with docstrings. We use Google-style docstrings for all Python code.

Example:
```python
def get_account(acc_id: str) -> Dict[str, Any]:
    """
    Get an account by ID.
    
    Args:
        acc_id: The account ID
        
    Returns:
        The account details
        
    Raises:
        HTTPException: If the account is not found
    """
    # ...
```

### API Documentation

All API endpoints should be documented with FastAPI's docstring-based documentation.

Example:
```python
@router.get("/{acc_id}", response_model=AccountResponse)
async def get_account(
    acc_id: str = Path(..., description="The account ID"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get an account by ID.
    
    This endpoint returns the details of a specific account.
    
    Regular users can only access their own accounts, while administrators can access any account.
    
    Args:
        acc_id: The account ID
        current_user: The current authenticated user
        
    Returns:
        The account details
        
    Raises:
        HTTPException: If the account is not found or the user doesn't have permission to access it
    """
    # ...
```

### Project Documentation

Project documentation should be written in Markdown and placed in the `docs` directory. Documentation should be clear, concise, and up-to-date.

## Pull Request Process

1. Make sure your code follows the coding standards.
2. Make sure all tests pass.
3. Update the documentation if necessary.
4. Create a pull request to the main repository.
5. Fill out the pull request template.
6. Wait for a code review.
7. Address any feedback from the code review.
8. Once approved, your pull request will be merged.

### Pull Request Template

```markdown
## Description

[Describe the changes you've made]

## Related Issues

[Link to any related issues]

## Checklist

- [ ] I have followed the coding standards
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] I have updated the documentation accordingly
- [ ] I have added type hints for all functions and classes
- [ ] I have added docstrings for all functions and classes
```

## Code Review Process

All pull requests will be reviewed by at least one maintainer. The reviewer will check:

1. Code quality and style
2. Test coverage
3. Documentation
4. Performance and security implications

The reviewer may request changes or ask questions. Please address all feedback promptly.

## Issue Tracking

We use GitHub Issues for tracking issues. When creating an issue, please use the appropriate template:

- Bug Report
- Feature Request
- Documentation Request

### Bug Report Template

```markdown
## Description

[Describe the bug]

## Steps to Reproduce

1. [First step]
2. [Second step]
3. [And so on...]

## Expected Behavior

[What you expected to happen]

## Actual Behavior

[What actually happened]

## Environment

- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.5]
- AccountDB version: [e.g., 1.0.0]
```

### Feature Request Template

```markdown
## Description

[Describe the feature you'd like to see]

## Use Case

[Describe how this feature would be used]

## Alternatives

[Describe any alternative solutions or features you've considered]
```

### Documentation Request Template

```markdown
## Description

[Describe the documentation you'd like to see]

## Current Documentation

[Describe the current documentation, if any]

## Proposed Documentation

[Describe the proposed documentation]
```

## Release Process

We follow [Semantic Versioning](https://semver.org/) for releases.

1. Update the version number in `backend/config.py`.
2. Update the CHANGELOG.md file.
3. Create a new release on GitHub.
4. Tag the release with the version number.
5. Publish the release.

### Version Numbers

- MAJOR version when you make incompatible API changes,
- MINOR version when you add functionality in a backwards compatible manner, and
- PATCH version when you make backwards compatible bug fixes.

### CHANGELOG Format

```markdown
# Changelog

## [1.0.0] - 2023-01-01

### Added
- Feature 1
- Feature 2

### Changed
- Change 1
- Change 2

### Fixed
- Bug fix 1
- Bug fix 2

### Removed
- Removed feature 1
- Removed feature 2
```

## Conclusion

Thank you for contributing to the AccountDB project! Your contributions help make the project better for everyone. If you have any questions, please don't hesitate to ask.
