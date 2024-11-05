#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Setting up the database..."

# Drop the existing database if it exists
sudo -u postgres psql -c "DROP DATABASE IF EXISTS movierecsys;"

# Create a new database
sudo -u postgres psql -c "CREATE DATABASE movierecsys;"

# Grant privileges to the user
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE movierecsys TO myuser;"

echo "Database setup completed successfully."
