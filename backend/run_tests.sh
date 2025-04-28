#!/bin/bash

# Run tests script for AccountDB

# Set up environment variables for testing
export TEST_DB_HOST=${TEST_DB_HOST:-localhost}
export TEST_DB_PORT=${TEST_DB_PORT:-5432}
export TEST_DB_NAME=${TEST_DB_NAME:-accountdb_test}
export TEST_DB_USER=${TEST_DB_USER:-postgres}
export TEST_DB_PASS=${TEST_DB_PASS:-postgres}

# Create logs directory if it doesn't exist
mkdir -p logs

# Parse command line arguments
UNIT_TESTS=false
INTEGRATION_TESTS=false
PERFORMANCE_TESTS=false
ALL_TESTS=false
COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --unit)
            UNIT_TESTS=true
            shift
            ;;
        --integration)
            INTEGRATION_TESTS=true
            shift
            ;;
        --performance)
            PERFORMANCE_TESTS=true
            shift
            ;;
        --all)
            ALL_TESTS=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $key"
            echo "Usage: $0 [--unit] [--integration] [--performance] [--all] [--coverage] [--verbose|-v]"
            exit 1
            ;;
    esac
done

# If no test type is specified, run all tests
if [[ "$UNIT_TESTS" == "false" && "$INTEGRATION_TESTS" == "false" && "$PERFORMANCE_TESTS" == "false" && "$ALL_TESTS" == "false" ]]; then
    ALL_TESTS=true
fi

# Load test environment variables
if [ -f .env.test ]; then
    echo "Loading test environment variables from .env.test"
    export $(grep -v '^#' .env.test | xargs)
fi

# Build the pytest command
PYTEST_CMD="python -m pytest"

# Add verbosity
if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage
if [[ "$COVERAGE" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term --cov-report=html"
fi

# Add test selection
if [[ "$ALL_TESTS" == "true" ]]; then
    echo "Running all tests..."
    $PYTEST_CMD
elif [[ "$UNIT_TESTS" == "true" && "$INTEGRATION_TESTS" == "true" && "$PERFORMANCE_TESTS" == "true" ]]; then
    echo "Running unit, integration, and performance tests..."
    $PYTEST_CMD -m "unit or integration or performance"
elif [[ "$UNIT_TESTS" == "true" && "$INTEGRATION_TESTS" == "true" ]]; then
    echo "Running unit and integration tests..."
    $PYTEST_CMD -m "unit or integration"
elif [[ "$UNIT_TESTS" == "true" && "$PERFORMANCE_TESTS" == "true" ]]; then
    echo "Running unit and performance tests..."
    $PYTEST_CMD -m "unit or performance"
elif [[ "$INTEGRATION_TESTS" == "true" && "$PERFORMANCE_TESTS" == "true" ]]; then
    echo "Running integration and performance tests..."
    $PYTEST_CMD -m "integration or performance"
elif [[ "$UNIT_TESTS" == "true" ]]; then
    echo "Running unit tests..."
    $PYTEST_CMD -m "unit"
elif [[ "$INTEGRATION_TESTS" == "true" ]]; then
    echo "Running integration tests..."
    $PYTEST_CMD -m "integration"
elif [[ "$PERFORMANCE_TESTS" == "true" ]]; then
    echo "Running performance tests..."
    $PYTEST_CMD -m "performance"
fi

# Exit with the pytest exit code
exit $?
