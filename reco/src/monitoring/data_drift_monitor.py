# src/monitoring/data_drift_monitor.py

import pandas as pd
import os
from prometheus_client import Gauge, start_http_server
import time
from evidently.model_profile import Profile
from evidently.model_profile.sections import DataDriftProfileSection

def monitor_data_drift(reference_data_path, current_data_path):
    """
    Monitor data drift between reference data and current data.

    Args:
        reference_data_path (str): Path to the reference data CSV file.
        current_data_path (str): Path to the current data CSV file.

    Returns:
        float: Data drift score (percentage of drifted features).
    """
    # Load data
    reference_data = pd.read_csv(reference_data_path)
    current_data = pd.read_csv(current_data_path)

    # Create a data drift profile
    profile = Profile(sections=[DataDriftProfileSection()])
    profile.calculate(reference_data, current_data)

    # Extract drift metrics
    report = profile.json()
    import json
    report_dict = json.loads(report)
    drift_metrics = report_dict["data_drift"]["data"]["metrics"]
    n_drifted_features = drift_metrics["n_drifted_features"]
    n_features = drift_metrics["n_features"]
    drift_share = drift_metrics["share_drifted_features"]

    return drift_share

if __name__ == "__main__":
    # Start Prometheus server to expose metrics
    start_http_server(8002)
    print("Prometheus metrics server started on port 8002.")

    # Define Prometheus metric
    data_drift_metric = Gauge('data_drift_share', 'Share of Drifted Features')

    # Paths to reference and current data
    REFERENCE_DATA_PATH = os.path.join('data', 'processed', 'reference_data.csv')
    CURRENT_DATA_PATH = os.path.join('data', 'processed', 'current_data.csv')

    while True:
        try:
            drift_share = monitor_data_drift(REFERENCE_DATA_PATH, CURRENT_DATA_PATH)
            data_drift_metric.set(drift_share)
            print(f"Data drift share updated: {drift_share}")
        except Exception as e:
            print(f"Error monitoring data drift: {e}")
        time.sleep(3600)  # Check every hour


# Explanation:

#     Uses the Evidently library to calculate data drift metrics.
#     Exposes the data_drift_share metric to Prometheus.
#     Runs an infinite loop to monitor data drift every hour.