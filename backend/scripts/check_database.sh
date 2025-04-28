#!/bin/bash

# Script to check database status and report any issues
# This script checks database connection, migration status, RLS policies, and indexes

# Set the working directory to the backend directory
cd "$(dirname "$0")/.." || exit 1

# Check database status
echo "Checking database status..."
python -m db.check_database "$@"
