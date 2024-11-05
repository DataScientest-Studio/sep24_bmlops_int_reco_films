#!/bin/bash

# Exit on error
set -e

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

# Step 1: Create directory structure
log "Creating directory structure..."
mkdir -p {data/{raw,processed,interim,evaluation},models/{trained_models,artifacts},logs,config,src/{api,data,models,features,monitoring,utils},tests,docs,deployment/{docker,kubernetes},airflow/dags,mlflow,monitoring/{prometheus,grafana/dashboards}}

# Step 2: Set up virtual environment
log "Setting up Python virtual environment..."
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Initialize Git and DVC
log "Initializing Git and DVC..."
git init
dvc init
dvc remote add -d storage s3://your-bucket/path  # Update with your S3 bucket

# Step 4: Set up database
log "Setting up PostgreSQL database..."
if ! command -v psql &> /dev/null; then
    error "PostgreSQL is not installed. Please install it first."
    exit 1
fi

sudo -u postgres psql -c "CREATE DATABASE movie_recommendation;"
sudo -u postgres psql -c "CREATE USER movie_user WITH PASSWORD 'movie_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE movie_recommendation TO movie_user;"

# Step 5: Initialize Airflow
log "Initializing Airflow..."
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Copy DAG files
cp src/airflow/dags/* airflow/dags/

# Step 6: Set up MLflow
log "Setting up MLflow..."
mkdir -p mlflow/artifacts
export MLFLOW_TRACKING_URI=sqlite:///mlflow/mlflow.db

# Step 7: Set up monitoring
log "Setting up monitoring tools..."
docker-compose -f monitoring/docker-compose.yml up -d

# Step 8: Process initial data
log "Processing initial data..."
python src/data/init_db.py --force-reset
python src/data/step1.py
python src/features/build_features.py

# Step 9: Train initial model
log "Training initial model..."
python src/models/train_model.py

# Step 10: Start services
log "Starting services..."
docker-compose up -d
kubectl apply -f deployment/kubernetes/

# Step 11: Run tests
log "Running tests..."
pytest tests/

# Step 12: Set up cron jobs
log "Setting up cron jobs..."
(crontab -l 2>/dev/null; echo "0 0 * * * $(pwd)/scripts/retrain_model.sh") | crontab -
(crontab -l 2>/dev/null; echo "*/15 * * * * $(pwd)/scripts/monitor_performance.sh") | crontab -

log "Setup completed successfully!"
log "Services running at:"
log "- API: http://localhost:8000"
log "- MLflow: http://localhost:5000"
log "- Airflow: http://localhost:8080"
log "- Prometheus: http://localhost:9090"
log "- Grafana: http://localhost:3000"

# Create a post-setup checklist
cat > SETUP_CHECKLIST.md << EOL
# Post-Setup Checklist

## Configuration
- [ ] Update database credentials in .env
- [ ] Configure S3 bucket for DVC
- [ ] Set up Slack/email notifications
- [ ] Configure Kubernetes secrets

## Data
- [ ] Upload initial MovieLens dataset
- [ ] Verify data processing pipeline
- [ ] Check feature engineering output

## Model
- [ ] Verify initial model training
- [ ] Check MLflow experiment tracking
- [ ] Test model retraining pipeline

## Monitoring
- [ ] Configure Grafana dashboards
- [ ] Set up alerting rules
- [ ] Verify metrics collection

## Security
- [ ] Update default passwords
- [ ] Configure SSL certificates
- [ ] Set up API authentication

## Documentation
- [ ] Update API documentation
- [ ] Document custom configurations
- [ ] Add deployment guides
EOL

log "Created post-setup checklist at SETUP_CHECKLIST.md" 