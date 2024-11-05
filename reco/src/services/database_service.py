from typing import List, Dict, Optional, Any
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
from pathlib import Path

from src.data.database import (
    get_session, Movie, Rating, User, UserPreference,
    MovieFeature, Feedback, ModelEvaluation, TrainingSubset
)

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_url: str = None):
        self.engine = create_engine(db_url) if db_url else get_session().bind
        
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute raw SQL query and return results."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise

    def get_user_ratings(self, user_id: int) -> pd.DataFrame:
        """Get all ratings for a specific user."""
        query = """
            SELECT r.*, m.title, m.genres
            FROM ratings r
            JOIN movies m ON r."movieId" = m."movieId"
            WHERE r."userId" = :user_id
            ORDER BY r.timestamp DESC
        """
        return pd.read_sql(text(query), self.engine, params={'user_id': user_id})

    def get_movie_ratings(self, movie_id: int) -> pd.DataFrame:
        """Get all ratings for a specific movie."""
        query = """
            SELECT r.*, u.username
            FROM ratings r
            JOIN users u ON r."userId" = u.id
            WHERE r."movieId" = :movie_id
            ORDER BY r.timestamp DESC
        """
        return pd.read_sql(text(query), self.engine, params={'movie_id': movie_id})

    def save_model_evaluation(
        self,
        run_id: str,
        model_path: str,
        metrics: Dict[str, float]
    ) -> None:
        """Save model evaluation results to database."""
        try:
            session = get_session()
            evaluation = ModelEvaluation(
                run_id=run_id,
                timestamp=datetime.utcnow(),
                model_path=model_path,
                rmse=metrics.get('rmse'),
                mae=metrics.get('mae'),
                precision_at_k=metrics.get('precision_at_k'),
                recall_at_k=metrics.get('recall_at_k'),
                ndcg_at_k=metrics.get('ndcg_at_k'),
                diversity=metrics.get('diversity'),
                novelty=metrics.get('novelty')
            )
            session.add(evaluation)
            session.commit()
            logger.info(f"Saved evaluation results for run {run_id}")
        except Exception as e:
            logger.error(f"Error saving model evaluation: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    def save_training_subset(
        self,
        subset_df: pd.DataFrame,
        subset_num: int,
        subset_type: str,
        metadata: Dict
    ) -> None:
        """Save training subset to database."""
        try:
            session = get_session()
            subset = TrainingSubset(
                subset_number=subset_num,
                subset_type=subset_type,
                data=subset_df.to_dict('records'),
                created_at=datetime.utcnow(),
                time_range_start=pd.to_datetime(subset_df['timestamp'].min()),
                time_range_end=pd.to_datetime(subset_df['timestamp'].max()),
                n_samples=len(subset_df),
                n_users=len(subset_df['userId'].unique()),
                n_movies=len(subset_df['movieId'].unique()),
                subset_metadata=metadata
            )
            session.add(subset)
            session.commit()
            logger.info(f"Saved {subset_type} subset {subset_num}")
        except Exception as e:
            logger.error(f"Error saving training subset: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_latest_model_evaluation(self) -> Optional[Dict]:
        """Get the most recent model evaluation results."""
        try:
            session = get_session()
            evaluation = (session.query(ModelEvaluation)
                        .order_by(ModelEvaluation.timestamp.desc())
                        .first())
            if evaluation:
                return {
                    'run_id': evaluation.run_id,
                    'timestamp': evaluation.timestamp,
                    'model_path': evaluation.model_path,
                    'metrics': {
                        'rmse': evaluation.rmse,
                        'mae': evaluation.mae,
                        'precision_at_k': evaluation.precision_at_k,
                        'recall_at_k': evaluation.recall_at_k,
                        'ndcg_at_k': evaluation.ndcg_at_k,
                        'diversity': evaluation.diversity,
                        'novelty': evaluation.novelty
                    }
                }
            return None
        except Exception as e:
            logger.error(f"Error getting latest model evaluation: {str(e)}")
            raise
        finally:
            session.close()

    def backup_database(self, backup_dir: str) -> None:
        """Create a backup of the database."""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup each table
            tables = [
                (Movie, 'movies.csv'),
                (Rating, 'ratings.csv'),
                (User, 'users.csv'),
                (UserPreference, 'user_preferences.csv'),
                (MovieFeature, 'movie_features.csv'),
                (Feedback, 'feedback.csv'),
                (ModelEvaluation, 'model_evaluations.csv'),
                (TrainingSubset, 'training_subsets.csv')
            ]
            
            for model, filename in tables:
                df = pd.read_sql(
                    session.query(model).statement,
                    self.engine
                )
                df.to_csv(backup_path / filename, index=False)
                
            logger.info(f"Database backup created in {backup_dir}")
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            raise

    def restore_database(self, backup_dir: str) -> None:
        """Restore database from backup."""
        try:
            backup_path = Path(backup_dir)
            session = get_session()
            
            # Restore each table
            if (backup_path / 'movies.csv').exists():
                movies_df = pd.read_csv(backup_path / 'movies.csv')
                for _, row in movies_df.iterrows():
                    movie = Movie(**row.to_dict())
                    session.merge(movie)
            
            if (backup_path / 'ratings.csv').exists():
                ratings_df = pd.read_csv(backup_path / 'ratings.csv')
                for _, row in ratings_df.iterrows():
                    rating = Rating(**row.to_dict())
                    session.merge(rating)
            
            # Continue for other tables...
            
            session.commit()
            logger.info(f"Database restored from {backup_dir}")
        except Exception as e:
            logger.error(f"Error restoring database: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            session = get_session()
            stats = {
                'total_users': session.query(User).count(),
                'total_movies': session.query(Movie).count(),
                'total_ratings': session.query(Rating).count(),
                'total_feedback': session.query(Feedback).count(),
                'avg_rating': session.query(func.avg(Rating.rating)).scalar(),
                'last_rating': session.query(func.max(Rating.timestamp)).scalar(),
                'last_feedback': session.query(func.max(Feedback.timestamp)).scalar(),
                'model_evaluations': session.query(ModelEvaluation).count(),
                'training_subsets': session.query(TrainingSubset).count()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            raise
        finally:
            session.close() 