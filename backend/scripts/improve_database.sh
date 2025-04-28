#!/bin/bash

# Script to improve database performance and security
# This script runs all the database improvements in one go

# Set the working directory to the backend directory
cd "$(dirname "$0")/.." || exit 1

# Check if the database is running
echo "Checking database connection..."
python -c "from db.connection import get_db_connection; conn = get_db_connection(); print('Database connection successful' if conn else 'Database connection failed'); conn.close() if conn else None" || {
    echo "Error: Could not connect to the database"
    exit 1
}

# Run database improvements
echo "Running database improvements..."
python -m db.improve_database "$@"

# Check database status
echo "Checking database status..."
python -m db.check_database

echo "Database improvements completed"
