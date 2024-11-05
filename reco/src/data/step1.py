"""
step1.py - Training Subset Creation and Organization

This script:
1. Loads data from the database
2. Creates time-based subsets for incremental training
3. Stores subsets and metadata in the database
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
import json
from tqdm import tqdm
import logging
from typing import Tuple, List, Dict
from sqlalchemy import text

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.data.database import (
    get_session, Movie, Rating, Link, Tag, 
    GenomeScore, GenomeTag, User, UserPreference, 
    MovieFeature, Feedback, TrainingSubset
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SubsetManager:
    def __init__(self, processed_data_path: str = None):
        if processed_data_path is None:
            processed_data_path = os.path.join(project_root, 'data', 'processed')
            
        self.processed_data_path = processed_data_path
        self.session = get_session()
        
        # Create directories if they don't exist
        os.makedirs(processed_data_path, exist_ok=True)
        os.makedirs(os.path.join(processed_data_path, 'subsets'), exist_ok=True)
        
        logger.info(f"Initialized SubsetManager with processed data path: {processed_data_path}")

    def load_data_from_db(self) -> pd.DataFrame:
        """Load all necessary data from database."""
        logger.info("Loading data from database...")
        
        try:
            query = text("""
                SELECT 
                    r."userId",
                    r."movieId",
                    r.rating,
                    r.timestamp,
                    m.title,
                    m.genres,
                    string_agg(DISTINCT t.tag, '|') as tags,
                    string_agg(DISTINCT gt.tag, '|') as genome_tags,
                    avg(gs.relevance) as avg_relevance
                FROM ratings r
                JOIN movies m ON r."movieId" = m."movieId"
                LEFT JOIN tags t ON r."movieId" = t."movieId"
                LEFT JOIN genome_scores gs ON r."movieId" = gs."movieId"
                LEFT JOIN genome_tags gt ON gs."tagId" = gt."tagId"
                GROUP BY 
                    r."userId",
                    r."movieId",
                    r.rating,
                    r.timestamp,
                    m.title,
                    m.genres
                ORDER BY r.timestamp
            """)
            
            # Execute query using SQLAlchemy 2.0 style
            with self.session.connection() as connection:
                result = connection.execute(query)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                
            logger.info(f"Loaded {len(df)} records from database")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from database: {str(e)}")
            raise

    def store_subset_in_db(self, subset_df: pd.DataFrame, subset_num: int, subset_type: str, metadata: Dict):
        """Store a subset and its metadata in the database."""
        try:
            # Convert DataFrame to records while handling NaN values
            records = subset_df.replace({np.nan: None}).to_dict(orient='records')
            
            subset = TrainingSubset(
                subset_number=subset_num,
                subset_type=subset_type,
                data=records,
                time_range_start=pd.to_datetime(subset_df['timestamp'].min()),
                time_range_end=pd.to_datetime(subset_df['timestamp'].max()),
                n_samples=len(subset_df),
                n_users=len(subset_df['userId'].unique()),
                n_movies=len(subset_df['movieId'].unique()),
                metadata=metadata
            )
            self.session.merge(subset)
            self.session.commit()
            logger.info(f"Stored {subset_type} subset {subset_num} in database")
        except Exception as e:
            logger.error(f"Error storing subset in database: {str(e)}")
            self.session.rollback()
            raise

    def create_time_based_subsets(self, df: pd.DataFrame, n_subsets: int = 5) -> List[Dict]:
        """Create and store time-based subsets."""
        logger.info(f"Creating {n_subsets} time-based subsets...")
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Calculate subset size
        subset_size = len(df) // n_subsets
        
        subsets = []
        for i in range(n_subsets):
            start_idx = i * subset_size
            end_idx = start_idx + subset_size if i < n_subsets - 1 else len(df)
            subset = df.iloc[start_idx:end_idx].copy()
            
            # Create train/test split
            train_df, test_df = train_test_split(subset, test_size=0.2, random_state=42)
            
            # Create metadata
            metadata = {
                'time_range': {
                    'start': subset['timestamp'].min().strftime('%Y-%m-%d'),
                    'end': subset['timestamp'].max().strftime('%Y-%m-%d')
                },
                'rating_distribution': subset['rating'].value_counts().to_dict(),
                'genre_distribution': subset['genres'].str.get_dummies(sep='|').sum().to_dict(),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Store in database
            self.store_subset_in_db(train_df, i+1, 'train', metadata)
            self.store_subset_in_db(test_df, i+1, 'test', metadata)
            
            # Also save to files for backup
            subset_dir = os.path.join(self.processed_data_path, 'subsets', f'subset_{i+1}')
            os.makedirs(subset_dir, exist_ok=True)
            
            train_df.to_csv(os.path.join(subset_dir, 'train.csv'), index=False)
            test_df.to_csv(os.path.join(subset_dir, 'test.csv'), index=False)
            
            subsets.append({
                'subset_number': i+1,
                'train': train_df,
                'test': test_df,
                'metadata': metadata
            })
            
            logger.info(f"Created subset {i+1}:")
            logger.info(f"  Time range: {metadata['time_range']['start']} to {metadata['time_range']['end']}")
            logger.info(f"  Train samples: {len(train_df)}")
            logger.info(f"  Test samples: {len(test_df)}")
        
        return subsets

def main():
    try:
        logger.info("Starting subset creation process...")
        
        # Create SubsetManager instance
        subset_manager = SubsetManager()
        
        # Load data from database
        df = subset_manager.load_data_from_db()
        
        # Create time-based subsets
        subsets = subset_manager.create_time_based_subsets(df)
        
        logger.info("Subset creation process completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during subset creation: {str(e)}")
        raise

if __name__ == "__main__":
    main()
