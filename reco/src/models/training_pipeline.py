"""
Training pipeline for incremental model training and evaluation.
"""

import os
import mlflow
import logging
from datetime import datetime
from src.data.database import (
    get_session, Movie, Rating, ModelEvaluation,
    UserPreference, MovieFeature
)
from src.models.collaborative_filtering import CollaborativeFilteringModel
from src.models.evaluate_model import evaluate_model
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingPipeline:
    def __init__(self, base_model_path: str, processed_data_path: str):
        self.base_model_path = base_model_path
        self.processed_data_path = processed_data_path
        self.session = get_session()
        
        # Set up MLflow
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        mlflow.set_experiment("movie_recommendations")

    def load_subset(self, subset_num: int, subset_type: str = 'train') -> pd.DataFrame:
        """Load a specific subset of data."""
        file_path = os.path.join(
            self.processed_data_path, 
            'subsets', 
            f'subset_{subset_num}_{subset_type}.csv'
        )
        return pd.read_csv(file_path)

    def train_and_evaluate(self, subset_num: int):
        """Train and evaluate model on a specific subset."""
        logger.info(f"Training on subset {subset_num}")
        
        # Load data
        train_data = self.load_subset(subset_num, 'train')
        test_data = self.load_subset(subset_num, 'test')
        
        # Start MLflow run
        with mlflow.start_run(run_name=f"subset_{subset_num}"):
            # Train model
            model_path = f"{self.base_model_path}_subset_{subset_num}.pkl"
            model = CollaborativeFilteringModel(model_path)
            model.fit(train_data)
            
            # Evaluate model
            metrics = evaluate_model(model, test_data)
            
            # Log metrics to MLflow
            for metric_name, (value, _) in metrics.items():
                mlflow.log_metric(metric_name, value)
            
            # Save model
            mlflow.sklearn.log_model(model, f"model_subset_{subset_num}")
            
            # Store evaluation results in database
            eval_record = ModelEvaluation(
                run_id=mlflow.active_run().info.run_id,
                timestamp=datetime.utcnow(),
                model_path=model_path,
                rmse=metrics['RMSE'][0],
                mae=metrics['MAE'][0],
                precision_at_k=metrics['Precision@10'][0],
                recall_at_k=metrics['Recall@10'][0],
                ndcg_at_k=metrics['NDCG@10'][0],
                diversity=metrics['Diversity'][0],
                novelty=metrics['Novelty'][0]
            )
            self.session.add(eval_record)
            self.session.commit()
            
            logger.info(f"Completed training and evaluation for subset {subset_num}")
            return metrics

    def run_pipeline(self, n_subsets: int = 5):
        """Run the complete training pipeline on all subsets."""
        logger.info("Starting training pipeline...")
        
        all_metrics = []
        for i in range(1, n_subsets + 1):
            try:
                metrics = self.train_and_evaluate(i)
                all_metrics.append(metrics)
                logger.info(f"Completed subset {i}/{n_subsets}")
            except Exception as e:
                logger.error(f"Error processing subset {i}: {str(e)}")
        
        # Analyze performance trends
        self.analyze_performance_trends(all_metrics)
        
        logger.info("Training pipeline completed!")

    def analyze_performance_trends(self, all_metrics):
        """Analyze and log performance trends across subsets."""
        # Convert metrics to DataFrame for analysis
        metrics_df = pd.DataFrame([
            {k: v[0] for k, v in metrics.items()}
            for metrics in all_metrics
        ])
        
        # Calculate trends
        trends = metrics_df.diff().mean()
        
        logger.info("Performance Trends:")
        for metric, trend in trends.items():
            trend_direction = "improving" if trend < 0 else "degrading"
            logger.info(f"{metric}: {trend_direction} by {abs(trend):.4f} per subset")

def main():
    base_model_path = "models/collaborative_filtering_model"
    processed_data_path = "data/processed"
    
    pipeline = TrainingPipeline(base_model_path, processed_data_path)
    pipeline.run_pipeline()

if __name__ == "__main__":
    main()
