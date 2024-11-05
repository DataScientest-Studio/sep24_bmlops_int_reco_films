#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 is required but not installed."
        exit 1
    fi
}

# Check required commands
required_commands=(python docker kubectl mlflow dvc)
for cmd in "${required_commands[@]}"; do
    check_command $cmd
done

# Step 1: Environment Setup
log "Setting up environment..."
./scripts/setup_environment.sh
if [ $? -ne 0 ]; then
    error "Environment setup failed"
    exit 1
fi

# Step 2: Database Setup
log "Setting up database..."
./scripts/setup_database.sh
if [ $? -ne 0 ]; then
    error "Database setup failed"
    exit 1
fi

# Step 3: Data Processing
log "Processing data..."
python src/data/data_pipeline.py
if [ $? -ne 0 ]; then
    error "Data processing failed"
    exit 1
fi

# Step 4: Feature Engineering
log "Building features..."
python src/features/build_features.py
if [ $? -ne 0 ]; then
    error "Feature engineering failed"
    exit 1
fi

# Step 5: Model Training
log "Training model..."
python src/models/train_model.py
if [ $? -ne 0 ]; then
    error "Model training failed"
    exit 1
fi

# Step 6: Model Evaluation
log "Evaluating model..."
python src/models/evaluate_model.py
if [ $? -ne 0 ]; then
    error "Model evaluation failed"
    exit 1
fi

# Step 7: Start Services
log "Starting services..."

# Start MLflow
mlflow server \
    --backend-store-uri ${MLFLOW_BACKEND_URI} \
    --default-artifact-root ${MLFLOW_ARTIFACT_ROOT} \
    --host 0.0.0.0 \
    --port 5000 &
MLFLOW_PID=$!

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Start API server
python src/api/main.py &
API_PID=$!

# Step 8: Run Tests
log "Running tests..."
./scripts/run_tests.sh
if [ $? -ne 0 ]; then
    warn "Some tests failed"
fi

# Step 9: Deploy to Kubernetes (if enabled)
if [ "${DEPLOY_TO_K8S}" = "true" ]; then
    log "Deploying to Kubernetes..."
    ./scripts/deploy_to_k8s.sh
    if [ $? -ne 0 ]; then
        error "Kubernetes deployment failed"
        exit 1
    fi
fi

# Cleanup function
cleanup() {
    log "Cleaning up..."
    kill $MLFLOW_PID $API_PID
    docker-compose -f docker-compose.monitoring.yml down
}

# Register cleanup function
trap cleanup EXIT

log "Pipeline completed successfully!"
log "Services running at:"
log "- MLflow UI: http://localhost:5000"
log "- API: http://localhost:8000"
log "- Prometheus: http://localhost:9090"
log "- Grafana: http://localhost:3000" 