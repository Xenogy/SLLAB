# Developer Guide

## Introduction

This guide is intended for developers who want to contribute to the AccountDB project. It provides information about the project structure, development environment setup, coding standards, and development workflow.

## Project Structure

The AccountDB project has the following structure:

```
accountdb/
├── backend/                 # Backend code
│   ├── config.py            # Configuration
│   ├── db/                  # Database code
│   │   ├── connection.py    # Database connection management
│   │   └── user_connection.py # User-specific database connection
│   ├── dependencies.py      # FastAPI dependencies
│   ├── error_handling/      # Error handling code
│   │   ├── exceptions.py    # Exception classes
│   │   ├── handlers.py      # Error handlers
│   │   ├── middleware.py    # Error handling middleware
│   │   ├── recovery.py      # Error recovery mechanisms
│   │   └── reporting.py     # Error reporting
│   ├── main.py              # Main application
│   ├── requirements.txt     # Python dependencies
│   ├── routers/             # API routers
│   │   ├── accounts.py      # Accounts router
│   │   ├── auth.py          # Authentication router
│   │   ├── cards.py         # Cards router
│   │   ├── hardware.py      # Hardware router
│   │   ├── steam_auth.py    # Steam authentication router
│   │   ├── account_status.py # Account status router
│   │   └── upload.py        # Upload router
│   ├── sql/                 # SQL initialization scripts
│   ├── tests/               # Tests
│   │   ├── conftest.py      # Test configuration
│   │   ├── fixtures/        # Test fixtures
│   │   ├── integration/     # Integration tests
│   │   ├── unit/            # Unit tests
│   │   └── utils/           # Test utilities
│   └── utils/               # Utility functions
│       ├── config_utils.py  # Configuration utilities
│       ├── crypto_utils.py  # Cryptography utilities
│       ├── date_utils.py    # Date utilities
│       ├── db_utils.py      # Database utilities
│       ├── error_utils.py   # Error utilities
│       ├── file_utils.py    # File utilities
│       ├── http_utils.py    # HTTP utilities
│       ├── json_utils.py    # JSON utilities
│       ├── logging_utils.py # Logging utilities
│       ├── string_utils.py  # String utilities
│       └── validation_utils.py # Validation utilities
├── docs/                    # Documentation
│   ├── api/                 # API documentation
│   ├── architecture/        # Architecture documentation
│   ├── database/            # Database documentation
│   └── guides/              # Guides
└── README.md                # Project README
```

## Development Environment Setup

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher
- Git

### Setup Steps

1. Clone the repository:

```bash
git clone https://github.com/your-username/accountdb.git
cd accountdb
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

4. Create a PostgreSQL database:

```bash
createdb accountdb
```

5. Initialize the database:

```bash
cd backend
python -c "from db.connection import init_db; init_db()"
```

6. Run the application:

```bash
uvicorn main:app --reload
```

The application will be available at http://localhost:8000.

## Coding Standards

### Python Code Style

- Follow PEP 8 for Python code style.
- Use 4 spaces for indentation.
- Use snake_case for variable and function names.
- Use CamelCase for class names.
- Use UPPER_CASE for constants.
- Use docstrings for all functions, classes, and modules.
- Use type hints for function parameters and return values.

### SQL Code Style

- Use UPPER CASE for SQL keywords.
- Use snake_case for table and column names.
- Use indentation to make SQL queries more readable.
- Use meaningful names for tables and columns.

### Git Commit Messages

- Use the imperative mood in the subject line.
- Limit the subject line to 50 characters.
- Capitalize the subject line.
- Do not end the subject line with a period.
- Separate the subject from the body with a blank line.
- Wrap the body at 72 characters.
- Use the body to explain what and why, not how.

## Development Workflow

### Feature Development

1. Create a new branch for your feature:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes.

3. Write tests for your changes.

4. Run the tests:

```bash
cd backend
pytest
```

5. Commit your changes:

```bash
git add .
git commit -m "Add your feature"
```

6. Push your changes:

```bash
git push origin feature/your-feature-name
```

7. Create a pull request.

### Bug Fixes

1. Create a new branch for your bug fix:

```bash
git checkout -b fix/your-bug-fix
```

2. Make your changes.

3. Write tests to verify the bug fix.

4. Run the tests:

```bash
cd backend
pytest
```

5. Commit your changes:

```bash
git add .
git commit -m "Fix your bug"
```

6. Push your changes:

```bash
git push origin fix/your-bug-fix
```

7. Create a pull request.

## Testing

### Running Tests

To run all tests:

```bash
cd backend
pytest
```

To run unit tests only:

```bash
cd backend
pytest -m unit
```

To run integration tests only:

```bash
cd backend
pytest -m integration
```

To run tests with coverage:

```bash
cd backend
pytest --cov=.
```

### Writing Tests

- Write unit tests for all functions and classes.
- Write integration tests for API endpoints.
- Use pytest fixtures for test setup and teardown.
- Use pytest markers to categorize tests.
- Use pytest parametrize for testing multiple inputs.
- Use pytest monkeypatch for mocking dependencies.

## Documentation

### API Documentation

The API is documented using OpenAPI. The OpenAPI documentation is available at:

```
http://localhost:8000/api/docs
```

The ReDoc documentation is available at:

```
http://localhost:8000/api/redoc
```

### Code Documentation

- Use docstrings for all functions, classes, and modules.
- Use type hints for function parameters and return values.
- Use comments to explain complex code.

### Architecture Documentation

The architecture documentation is available in the `docs/architecture` directory.

### Database Documentation

The database documentation is available in the `docs/database` directory.

## Deployment

### Prerequisites

- Docker
- Docker Compose

### Deployment Steps

1. Build the Docker image:

```bash
docker build -t accountdb .
```

2. Run the Docker container:

```bash
docker run -p 8000:8000 accountdb
```

The application will be available at http://localhost:8000.

### Docker Compose

You can also use Docker Compose to run the application and its dependencies:

```bash
docker-compose up
```

The application will be available at http://localhost:8000.

## Troubleshooting

### Common Issues

#### Database Connection Issues

If you encounter database connection issues, check the following:

- Make sure the PostgreSQL server is running.
- Check the database connection parameters in the configuration.
- Make sure the database exists.
- Make sure the database user has the necessary permissions.

#### API Errors

If you encounter API errors, check the following:

- Check the API request parameters.
- Check the API request headers.
- Check the API request body.
- Check the API response status code.
- Check the API response body.

#### Authentication Issues

If you encounter authentication issues, check the following:

- Make sure you are using a valid JWT token.
- Make sure the token has not expired.
- Make sure the token has the necessary permissions.

## Conclusion

This guide provides information about the AccountDB project structure, development environment setup, coding standards, and development workflow. If you have any questions or need further assistance, please contact the project maintainers.
