from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from src.data.database import Movie, Rating, UserPreference
from src.models.collaborative_filtering import CollaborativeFiltering

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.cf_model = CollaborativeFiltering()
        self._load_model_data()

    def _load_model_data(self):
        """Load necessary data for recommendations"""
        try:
            # Load ratings
            ratings_query = self.db.query(Rating).all()
            self.ratings_df = pd.DataFrame([
                {
                    'userId': r.userId,
                    'movieId': r.movieId,
                    'rating': r.rating,
                    'timestamp': r.timestamp
                } for r in ratings_query
            ])
            
            # Train model if we have data
            if not self.ratings_df.empty:
                self.cf_model.fit(self.ratings_df)
                logger.info("Model trained successfully")
            else:
                logger.warning("No ratings data available for training")
                
        except Exception as e:
            logger.error(f"Error loading model data: {str(e)}")
            raise

    def get_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10,
        exclude_rated: bool = True
    ) -> List[Dict]:
        """Get movie recommendations for a user"""
        try:
            # Get user's rated movies if we want to exclude them
            rated_movies = set()
            if exclude_rated:
                rated_movies = set(
                    self.ratings_df[self.ratings_df['userId'] == user_id]['movieId']
                )
            
            # Get recommendations
            recommended_movie_ids = self.cf_model.recommend(user_id, n_recommendations)
            
            # Filter out rated movies
            recommended_movie_ids = [
                mid for mid in recommended_movie_ids if mid not in rated_movies
            ]
            
            # Get movie details
            movies = self.db.query(Movie).filter(
                Movie.movieId.in_(recommended_movie_ids)
            ).all()
            
            # Create response
            recommendations = []
            for movie in movies:
                # Get average rating
                avg_rating = self.ratings_df[
                    self.ratings_df['movieId'] == movie.movieId
                ]['rating'].mean()
                
                recommendations.append({
                    'movieId': movie.movieId,
                    'title': movie.title,
                    'genres': movie.genres,
                    'averageRating': float(avg_rating) if not np.isnan(avg_rating) else None,
                    'recommendedAt': datetime.utcnow().isoformat()
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise

    def get_similar_movies(
        self,
        movie_id: int,
        n_similar: int = 10
    ) -> List[Dict]:
        """Get similar movies based on a movie ID"""
        try:
            # Get similar movie IDs
            similar_movie_ids = self.cf_model.get_similar_movies(movie_id, n_similar)
            
            # Get movie details
            movies = self.db.query(Movie).filter(
                Movie.movieId.in_(similar_movie_ids)
            ).all()
            
            # Create response
            similar_movies = []
            for movie in movies:
                avg_rating = self.ratings_df[
                    self.ratings_df['movieId'] == movie.movieId
                ]['rating'].mean()
                
                similar_movies.append({
                    'movieId': movie.movieId,
                    'title': movie.title,
                    'genres': movie.genres,
                    'averageRating': float(avg_rating) if not np.isnan(avg_rating) else None
                })
            
            return similar_movies
            
        except Exception as e:
            logger.error(f"Error getting similar movies: {str(e)}")
            raise

    def update_user_preferences(
        self,
        user_id: int,
        preferences: Dict
    ) -> None:
        """Update user preferences"""
        try:
            user_pref = self.db.query(UserPreference).filter(
                UserPreference.userId == user_id
            ).first()
            
            if user_pref:
                user_pref.preferences = preferences
            else:
                user_pref = UserPreference(
                    userId=user_id,
                    preferences=preferences
                )
                self.db.add(user_pref)
            
            self.db.commit()
            logger.info(f"Updated preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            self.db.rollback()
            raise 