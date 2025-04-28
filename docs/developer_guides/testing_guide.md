# AccountDB Testing Guide

## Introduction

This guide provides detailed information about testing the AccountDB system. It covers unit testing, integration testing, end-to-end testing, and performance testing. Following these guidelines ensures that the codebase remains reliable, maintainable, and high-quality.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Testing Tools](#testing-tools)
3. [Test Types](#test-types)
4. [Writing Tests](#writing-tests)
5. [Running Tests](#running-tests)
6. [Test Coverage](#test-coverage)
7. [Mocking](#mocking)
8. [Test Data](#test-data)
9. [Continuous Integration](#continuous-integration)
10. [Performance Testing](#performance-testing)
11. [Security Testing](#security-testing)
12. [Troubleshooting](#troubleshooting)

## Testing Philosophy

### Why We Test

- **Prevent Regressions**: Tests help ensure that new changes don't break existing functionality.
- **Document Behavior**: Tests serve as documentation for how the code should behave.
- **Improve Design**: Writing tests often leads to better code design.
- **Enable Refactoring**: Tests provide confidence when refactoring code.
- **Facilitate Collaboration**: Tests help team members understand how the code works.

### Testing Principles

1. **Test Early, Test Often**: Write tests as you write code, not after.
2. **Test Behavior, Not Implementation**: Focus on what the code does, not how it does it.
3. **Keep Tests Simple**: Tests should be easy to understand and maintain.
4. **Make Tests Independent**: Tests should not depend on each other.
5. **Test Edge Cases**: Test boundary conditions and error cases.
6. **Test One Thing at a Time**: Each test should test a single aspect of the code.
7. **Use Descriptive Test Names**: Test names should describe what is being tested.

## Testing Tools

### Primary Testing Tools

- **pytest**: The main testing framework for Python code.
- **pytest-cov**: Plugin for measuring test coverage.
- **pytest-asyncio**: Plugin for testing asynchronous code.
- **pytest-mock**: Plugin for mocking dependencies.
- **pytest-xdist**: Plugin for running tests in parallel.

### Additional Testing Tools

- **hypothesis**: Property-based testing framework.
- **locust**: Load testing tool.
- **bandit**: Security testing tool.
- **safety**: Dependency vulnerability scanner.

### Installation

```bash
pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist hypothesis locust bandit safety
```

## Test Types

### Unit Tests

Unit tests test individual components in isolation. They should be fast, focused, and independent.

Example:
```python
def test_calculate_total():
    """Test calculating the total price of items."""
    # Arrange
    items = [
        {"price": 10.0, "quantity": 2},
        {"price": 5.0, "quantity": 3}
    ]
    
    # Act
    total = calculate_total(items)
    
    # Assert
    assert total == 35.0
```

### Integration Tests

Integration tests test how components work together. They test the integration points between components.

Example:
```python
def test_create_account_with_hardware():
    """Test creating an account with a hardware profile."""
    # Arrange
    account_data = {
        "acc_id": "76561199123456789",
        "acc_username": "testuser",
        "acc_password": "password123",
        "acc_email_address": "test@example.com",
        "acc_email_password": "emailpass123"
    }
    
    hardware_data = {
        "hw_id": "hw_id_1",
        "hw_name": "Hardware 1",
        "hw_type": "Type 1"
    }
    
    # Act
    account = create_account(account_data)
    hardware = create_hardware(account["acc_id"], hardware_data)
    
    # Assert
    assert account["acc_id"] == account_data["acc_id"]
    assert hardware["acc_id"] == account["acc_id"]
    assert hardware["hw_id"] == hardware_data["hw_id"]
```

### End-to-End Tests

End-to-end tests test the entire system from the user's perspective. They test the system as a whole.

Example:
```python
def test_create_account_api():
    """Test creating an account through the API."""
    # Arrange
    client = TestClient(app)
    account_data = {
        "acc_id": "76561199123456789",
        "acc_username": "testuser",
        "acc_password": "password123",
        "acc_email_address": "test@example.com",
        "acc_email_password": "emailpass123"
    }
    
    # Act
    response = client.post(
        "/accounts",
        json=account_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Assert
    assert response.status_code == 201
    assert response.json()["acc_id"] == account_data["acc_id"]
```

### Performance Tests

Performance tests test the performance characteristics of the system. They test how the system performs under load.

Example:
```python
def test_list_accounts_performance():
    """Test the performance of listing accounts."""
    # Arrange
    client = TestClient(app)
    
    # Create 1000 accounts
    for i in range(1000):
        create_test_account(f"testuser{i}")
    
    # Act
    start_time = time.time()
    response = client.get(
        "/accounts/list?limit=100&offset=0",
        headers={"Authorization": f"Bearer {token}"}
    )
    end_time = time.time()
    
    # Assert
    assert response.status_code == 200
    assert len(response.json()["accounts"]) == 100
    assert end_time - start_time < 0.5  # Response time should be less than 500ms
```

## Writing Tests

### Test Structure

We use the Arrange-Act-Assert pattern for tests:

1. **Arrange**: Set up the test data and environment.
2. **Act**: Perform the action being tested.
3. **Assert**: Verify the expected outcome.

Example:
```python
def test_get_account():
    """Test getting an account by ID."""
    # Arrange
    acc_id = "76561199123456789"
    create_test_account(acc_id)
    
    # Act
    account = get_account(acc_id)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == acc_id
```

### Test Naming

Test names should be descriptive and follow the pattern `test_<function_name>_<scenario>_<expected_outcome>`.

Examples:
- `test_get_account_existing_returns_account`
- `test_get_account_nonexistent_returns_none`
- `test_create_account_valid_data_creates_account`
- `test_create_account_invalid_data_raises_error`

### Test Organization

Tests should be organized in the same structure as the code being tested. For example, if you have a module `accounts.py`, you should have a test module `test_accounts.py`.

Example:
```
backend/
├── accounts.py
├── tests/
│   ├── test_accounts.py
│   └── ...
└── ...
```

### Parameterized Tests

Use parameterized tests to test multiple inputs with the same test function.

Example:
```python
@pytest.mark.parametrize("items,expected", [
    ([{"price": 10.0, "quantity": 2}, {"price": 5.0, "quantity": 3}], 35.0),
    ([{"price": 10.0, "quantity": 1}], 10.0),
    ([], 0.0)
])
def test_calculate_total(items, expected):
    """Test calculating the total price of items."""
    assert calculate_total(items) == expected
```

### Testing Exceptions

Use `pytest.raises` to test that a function raises an exception.

Example:
```python
def test_get_account_invalid_id_raises_error():
    """Test that get_account raises an error for an invalid ID."""
    with pytest.raises(ValueError):
        get_account("invalid_id")
```

### Testing Asynchronous Code

Use `pytest.mark.asyncio` to test asynchronous code.

Example:
```python
@pytest.mark.asyncio
async def test_get_account_async():
    """Test getting an account asynchronously."""
    # Arrange
    acc_id = "76561199123456789"
    await create_test_account_async(acc_id)
    
    # Act
    account = await get_account_async(acc_id)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == acc_id
```

## Running Tests

### Running All Tests

```bash
pytest
```

### Running Specific Tests

```bash
# Run tests in a specific file
pytest tests/test_accounts.py

# Run a specific test
pytest tests/test_accounts.py::test_get_account

# Run tests matching a pattern
pytest -k "account"
```

### Running Tests with Coverage

```bash
pytest --cov=.
```

### Running Tests in Parallel

```bash
pytest -xvs -n auto
```

### Running Tests with Verbose Output

```bash
pytest -v
```

### Running Tests with Debug Output

```bash
pytest --log-cli-level=DEBUG
```

## Test Coverage

### Measuring Coverage

We use pytest-cov to measure test coverage. We aim for at least 80% code coverage.

```bash
pytest --cov=. --cov-report=term --cov-report=html
```

This will generate a coverage report in the terminal and an HTML report in the `htmlcov` directory.

### Coverage Thresholds

We enforce minimum coverage thresholds:

```bash
pytest --cov=. --cov-fail-under=80
```

This will fail the tests if the coverage is below 80%.

### Ignoring Code in Coverage

Use the `# pragma: no cover` comment to exclude code from coverage.

Example:
```python
def debug_function():
    """This function is only used for debugging."""
    # pragma: no cover
    print("Debug information")
```

## Mocking

### When to Mock

- Mock external dependencies (e.g., databases, APIs).
- Mock slow or complex components.
- Mock components that are not yet implemented.
- Mock components that are difficult to set up for testing.

### How to Mock

We use `pytest-mock` for mocking.

Example:
```python
def test_get_account_with_mock(mocker):
    """Test getting an account with a mock database."""
    # Arrange
    acc_id = "76561199123456789"
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = (acc_id, "username", "email@example.com")
    mock_cursor.description = [("acc_id",), ("acc_username",), ("acc_email_address",)]
    
    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    mocker.patch("db.get_db_connection", return_value=mock_conn)
    
    # Act
    account = get_account(acc_id)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == acc_id
    assert account["acc_username"] == "username"
    assert account["acc_email_address"] == "email@example.com"
```

### Mocking Context Managers

Use `mocker.patch` with a context manager to mock context managers.

Example:
```python
def test_get_account_with_context_manager_mock(mocker):
    """Test getting an account with a mock database context manager."""
    # Arrange
    acc_id = "76561199123456789"
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = (acc_id, "username", "email@example.com")
    mock_cursor.description = [("acc_id",), ("acc_username",), ("acc_email_address",)]
    
    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = mock_conn
    
    mocker.patch("db.get_db_connection", return_value=mock_context)
    
    # Act
    account = get_account(acc_id)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == acc_id
    assert account["acc_username"] == "username"
    assert account["acc_email_address"] == "email@example.com"
```

### Mocking Asynchronous Functions

Use `mocker.patch` with an asynchronous function to mock asynchronous functions.

Example:
```python
@pytest.mark.asyncio
async def test_get_account_async_with_mock(mocker):
    """Test getting an account asynchronously with a mock database."""
    # Arrange
    acc_id = "76561199123456789"
    
    async def mock_get_account_async(acc_id):
        return {
            "acc_id": acc_id,
            "acc_username": "username",
            "acc_email_address": "email@example.com"
        }
    
    mocker.patch("db.get_account_async", side_effect=mock_get_account_async)
    
    # Act
    account = await get_account_async(acc_id)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == acc_id
    assert account["acc_username"] == "username"
    assert account["acc_email_address"] == "email@example.com"
```

## Test Data

### Test Fixtures

Use pytest fixtures to set up test data.

Example:
```python
@pytest.fixture
def test_account():
    """Create a test account."""
    acc_id = "76561199123456789"
    create_test_account(acc_id)
    return acc_id

def test_get_account_with_fixture(test_account):
    """Test getting an account by ID using a fixture."""
    # Act
    account = get_account(test_account)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == test_account
```

### Factory Functions

Use factory functions to create test data.

Example:
```python
def create_test_account(acc_id="76561199123456789", username="testuser", email="test@example.com"):
    """Create a test account."""
    account_data = {
        "acc_id": acc_id,
        "acc_username": username,
        "acc_password": "password123",
        "acc_email_address": email,
        "acc_email_password": "emailpass123"
    }
    return create_account(account_data)

def test_get_account_with_factory():
    """Test getting an account by ID using a factory function."""
    # Arrange
    acc_id = "76561199123456789"
    create_test_account(acc_id)
    
    # Act
    account = get_account(acc_id)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == acc_id
```

### Test Databases

Use a separate test database for testing.

Example:
```python
@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    # Set up test database
    os.environ["DB_NAME"] = "accountdb_test"
    init_test_db()
    
    yield
    
    # Tear down test database
    drop_test_db()

def test_get_account_with_test_db(test_db):
    """Test getting an account by ID using a test database."""
    # Arrange
    acc_id = "76561199123456789"
    create_test_account(acc_id)
    
    # Act
    account = get_account(acc_id)
    
    # Assert
    assert account is not None
    assert account["acc_id"] == acc_id
```

## Continuous Integration

### GitHub Actions

We use GitHub Actions for continuous integration. The CI pipeline runs the following checks:

- Code formatting
- Linting
- Type checking
- Tests
- Test coverage

Example workflow:
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: accountdb
          POSTGRES_PASSWORD: accountdb
          POSTGRES_DB: accountdb_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install -r backend/requirements-dev.txt
    
    - name: Check formatting
      run: |
        black --check .
        isort --check .
    
    - name: Lint
      run: |
        flake8 .
        mypy .
    
    - name: Test
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

### Pre-commit Hooks

We use pre-commit hooks to enforce code style and run tests before committing. To set up pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Example pre-commit configuration:
```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.1
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/pycqa/isort
    rev: 5.9.3
    hooks:
    -   id: isort

-   repo: https://github.com/psf/black
    rev: 21.9b0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
    -   id: flake8

-   repo: local
    hooks:
    -   id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Performance Testing

### Load Testing

We use Locust for load testing. Locust is a Python-based load testing tool that allows you to define user behavior in code.

Example:
```python
from locust import HttpUser, task, between

class AccountUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Log in and get a token
        response = self.client.post(
            "/auth/token",
            json={"username": "testuser", "password": "password123"}
        )
        self.token = response.json()["access_token"]
    
    @task
    def list_accounts(self):
        self.client.get(
            "/accounts/list?limit=100&offset=0",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task
    def get_account(self):
        self.client.get(
            "/accounts/76561199123456789",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

To run the load test:

```bash
locust -f locustfile.py
```

### Profiling

We use cProfile for profiling Python code.

Example:
```python
import cProfile
import pstats

def profile_get_accounts():
    """Profile the get_accounts function."""
    cProfile.runctx(
        "get_accounts(limit=100, offset=0)",
        globals(),
        locals(),
        "get_accounts.prof"
    )
    
    stats = pstats.Stats("get_accounts.prof")
    stats.strip_dirs().sort_stats("cumulative").print_stats(20)

if __name__ == "__main__":
    profile_get_accounts()
```

### Benchmarking

We use pytest-benchmark for benchmarking.

Example:
```python
def test_get_account_benchmark(benchmark):
    """Benchmark the get_account function."""
    # Arrange
    acc_id = "76561199123456789"
    create_test_account(acc_id)
    
    # Act & Assert
    account = benchmark(get_account, acc_id)
    assert account is not None
    assert account["acc_id"] == acc_id
```

## Security Testing

### Dependency Scanning

We use safety to scan for vulnerabilities in dependencies.

```bash
safety check
```

### Static Analysis

We use bandit for static security analysis.

```bash
bandit -r .
```

### OWASP ZAP

We use OWASP ZAP for dynamic security testing.

```bash
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:8000
```

## Troubleshooting

### Common Issues

#### Tests Fail with Database Errors

**Problem**: Tests fail with database connection errors.

**Solution**:
1. Make sure the test database is running.
2. Check the database connection parameters.
3. Make sure the test database is initialized.
4. Use a separate test database for testing.

#### Tests Fail with Authentication Errors

**Problem**: Tests fail with authentication errors.

**Solution**:
1. Make sure the JWT secret is configured correctly.
2. Make sure the JWT algorithm is configured correctly.
3. Make sure the JWT expiration is configured correctly.
4. Make sure the test user exists in the database.

#### Tests Are Slow

**Problem**: Tests are slow to run.

**Solution**:
1. Use mocks for external dependencies.
2. Use fixtures to set up test data once.
3. Run tests in parallel with pytest-xdist.
4. Use a separate test database for testing.

#### Tests Fail Intermittently

**Problem**: Tests fail intermittently.

**Solution**:
1. Make sure tests are independent.
2. Make sure tests clean up after themselves.
3. Make sure tests don't depend on external state.
4. Use a separate test database for testing.

### Getting Help

If you need further assistance, please contact the development team or open an issue on the GitHub repository.

## Conclusion

Following these testing guidelines ensures that the AccountDB codebase remains reliable, maintainable, and high-quality. All contributors are expected to write tests for their code. If you have any questions, please don't hesitate to ask.
