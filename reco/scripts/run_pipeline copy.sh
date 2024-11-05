#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a step has been completed
step_completed() {
    if [ -f ".pipeline_progress/$1" ]; then
        return 0
    else
        return 1
    fi
}

# Function to mark a step as completed
mark_step_completed() {
    mkdir -p .pipeline_progress
    touch ".pipeline_progress/$1"
}

# Check if required directories exist
for dir in data/raw data/processed models src/data src/features src/models src/api tests; do
    if [ ! -d "$dir" ]; then
        log "Error: Directory $dir does not exist. Please check your project structure."
        exit 1
    fi
done

# Step 1: Initialize database and process data
if ! step_completed "init_db_and_process_data"; then
    log "Step 1: Initializing database and processing data..."
    python src/data/init_db.py
    python src/data/make_dataset.py
    mark_step_completed "init_db_and_process_data"
else
    log "Step 1: Database initialized and data processed. Skipping..."
fi

# Step 2: Build features
if ! step_completed "build_features"; then
    log "Step 2: Building features..."
    python src/features/build_features.py
    mark_step_completed "build_features"
else
    log "Step 2: Features already built. Skipping..."
fi

# Step 3: Train the collaborative filtering model
log "Step 3: Training the collaborative filtering model..."
python src/models/train_model.py

# Step 4: Evaluate the model
log "Step 4: Evaluating the model..."
python src/models/evaluate_model.py

# Step 5: Start MLflow server
log "Step 5: Starting MLflow server..."
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns -h 0.0.0.0 -p 5000 &
MLFLOW_PID=$!

# Step 6: Log model and metrics to MLflow
log "Step 6: Logging model and metrics to MLflow..."
python src/models/log_model_to_mlflow.py

# Step 7: Start Airflow
log "Step 7: Initializing Airflow database..."
airflow db init
log "Creating Airflow admin user..."
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
log "Starting Airflow webserver and scheduler..."
airflow webserver -p 8080 &
AIRFLOW_WEBSERVER_PID=$!
airflow scheduler &
AIRFLOW_SCHEDULER_PID=$!

# Step 8: Update DVC
log "Step 8: Updating DVC..."
dvc add data/processed/*.csv models/*.pkl
dvc push

# Step 9: Start the API server
log "Step 9: Starting API server..."
python src/api/main.py &
API_PID=$!

# Wait for API to start
sleep 5

# Step 10: Run tests
log "Step 10: Running tests..."
pytest tests/

# Step 11: Visualize performance
log "Step 11: Visualizing performance..."
python src/visualization/visualize_performance.py

# Step 12: Start monitoring services
log "Step 12: Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

log "Pipeline execution completed successfully."
log "MLflow server running on http://localhost:5000"
log "Airflow webserver running on http://localhost:8080"
log "API server running on http://localhost:8000"
log "Prometheus running on http://localhost:9090"
log "Grafana running on http://localhost:3000"

# Cleanup function to stop background processes
cleanup() {
    log "Cleaning up..."
    kill $MLFLOW_PID $AIRFLOW_WEBSERVER_PID $AIRFLOW_SCHEDULER_PID $API_PID
    docker-compose -f docker-compose.monitoring.yml down
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT
