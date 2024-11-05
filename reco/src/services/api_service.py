from typing import List, Dict, Optional
from fastapi import HTTPException, status
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.collaborative_filtering import CollaborativeFilteringModel
from src.data.database import Movie, Rating, User, UserPreference
from src.services.cache_service import CacheService
from src.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)

class APIService:
    def __init__(self, db: Session, model_path: str):
        self.db = db
        self.model = CollaborativeFilteringModel(model_path)
        self.cache = CacheService()
        self.metrics = MetricsService(db)
        
    async def get_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10,
        include_metadata: bool = True
    ) -> List[Dict]:
        """Get movie recommendations for a user."""
        try:
            # Check cache first
            cache_key = f"recommendations:{user_id}:{n_recommendations}"
            cached_recommendations = await self.cache.get(cache_key)
            if cached_recommendations:
                return cached_recommendations
            
            # Generate recommendations
            start_time = datetime.utcnow()
            recommendations = self.model.recommend(user_id, n_recommendations)
            
            # Enrich with metadata if requested
            if include_metadata:
                recommendations = self._enrich_recommendations(recommendations)
            
            # Log metrics
            end_time = datetime.utcnow()
            self.metrics.log_recommendation_request(
                user_id=user_id,
                recommendations=recommendations,
                latency=(end_time - start_time).total_seconds()
            )
            
            # Cache results
            await self.cache.set(cache_key, recommendations, expire=3600)  # 1 hour
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating recommendations"
            )
            
    def _enrich_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Add metadata to recommendations."""
        movie_ids = [rec['movieId'] for rec in recommendations]
        movies = (self.db.query(Movie)
                 .filter(Movie.movieId.in_(movie_ids))
                 .all())
        
        movie_data = {
            movie.movieId: {
                'title': movie.title,
                'genres': movie.genres,
                'year': movie.year
            } for movie in movies
        }
        
        for rec in recommendations:
            rec.update(movie_data.get(rec['movieId'], {}))
            
        return recommendations
    
    async def submit_feedback(
        self,
        user_id: int,
        movie_id: int,
        rating: float,
        feedback_type: str = 'explicit'
    ) -> Dict:
        """Submit user feedback for a movie."""
        try:
            # Store feedback
            feedback = Rating(
                userId=user_id,
                movieId=movie_id,
                rating=rating,
                timestamp=datetime.utcnow()
            )
            self.db.add(feedback)
            
            # Log metrics
            self.metrics.log_user_feedback(
                user_id=user_id,
                movie_id=movie_id,
                rating=rating,
                feedback_type=feedback_type
            )
            
            # Invalidate cache
            await self.cache.delete(f"recommendations:{user_id}:*")
            
            self.db.commit()
            return {"status": "success", "message": "Feedback submitted successfully"}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error submitting feedback: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error submitting feedback"
            )
            
    async def get_user_preferences(
        self,
        user_id: int
    ) -> Dict:
        """Get user preferences and statistics."""
        try:
            # Get user preferences
            preferences = (self.db.query(UserPreference)
                         .filter_by(userId=user_id)
                         .first())
            
            # Get user statistics
            ratings = (self.db.query(Rating)
                      .filter_by(userId=user_id)
                      .all())
            
            stats = {
                'total_ratings': len(ratings),
                'average_rating': sum(r.rating for r in ratings) / len(ratings) if ratings else 0,
                'last_activity': max(r.timestamp for r in ratings) if ratings else None
            }
            
            return {
                'preferences': preferences.preferences if preferences else {},
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user preferences"
            )
            
    def close(self):
        """Close database session."""
        self.db.close() 