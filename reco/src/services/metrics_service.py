from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Define Prometheus metrics
RECOMMENDATION_REQUESTS = Counter(
    'recommendation_requests_total',
    'Total number of recommendation requests',
    ['user_id']
)

RECOMMENDATION_LATENCY = Histogram(
    'recommendation_latency_seconds',
    'Time taken to generate recommendations',
    ['user_id']
)

USER_SATISFACTION = Gauge(
    'user_satisfaction_score',
    'Average user satisfaction score',
    ['user_id']
)

class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def log_recommendation_request(
        self,
        user_id: int,
        recommendations: List[Dict],
        latency: float
    ) -> None:
        """Log a recommendation request"""
        try:
            # Increment request counter
            RECOMMENDATION_REQUESTS.labels(user_id=str(user_id)).inc()
            
            # Record latency
            RECOMMENDATION_LATENCY.labels(user_id=str(user_id)).observe(latency)
            
            # Store in database for analysis
            for rec in recommendations:
                recommendation_log = RecommendationLog(
                    userId=user_id,
                    movieId=rec['movieId'],
                    timestamp=datetime.utcnow(),
                    latency=latency
                )
                self.db.add(recommendation_log)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging recommendation request: {str(e)}")
            self.db.rollback()

    def log_user_feedback(
        self,
        user_id: int,
        movie_id: int,
        rating: float,
        feedback_type: str
    ) -> None:
        """Log user feedback"""
        try:
            # Update satisfaction score
            USER_SATISFACTION.labels(user_id=str(user_id)).set(rating)
            
            # Store feedback
            feedback = UserFeedback(
                userId=user_id,
                movieId=movie_id,
                rating=rating,
                feedbackType=feedback_type,
                timestamp=datetime.utcnow()
            )
            self.db.add(feedback)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging user feedback: {str(e)}")
            self.db.rollback()

    def get_user_metrics(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict:
        """Get metrics for a specific user"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recommendation stats
            rec_stats = pd.read_sql(
                self.db.query(RecommendationLog)
                .filter(
                    RecommendationLog.userId == user_id,
                    RecommendationLog.timestamp >= start_date
                ).statement,
                self.db.bind
            )
            
            # Get feedback stats
            feedback_stats = pd.read_sql(
                self.db.query(UserFeedback)
                .filter(
                    UserFeedback.userId == user_id,
                    UserFeedback.timestamp >= start_date
                ).statement,
                self.db.bind
            )
            
            return {
                'total_recommendations': len(rec_stats),
                'average_latency': float(rec_stats['latency'].mean()),
                'total_feedback': len(feedback_stats),
                'average_rating': float(feedback_stats['rating'].mean()),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting user metrics: {str(e)}")
            raise

    def get_system_metrics(
        self,
        days: int = 30
    ) -> Dict:
        """Get overall system metrics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get overall stats
            rec_stats = pd.read_sql(
                self.db.query(RecommendationLog)
                .filter(RecommendationLog.timestamp >= start_date)
                .statement,
                self.db.bind
            )
            
            feedback_stats = pd.read_sql(
                self.db.query(UserFeedback)
                .filter(UserFeedback.timestamp >= start_date)
                .statement,
                self.db.bind
            )
            
            return {
                'total_recommendations': len(rec_stats),
                'unique_users': len(rec_stats['userId'].unique()),
                'average_latency': float(rec_stats['latency'].mean()),
                'total_feedback': len(feedback_stats),
                'average_rating': float(feedback_stats['rating'].mean()),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            raise 