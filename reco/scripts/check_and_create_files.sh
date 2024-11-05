#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Project root directory
PROJECT_ROOT="reco_clean"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Required files structure
declare -A REQUIRED_FILES=(
    # Configuration files
    ["config/config.yaml"]="Main configuration file"
    ["config/model_config.yaml"]="Model configuration"
    ["config/monitoring_config.yaml"]="Monitoring configuration"
    ["config/airflow_config.yaml"]="Airflow configuration"
    ["config/database_config.yaml"]="Database configuration"
    
    # Source code - API
    ["src/api/__init__.py"]="API initialization"
    ["src/api/main.py"]="Main API application"
    ["src/api/routes.py"]="API routes"
    ["src/api/auth.py"]="Authentication module"
    ["src/api/endpoints.py"]="API endpoints"
    
    # Source code - Data
    ["src/data/__init__.py"]="Data module initialization"
    ["src/data/database.py"]="Database models"
    ["src/data/init_db.py"]="Database initialization"
    ["src/data/data_processing.py"]="Data processing"
    ["src/data/step1.py"]="Data preprocessing step"
    
    # Source code - Models
    ["src/models/__init__.py"]="Models initialization"
    ["src/models/collaborative_filtering.py"]="Collaborative filtering model"
    ["src/models/train_model.py"]="Model training"
    ["src/models/evaluate_model.py"]="Model evaluation"
    ["src/models/predict_model.py"]="Model prediction"
    ["src/models/retrain_model.py"]="Model retraining"
    ["src/models/user_model.py"]="User model"
    ["src/models/feedback.py"]="Feedback model"
    
    # Source code - Features
    ["src/features/__init__.py"]="Features initialization"
    ["src/features/build_features.py"]="Feature engineering"
    
    # Source code - Monitoring
    ["src/monitoring/__init__.py"]="Monitoring initialization"
    ["src/monitoring/data_drift_monitor.py"]="Data drift monitoring"
    ["src/monitoring/performance_monitor.py"]="Performance monitoring"
    ["src/monitoring/user_feedback_monitor.py"]="User feedback monitoring"
    
    # Source code - Utils
    ["src/utils/__init__.py"]="Utils initialization"
    ["src/utils/config.py"]="Configuration utilities"
    ["src/utils/logger.py"]="Logging utilities"
    
    # Tests
    ["tests/__init__.py"]="Tests initialization"
    ["tests/test_api.py"]="API tests"
    ["tests/test_model.py"]="Model tests"
    ["tests/test_data.py"]="Data tests"
    ["tests/test_monitoring.py"]="Monitoring tests"
    
    # Airflow DAGs
    ["airflow/dags/training_dag.py"]="Training DAG"
    ["airflow/dags/monitoring_dag.py"]="Monitoring DAG"
    ["airflow/dags/retraining_dag.py"]="Retraining DAG"
    
    # Scripts
    ["scripts/setup.sh"]="Setup script"
    ["scripts/run_pipeline.sh"]="Pipeline execution"
    ["scripts/deploy_to_k8s.sh"]="Kubernetes deployment"
    
    # Documentation
    ["docs/api.md"]="API documentation"
    ["docs/model.md"]="Model documentation"
    ["docs/deployment.md"]="Deployment documentation"
    
    # Deployment
    ["deployment/Dockerfile"]="Dockerfile"
    ["deployment/docker-compose.yml"]="Docker Compose"
    ["deployment/kubernetes/deployment.yaml"]="Kubernetes deployment"
    ["deployment/kubernetes/service.yaml"]="Kubernetes service"
)

# Check and create directories
log "Creating directory structure..."
for file_path in "${!REQUIRED_FILES[@]}"; do
    dir_path=$(dirname "${PROJECT_ROOT}/${file_path}")
    mkdir -p "$dir_path"
done

# Check and create files
log "Checking required files..."
missing_files=()
for file_path in "${!REQUIRED_FILES[@]}"; do
    full_path="${PROJECT_ROOT}/${file_path}"
    if [ ! -f "$full_path" ]; then
        missing_files+=("$file_path")
        warn "Missing: $file_path - ${REQUIRED_FILES[$file_path]}"
    else
        log "Found: $file_path"
    fi
done

# Create missing files with templates
if [ ${#missing_files[@]} -gt 0 ]; then
    log "Creating missing files..."
    for file_path in "${missing_files[@]}"; do
        full_path="${PROJECT_ROOT}/${file_path}"
        
        # Create file based on type
        case "$file_path" in
            *.py)
                echo "\"\"\"
${REQUIRED_FILES[$file_path]}
\"\"\"

# Add your code here
" > "$full_path"
                ;;
            *.yaml|*.yml)
                echo "# ${REQUIRED_FILES[$file_path]}

# Add your configuration here
" > "$full_path"
                ;;
            *.md)
                echo "# ${REQUIRED_FILES[$file_path]}

## Overview

Add documentation here
" > "$full_path"
                ;;
            *.sh)
                echo "#!/bin/bash

# ${REQUIRED_FILES[$file_path]}

# Add your script here
" > "$full_path"
                chmod +x "$full_path"
                ;;
            *)
                echo "# ${REQUIRED_FILES[$file_path]}" > "$full_path"
                ;;
        esac
        log "Created: $file_path"
    done
fi

# Create .gitignore
log "Creating .gitignore..."
cat > "${PROJECT_ROOT}/.gitignore" << 'EOL'
# Python
__pycache__/
*.py[cod]
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
.env
.venv

# Data and Models
data/raw/
data/processed/
data/interim/
models/trained_models/
*.csv
*.pkl
*.h5
*.keras
*.joblib

# Logs and monitoring
logs/
*.log
monitoring/data/

# MLflow
mlruns/
mlflow.db

# Airflow
airflow.db
airflow.cfg
webserver_config.py
airflow-webserver.pid

# IDE
.idea/
.vscode/
*.swp
*.swo

# DVC
.dvc/
/dvc.lock
/dvc.yaml

# Keep
!requirements.txt
!setup.py
!README.md
!config/*.yaml
!deployment/kubernetes/*.yaml
EOL

# Create README.md if it doesn't exist
if [ ! -f "${PROJECT_ROOT}/README.md" ]; then
    log "Creating README.md..."
    cat > "${PROJECT_ROOT}/README.md" << 'EOL'
# Movie Recommendation System

## Overview

This is a comprehensive movie recommendation system built with MLOps best practices.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python src/data/init_db.py
```

4. Run the pipeline:
```bash
./scripts/run_pipeline.sh
```

## Components

- Data Processing Pipeline
- Collaborative Filtering Model
- FastAPI Service
- MLflow Tracking
- Airflow DAGs
- Prometheus/Grafana Monitoring

## Documentation

See the `docs/` directory for detailed documentation.
EOL
fi

log "File structure verification and creation completed!"
log "Next steps:"
log "1. Review and update the created files"
log "2. Install dependencies: pip install -r requirements.txt"
log "3. Initialize the database: python src/data/init_db.py"
log "4. Run the pipeline: ./scripts/run_pipeline.sh" 