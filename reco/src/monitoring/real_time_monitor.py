import time
import logging
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime, timedelta
import yaml
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Prometheus metrics
MODEL_PERFORMANCE = Gauge('model_performance', 'Model performance metrics', ['metric'])
USER_SATISFACTION = Gauge('user_satisfaction', 'User satisfaction score')
API_LATENCY = Histogram('api_latency_seconds', 'API response time', ['endpoint'])
RECOMMENDATION_REQUESTS = Counter('recommendation_requests_total', 'Total recommendation requests')
DATA_DRIFT = Gauge('data_drift', 'Data drift metrics', ['feature'])

class RealTimeMonitor:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.db_engine = create_engine(os.getenv('DATABASE_URL'))
        
    def monitor_model_performance(self):
        """Monitor model performance metrics"""
        try:
            query = text("""
                SELECT rmse, precision_at_k, recall_at_k, ndcg_at_k
                FROM model_evaluations
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            with self.db_engine.connect() as conn:
                result = conn.execute(query).fetchone()
                
            if result:
                MODEL_PERFORMANCE.labels('rmse').set(result.rmse)
                MODEL_PERFORMANCE.labels('precision').set(result.precision_at_k)
                MODEL_PERFORMANCE.labels('recall').set(result.recall_at_k)
                MODEL_PERFORMANCE.labels('ndcg').set(result.ndcg_at_k)
                
        except Exception as e:
            logger.error(f"Error monitoring model performance: {str(e)}")
    
    def monitor_user_feedback(self):
        """Monitor user feedback and satisfaction"""
        try:
            query = text("""
                SELECT AVG(rating) as avg_rating
                FROM user_feedback
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
            """)
            
            with self.db_engine.connect() as conn:
                result = conn.execute(query).fetchone()
                
            if result and result.avg_rating:
                USER_SATISFACTION.set(result.avg_rating)
                
        except Exception as e:
            logger.error(f"Error monitoring user feedback: {str(e)}")
    
    def monitor_data_drift(self):
        """Monitor data drift metrics"""
        try:
            # Implementation of data drift detection
            # This is a placeholder - implement your drift detection logic
            drift_metrics = {
                'rating_dist': 0.05,
                'user_behavior': 0.03,
                'movie_popularity': 0.04
            }
            
            for feature, drift_value in drift_metrics.items():
                DATA_DRIFT.labels(feature).set(drift_value)
                
        except Exception as e:
            logger.error(f"Error monitoring data drift: {str(e)}")
    
    def run(self):
        """Run the monitoring service"""
        # Start Prometheus HTTP server
        start_http_server(self.config['prometheus']['port'])
        logger.info(f"Started Prometheus server on port {self.config['prometheus']['port']}")
        
        while True:
            try:
                self.monitor_model_performance()
                self.monitor_user_feedback()
                self.monitor_data_drift()
                
                # Sleep according to configuration
                time.sleep(self.config['metrics']['model_performance']['interval'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    config_path = "config/monitoring_config.yaml"
    monitor = RealTimeMonitor(config_path)
    monitor.run() 