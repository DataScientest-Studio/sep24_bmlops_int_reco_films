# scripts/setup.sh

#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

echo "Installing required packages..."
pip install -r requirements.txt

echo "Installing additional required packages..."
pip install sqlalchemy psycopg2-binary python-dotenv

echo "Setting up the database..."
python3 -m src.data.init_db

echo "Setup completed successfully."

# Mark the init_db step as completed
mkdir -p .pipeline_progress
touch .pipeline_progress/init_db
