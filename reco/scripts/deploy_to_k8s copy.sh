#!/bin/bash

# Apply Kubernetes configurations
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/app-deployment.yaml
kubectl apply -f k8s/app-service.yaml
kubectl apply -f k8s/mlflow-deployment.yaml
kubectl apply -f k8s/mlflow-service.yaml
kubectl apply -f k8s/airflow-deployment.yaml
kubectl apply -f k8s/airflow-service.yaml

# Wait for deployments to be ready
kubectl rollout status deployment/postgres
kubectl rollout status deployment/movie-recommender-app
kubectl rollout status deployment/mlflow
kubectl rollout status deployment/airflow

echo "Deployment completed successfully!"
