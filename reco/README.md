# Movie Recommendation MLOps Project

A comprehensive movie recommendation system implementing MLOps best practices, including continuous training, monitoring, and automated deployment.

[![CI/CD](https://github.com/yourusername/movie-recommendation/actions/workflows/ci_cd.yml/badge.svg)](https://github.com/yourusername/movie-recommendation/actions/workflows/ci_cd.yml)

## Current Status

### ✅ Completed Features

1. **Data Processing and Integration**
   - Successfully integrated all data sources:
     - movies.csv
     - ratings.csv
     - links.csv
     - tags.csv
     - genome-scores.csv
     - genome-tags.csv
   - Implemented data preprocessing pipeline
   - Created time-based data subsets for incremental training

2. **Database Integration**
   - PostgreSQL database setup with SQLAlchemy
   - Implemented all necessary data models
   - Data migration from CSV to database
   - User feedback storage system

3. **Collaborative Filtering Implementation**
   - Implemented user-based collaborative filtering
   - Added item-based similarity calculations
   - Integrated user preferences into recommendations
   - Added support for cold-start scenarios

4. **Model Training and Evaluation**
   - Implemented comprehensive evaluation metrics:
     - RMSE, MAE
     - Precision@K, Recall@K
     - NDCG@K
     - Coverage and Diversity metrics
   - Added support for subset-based training
   - Implemented model versioning with MLflow

5. **Monitoring and Logging**
   - Set up Prometheus metrics
   - Created Grafana dashboards
   - Implemented performance monitoring
   - Added data drift detection

6. **Testing**
   - Unit tests for all components
   - Integration tests for the pipeline
   - API endpoint tests

### 🚧 In Progress

1. **API Enhancement**
   - Adding rate limiting
   - Implementing caching
   - Enhancing error handling

2. **User Feedback Integration**
   - Real-time feedback processing
   - Feedback-based model updates
   - A/B testing framework

3. **Deployment and Scaling**
   - Kubernetes deployment optimization
   - Auto-scaling configuration
   - Production environment setup

## System Architecture




movie-recommendation/
├── src/
│ ├── data/ # Data processing and database operations
│ ├── models/ # Model training and evaluation
│ ├── api/ # FastAPI implementation
│ └── monitoring/ # Monitoring and logging
├── airflow/ # Airflow DAGs for automation
├── tests/ # Unit and integration tests
└── deployment/ # Deployment configurations


## Setup and Installation

1. **Clone the repository and set up DVC**
bash
git clone https://github.com/yourusername/movie-recommendation.git
cd movie-recommendation
dvc init
dvc remote add -d storage s3://your-bucket/path


2. **Set up the environment**
bash
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt


3. **Initialize the database**

bash
python src/data/init_db.py --force-reset
bash


4. **Create data subsets**

python src/data/step1.py
bash


## Running the Pipeline

1. **Start the services**

docker-compose up -d


2. **Run the training pipeline**

bash
python src/models/training_pipeline.py


3. **Start the API**

bash
uvicorn src.api.main:app --reload


## Monitoring

- **MLflow:** Access at `http://localhost:5000`
- **Airflow:** Access at `http://localhost:8080`
- **Prometheus:** Access at `http://localhost:9090`
- **Grafana:** Access at `http://localhost:3000`

## Automated Retraining

The system implements automated retraining through Airflow DAGs:

1. **Weekly Full Retraining**
   - Incorporates all historical data
   - Updates base model

2. **Daily Incremental Updates**
   - Processes new user feedback
   - Updates model weights

3. **Hourly Performance Monitoring**
   - Tracks model metrics
   - Triggers alerts if needed

## DVC and DAGShub Integration

1. **Data Version Control**

bash
dvc add data/raw/movies.csv
dvc push


2. **Experiment Tracking**


bash
dvc exp run
dvc exp show


3. **DAGShub Pipeline**
- Pipeline visualization available at: `https://dagshub.com/username/movie-recommendation`
- Experiment tracking integrated with MLflow

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Next Steps

1. **Short Term**
   - Complete API enhancement
   - Finalize user feedback integration
   - Implement remaining tests

2. **Medium Term**
   - Enhance monitoring system
   - Optimize model performance
   - Improve documentation

3. **Long Term**
   - Scale to larger datasets
   - Add advanced recommendation features
   - Implement A/B testing framework

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This README now reflects:
1. All completed components
Current status of each feature
Clear instructions for setup and usage
Integration with DVC and DAGShub
5. Detailed monitoring and retraining information
