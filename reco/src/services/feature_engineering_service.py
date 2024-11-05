from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import logging
from sqlalchemy.orm import Session
import json

from src.data.database import (
    Movie, Rating, Tag, GenomeScore, GenomeTag,
    MovieFeature, UserPreference, get_session
)

logger = logging.getLogger(__name__)

class FeatureEngineeringService:
    def __init__(self, db: Session = None):
        self.db = db or get_session()
        self.scaler = StandardScaler()
        
    def create_movie_features(self) -> pd.DataFrame:
        """Create movie features from various sources."""
        logger.info("Creating movie features...")
        
        try:
            # Get basic movie data
            movies_query = """
                SELECT m."movieId", m.title, m.genres,
                       AVG(r.rating) as avg_rating,
                       COUNT(r.rating) as rating_count
                FROM movies m
                LEFT JOIN ratings r ON m."movieId" = r."movieId"
                GROUP BY m."movieId", m.title, m.genres
            """
            movies_df = pd.read_sql(movies_query, self.db.bind)
            
            # Process genres using TF-IDF
            tfidf = TfidfVectorizer()
            genre_features = tfidf.fit_transform(movies_df['genres'].fillna(''))
            genre_features_df = pd.DataFrame(
                genre_features.toarray(),
                columns=[f'genre_{f}' for f in tfidf.get_feature_names_out()],
                index=movies_df['movieId']
            )
            
            # Get tag features
            tags_query = """
                SELECT t."movieId", 
                       string_agg(t.tag, ' ') as tags,
                       COUNT(*) as tag_count
                FROM tags t
                GROUP BY t."movieId"
            """
            tags_df = pd.read_sql(tags_query, self.db.bind)
            
            # Process tags using TF-IDF
            tag_tfidf = TfidfVectorizer(max_features=100)
            tag_features = tag_tfidf.fit_transform(tags_df['tags'].fillna(''))
            tag_features_df = pd.DataFrame(
                tag_features.toarray(),
                columns=[f'tag_{f}' for f in tag_tfidf.get_feature_names_out()],
                index=tags_df['movieId']
            )
            
            # Combine all features
            features_df = pd.concat([
                genre_features_df,
                tag_features_df
            ], axis=1).fillna(0)
            
            # Add rating statistics
            features_df['avg_rating'] = movies_df.set_index('movieId')['avg_rating']
            features_df['rating_count'] = movies_df.set_index('movieId')['rating_count']
            
            # Scale numerical features
            numerical_cols = ['avg_rating', 'rating_count']
            features_df[numerical_cols] = self.scaler.fit_transform(features_df[numerical_cols])
            
            # Store features in database
            self._store_movie_features(features_df)
            
            logger.info(f"Created features for {len(features_df)} movies")
            return features_df
            
        except Exception as e:
            logger.error(f"Error creating movie features: {str(e)}")
            raise
            
    def create_user_features(self) -> pd.DataFrame:
        """Create user features from their interactions."""
        logger.info("Creating user features...")
        
        try:
            # Get user rating patterns
            ratings_query = """
                SELECT r."userId",
                       AVG(r.rating) as avg_rating,
                       COUNT(*) as rating_count,
                       stddev(r.rating) as rating_std
                FROM ratings r
                GROUP BY r."userId"
            """
            ratings_df = pd.read_sql(ratings_query, self.db.bind)
            
            # Get genre preferences
            genre_prefs_query = """
                SELECT r."userId",
                       m.genres,
                       AVG(r.rating) as genre_avg_rating,
                       COUNT(*) as genre_count
                FROM ratings r
                JOIN movies m ON r."movieId" = m."movieId"
                GROUP BY r."userId", m.genres
            """
            genre_prefs_df = pd.read_sql(genre_prefs_query, self.db.bind)
            
            # Process genre preferences
            genre_pivot = genre_prefs_df.pivot_table(
                index='userId',
                columns='genres',
                values=['genre_avg_rating', 'genre_count'],
                fill_value=0
            )
            genre_pivot.columns = [f'{col[0]}_{col[1]}'.replace(' ', '_') 
                                 for col in genre_pivot.columns]
            
            # Combine features
            features_df = pd.concat([
                ratings_df.set_index('userId'),
                genre_pivot
            ], axis=1).fillna(0)
            
            # Scale numerical features
            numerical_cols = features_df.select_dtypes(include=[np.number]).columns
            features_df[numerical_cols] = self.scaler.fit_transform(features_df[numerical_cols])
            
            # Store features in database
            self._store_user_features(features_df)
            
            logger.info(f"Created features for {len(features_df)} users")
            return features_df
            
        except Exception as e:
            logger.error(f"Error creating user features: {str(e)}")
            raise
            
    def _store_movie_features(self, features_df: pd.DataFrame):
        """Store movie features in the database."""
        for movie_id, features in features_df.iterrows():
            movie_feature = MovieFeature(
                movieId=movie_id,
                features=json.dumps(features.to_dict())
            )
            self.db.merge(movie_feature)
        self.db.commit()
        
    def _store_user_features(self, features_df: pd.DataFrame):
        """Store user features in the database."""
        for user_id, features in features_df.iterrows():
            user_preference = UserPreference(
                userId=user_id,
                preferences=json.dumps(features.to_dict())
            )
            self.db.merge(user_preference)
        self.db.commit()
        
    def close(self):
        """Close the database session."""
        self.db.close() 