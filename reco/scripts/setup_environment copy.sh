#!/bin/bash

# Setup script for the Movie Recommendation MLOps Project

echo "Creating virtual environment..."
python -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Initializing DVC..."
dvc init

echo "Setting up DVC remote (if applicable)..."
# dvc remote add -d myremote s3://mybucket/path

echo "Environment setup complete."


#chmod +x scripts/setup_environment.sh
