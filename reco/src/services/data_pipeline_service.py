import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, List, Optional
import pandas as pd
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from tqdm import tqdm

# Then use the original import
from src.data.database import (
    Movie, Rating, Link, Tag, GenomeScore, GenomeTag,
    TrainingSubset, get_session
)

logger = logging.getLogger(__name__)

class DataPipelineService:
    def __init__(self, db: Session = None):
        self.db = db or get_session()
        
    def process_movies(self, movies_df: pd.DataFrame) -> None:
        """Process and store movie data."""
        logger.info("Processing movies data...")
        for _, row in tqdm(movies_df.iterrows(), total=len(movies_df)):
            movie = Movie(
                movieId=row['movieId'],
                title=row['title'],
                genres=row['genres']
            )
            try:
                self.db.merge(movie)
            except Exception as e:
                logger.error(f"Error processing movie {row['movieId']}: {str(e)}")
                self.db.rollback()
        self.db.commit()
        
    def process_ratings(self, ratings_df: pd.DataFrame) -> None:
        """Process and store rating data."""
        logger.info("Processing ratings data...")
        for _, row in tqdm(ratings_df.iterrows(), total=len(ratings_df)):
            rating = Rating(
                userId=row['userId'],
                movieId=row['movieId'],
                rating=row['rating'],
                timestamp=pd.to_datetime(row['timestamp'])
            )
            try:
                self.db.merge(rating)
            except Exception as e:
                logger.error(f"Error processing rating: {str(e)}")
                self.db.rollback()
        self.db.commit()
        
    def create_training_subset(
        self,
        data: pd.DataFrame,
        subset_number: int,
        subset_type: str,
        metadata: Dict
    ) -> None:
        """Create and store a training subset."""
        try:
            subset = TrainingSubset(
                subset_number=subset_number,
                subset_type=subset_type,
                data=data.to_dict('records'),
                created_at=datetime.utcnow(),
                time_range_start=pd.to_datetime(data['timestamp'].min()),
                time_range_end=pd.to_datetime(data['timestamp'].max()),
                n_samples=len(data),
                n_users=len(data['userId'].unique()),
                n_movies=len(data['movieId'].unique()),
                subset_metadata=metadata
            )
            self.db.merge(subset)
            self.db.commit()
            logger.info(f"Created {subset_type} subset {subset_number}")
        except Exception as e:
            logger.error(f"Error creating training subset: {str(e)}")
            self.db.rollback()
            raise
            
    def get_training_subset(
        self,
        subset_number: int,
        subset_type: str
    ) -> Optional[pd.DataFrame]:
        """Retrieve a specific training subset."""
        try:
            subset = (self.db.query(TrainingSubset)
                     .filter_by(subset_number=subset_number, subset_type=subset_type)
                     .first())
            if subset:
                return pd.DataFrame(subset.data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving training subset: {str(e)}")
            return None
            
    def get_latest_data(
        self,
        days: int = 30
    ) -> pd.DataFrame:
        """Get the latest ratings data for a specified number of days."""
        try:
            cutoff_date = datetime.utcnow() - pd.Timedelta(days=days)
            ratings = (self.db.query(Rating)
                      .filter(Rating.timestamp >= cutoff_date)
                      .all())
            return pd.DataFrame([{
                'userId': r.userId,
                'movieId': r.movieId,
                'rating': r.rating,
                'timestamp': r.timestamp
            } for r in ratings])
        except Exception as e:
            logger.error(f"Error retrieving latest data: {str(e)}")
            return pd.DataFrame()
            
    def cleanup_old_subsets(
        self,
        keep_last_n: int = 5
    ) -> None:
        """Clean up old training subsets, keeping only the most recent n."""
        try:
            subsets = (self.db.query(TrainingSubset)
                      .order_by(TrainingSubset.created_at.desc())
                      .all())
            
            # Group by subset type
            subset_groups = {}
            for subset in subsets:
                if subset.subset_type not in subset_groups:
                    subset_groups[subset.subset_type] = []
                subset_groups[subset.subset_type].append(subset)
            
            # Delete old subsets for each type
            for subset_type, type_subsets in subset_groups.items():
                if len(type_subsets) > keep_last_n:
                    for subset in type_subsets[keep_last_n:]:
                        self.db.delete(subset)
            
            self.db.commit()
            logger.info("Cleaned up old training subsets")
        except Exception as e:
            logger.error(f"Error cleaning up old subsets: {str(e)}")
            self.db.rollback()
            
    def close(self):
        """Close the database session."""
        self.db.close() 