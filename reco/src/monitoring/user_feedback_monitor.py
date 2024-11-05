# src/monitoring/user_feedback_monitor.py

import pandas as pd
import os
from prometheus_client import Gauge, start_http_server
import time

def monitor_user_feedback(feedback_data_path):
    """
    Monitor user feedback and calculate satisfaction score.

    Args:
        feedback_data_path (str): Path to the user feedback CSV file.

    Returns:
        float: Average user satisfaction score.
    """
    if not os.path.exists(feedback_data_path):
        print("Feedback data file does not exist.")
        return 0.0

    feedback_data = pd.read_csv(feedback_data_path)
    if feedback_data.empty:
        print("Feedback data is empty.")
        return 0.0

    # Calculate average satisfaction score
    satisfaction_score = feedback_data['satisfaction_rating'].mean()
    return satisfaction_score

if __name__ == "__main__":
    # Start Prometheus server to expose metrics
    start_http_server(8003)
    print("Prometheus metrics server started on port 8003.")

    # Define Prometheus metric
    user_satisfaction_metric = Gauge('user_satisfaction_score', 'Average User Satisfaction Score')

    # Path to user feedback data
    FEEDBACK_DATA_PATH = os.path.join('data', 'feedback', 'user_feedback.csv')

    while True:
        try:
            satisfaction_score = monitor_user_feedback(FEEDBACK_DATA_PATH)
            user_satisfaction_metric.set(satisfaction_score)
            print(f"User satisfaction score updated: {satisfaction_score}")
        except Exception as e:
            print(f"Error monitoring user feedback: {e}")
        time.sleep(300)  # Check every 5 minutes


# Calculates the average user satisfaction score from feedback data.
# Exposes the user_satisfaction_score metric to Prometheus.
# Checks for feedback updates every 5 minutes.