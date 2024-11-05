#!/bin/bash

# Exit on error
set -e

# Load environment variables
source .env

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting setup process...${NC}"

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install requirements
pip install -r requirements.txt

# 3. Initialize database
python scripts/init_database.py

# 4. Set up DVC
dvc init
dvc remote add -d storage s3://your-bucket/path
dvc remote modify storage access_key_id ${AWS_ACCESS_KEY_ID}
dvc remote modify storage secret_access_key ${AWS_SECRET_ACCESS_KEY}

# 5. Start Docker services
docker-compose up -d

# 6. Initialize Airflow
airflow db init
airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# 7. Start MLflow server
mlflow server \
    --backend-store-uri postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME} \
    --default-artifact-root ./mlruns \
    --host 0.0.0.0 \
    --port 5000 &

# 8. Set up monitoring
./scripts/setup_monitoring.sh

echo -e "${GREEN}Setup completed successfully!${NC}" 