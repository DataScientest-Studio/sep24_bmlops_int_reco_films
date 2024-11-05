# src/monitoring/performance_monitor.py

import pandas as pd
import os
from prometheus_client import Gauge, start_http_server

# Define Prometheus metrics
model_rmse = Gauge('model_rmse', 'Model RMSE on evaluation data')

def monitor_performance():
    """
    Monitor the model's performance and expose metrics to Prometheus.
    """
    # Paths
    EVALUATION_DATA_PATH = os.path.join('data', 'evaluation', 'eval_set_1.csv')
    MODEL_PATH = os.path.join('models', 'trained_models', 'current_model.pkl')

    # Load evaluation data
    eval_data = pd.read_csv(EVALUATION_DATA_PATH)

    # Evaluate the model
    from src.models.evaluate_model import evaluate_model
    evaluation_results = evaluate_model(eval_data, MODEL_PATH)

    # Update Prometheus metrics
    rmse = evaluation_results['test_rmse'].mean()
    model_rmse.set(rmse)
    print(f"Model RMSE updated to {rmse}")

if __name__ == "__main__":
    # Start Prometheus server to expose metrics
    start_http_server(8001)
    print("Prometheus metrics server started on port 8001.")

    # Monitor performance periodically
    import time
    while True:
        monitor_performance()
        time.sleep(300)  # Wait for 5 minutes before next check

# Explanation:

#     monitor_performance: Evaluates the model and updates Prometheus metrics.
#     Prometheus Metrics: Exposes the RMSE metric, which can be scraped by Prometheus.