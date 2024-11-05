import mlflow
import matplotlib.pyplot as plt
import pandas as pd

def visualize_performance():
    # Get all runs from the MLflow experiment
    runs = mlflow.search_runs()

    # Extract metrics
    metrics = ['RMSE', 'MAE', 'Precision@10', 'Recall@10', 'NDCG@10']
    
    plt.figure(figsize=(12, 8))
    for metric in metrics:
        plt.plot(runs['start_time'], runs[f'metrics.{metric}'], label=metric)
    
    plt.xlabel('Time')
    plt.ylabel('Metric Value')
    plt.title('Model Performance Over Time')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('reports/figures/model_performance_over_time.png')
    plt.close()

    # Create a summary DataFrame
    summary = runs[['start_time'] + [f'metrics.{m}' for m in metrics]].describe()
    summary.to_csv('reports/model_performance_summary.csv')

if __name__ == "__main__":
    visualize_performance()
