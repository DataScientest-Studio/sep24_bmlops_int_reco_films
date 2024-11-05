#!/bin/bash

# Run pytest with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run API tests
python -m pytest tests/test_api.py

# Run database viewer test
python scripts/database_viewer.py

# Run recommendations test
python scripts/test_recommendations.py

# Test Kubernetes deployment (make sure you have a test cluster or minikube running)
./scripts/deploy_to_k8s.sh

# Test Docker build
docker build -t movie-recommender:test .

# Test Docker Compose
docker-compose up -d
docker-compose down

# Run monitoring tests
python -m unittest tests/test_monitoring.py
