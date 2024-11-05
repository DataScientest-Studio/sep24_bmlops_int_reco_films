# tests/test_monitoring.py

import unittest
import requests
from src.monitoring.performance_monitor import monitor_performance

class TestMonitoring(unittest.TestCase):
    def test_monitor_performance(self):
        rmse = monitor_performance()
        self.assertIsNotNone(rmse)
        self.assertIsInstance(rmse, float)

    def test_prometheus_metrics(self):
        response = requests.get("http://localhost:8000/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("recommendations_total", response.text)
        self.assertIn("feedback_total", response.text)
        self.assertIn("request_processing_seconds", response.text)

    def test_grafana_dashboard(self):
        response = requests.get("http://localhost:3000/api/dashboards/uid/movie-recommender")
        self.assertEqual(response.status_code, 200)
        dashboard_data = response.json()
        self.assertEqual(dashboard_data["dashboard"]["title"], "Movie Recommender Dashboard")

if __name__ == '__main__':
    unittest.main()
