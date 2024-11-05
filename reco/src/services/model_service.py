from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import mlflow
from sqlalchemy.orm import Session

from src.data.database import (
    get_session, Movie, Rating, ModelEvaluation,
    UserPreference, MovieFeature
)
from src.models.collaborative_filtering import CollaborativeFiltering

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, db: Session = None):
        self.db = db or get_session()
        self.model = CollaborativeFiltering()
        
    def train_model(
        self,
        training_data: pd.DataFrame,
        model_params: Dict = None
    ) -> None:
        """Train the model and log metrics with MLflow."""
        try:
            with mlflow.start_run():
                # Log parameters
                if model_params:
                    mlflow.log_params(model_params)
                
                # Train model
                self.model.fit(training_data)
                
                # Save model artifacts
                mlflow.sklearn.log_model(self.model, "model")
                
                logger.info("Model training completed successfully")
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
            
    def generate_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10
    ) -> List[Dict]:
        """Generate movie recommendations for a user."""
        try:
            # Get user's rated movies
            rated_movies = set(
                rating.movieId for rating in 
                self.db.query(Rating).filter_by(userId=user_id).all()
            )
            
            # Get recommendations
            recommended_movie_ids = self.model.recommend(
                user_id,
                n_recommendations=n_recommendations + len(rated_movies)
            )
            
            # Filter out already rated movies
            recommended_movie_ids = [
                mid for mid in recommended_movie_ids 
                if mid not in rated_movies
            ][:n_recommendations]
            
            # Get movie details
            recommendations = []
            for movie_id in recommended_movie_ids:
                movie = self.db.query(Movie).filter_by(movieId=movie_id).first()
                if movie:
                    # Get average rating
                    avg_rating = (self.db.query(func.avg(Rating.rating))
                                .filter_by(movieId=movie_id)
                                .scalar())
                    
                    recommendations.append({
                        'movieId': movie.movieId,
                        'title': movie.title,
                        'genres': movie.genres,
                        'averageRating': float(avg_rating) if avg_rating else None
                    })
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
            
    def evaluate_model(
        self,
        test_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Evaluate the model and log metrics."""
        try:
            metrics = {}
            
            # Calculate RMSE
            predictions = []
            for _, row in test_data.iterrows():
                pred = self.model.predict(row['userId'], row['movieId'])
                predictions.append((row['rating'], pred))
            
            rmse = np.sqrt(np.mean([(true - pred) ** 2 
                                  for true, pred in predictions]))
            metrics['rmse'] = rmse
            
            # Calculate additional metrics
            metrics.update(self._calculate_additional_metrics(test_data))
            
            # Log evaluation to database
            eval_record = ModelEvaluation(
                timestamp=datetime.utcnow(),
                rmse=metrics['rmse'],
                mae=metrics.get('mae'),
                precision_at_k=metrics.get('precision_at_k'),
                recall_at_k=metrics.get('recall_at_k'),
                ndcg_at_k=metrics.get('ndcg_at_k'),
                diversity=metrics.get('diversity'),
                novelty=metrics.get('novelty')
            )
            self.db.add(eval_record)
            self.db.commit()
            
            return metrics
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            self.db.rollback()
            return {}
            
    def _calculate_additional_metrics(
        self,
        test_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate additional evaluation metrics."""
        metrics = {}
        try:
            # Calculate MAE
            predictions = []
            for _, row in test_data.iterrows():
                pred = self.model.predict(row['userId'], row['movieId'])
                predictions.append((row['rating'], pred))
            
            mae = np.mean([abs(true - pred) for true, pred in predictions])
            metrics['mae'] = mae
            
            # Add more metrics as needed
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating additional metrics: {str(e)}")
            return metrics
            
    def get_model_performance_history(
        self,
        days: int = 30
    ) -> pd.DataFrame:
        """Get historical model performance metrics."""
        try:
            cutoff_date = datetime.utcnow() - pd.Timedelta(days=days)
            evaluations = (self.db.query(ModelEvaluation)
                         .filter(ModelEvaluation.timestamp >= cutoff_date)
                         .all())
            
            return pd.DataFrame([{
                'timestamp': eval.timestamp,
                'rmse': eval.rmse,
                'mae': eval.mae,
                'precision_at_k': eval.precision_at_k,
                'recall_at_k': eval.recall_at_k,
                'ndcg_at_k': eval.ndcg_at_k,
                'diversity': eval.diversity,
                'novelty': eval.novelty
            } for eval in evaluations])
        except Exception as e:
            logger.error(f"Error retrieving model performance history: {str(e)}")
            return pd.DataFrame()
            
    def close(self):
        """Close the database session."""
        self.db.close() 