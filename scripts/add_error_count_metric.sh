#!/bin/bash

# Script to add the error_count metric to the database

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source the environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# Database connection parameters
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-accountdb}
DB_USER=${DB_USER:-acc_user}
DB_PASSWORD=${DB_PASSWORD:-acc_password}

echo "Adding error_count metric to database..."

# Run the SQL script
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$PROJECT_ROOT/inits/15-add_error_count_metric.sql"

if [ $? -eq 0 ]; then
    echo "Successfully added error_count metric to database."
else
    echo "Failed to add error_count metric to database."
    exit 1
fi

echo "Done."
