# src/monitoring/recommendation_quality_monitor.py

import pandas as pd
import os
from prometheus_client import Gauge, start_http_server
import time
from sklearn.metrics import ndcg_score

def monitor_recommendation_quality(ground_truth_path, recommendations_path):
    """
    Monitor the recommendation quality using NDCG.

    Args:
        ground_truth_path (str): Path to the ground truth CSV file.
        recommendations_path (str): Path to the recommendations CSV file.

    Returns:
        float: Average NDCG score.
    """
    # Load data
    ground_truth = pd.read_csv(ground_truth_path)
    recommendations = pd.read_csv(recommendations_path)

    # Merge data on user_id
    merged_data = pd.merge(ground_truth, recommendations, on='user_id', how='inner')

    ndcg_scores = []
    for _, row in merged_data.iterrows():
        true_relevance = [row['true_movie_ids']]  # Assuming this is a list of true movie IDs
        recommended = [row['recommended_movie_ids']]  # Assuming this is a list of recommended movie IDs

        # Compute NDCG score
        ndcg = ndcg_score([true_relevance], [recommended])
        ndcg_scores.append(ndcg)

    if ndcg_scores:
        average_ndcg = sum(ndcg_scores) / len(ndcg_scores)
    else:
        average_ndcg = 0.0

    return average_ndcg

if __name__ == "__main__":
    # Start Prometheus server to expose metrics
    start_http_server(8004)
    print("Prometheus metrics server started on port 8004.")

    # Define Prometheus metric
    recommendation_quality_metric = Gauge('recommendation_ndcg_score', 'Average Recommendation NDCG Score')

    # Paths to ground truth and recommendations
    GROUND_TRUTH_PATH = os.path.join('data', 'evaluation', 'ground_truth.csv')
    RECOMMENDATIONS_PATH = os.path.join('data', 'evaluation', 'recommendations.csv')

    while True:
        try:
            ndcg_score_avg = monitor_recommendation_quality(GROUND_TRUTH_PATH, RECOMMENDATIONS_PATH)
            recommendation_quality_metric.set(ndcg_score_avg)
            print(f"Recommendation NDCG score updated: {ndcg_score_avg}")
        except Exception as e:
            print(f"Error monitoring recommendation quality: {e}")
        time.sleep(3600)  # Check every hour

# Calculates the average NDCG score to assess recommendation quality.
# Exposes the recommendation_ndcg_score metric to Prometheus.
# Runs every hour to update the metric.