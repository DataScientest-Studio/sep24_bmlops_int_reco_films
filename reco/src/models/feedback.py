from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import logging
from typing import Optional, List, Dict

Base = declarative_base()
logger = logging.getLogger(__name__)

class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Add constraint to ensure rating is between 0 and 5
    __table_args__ = (
        CheckConstraint('rating >= 0 AND rating <= 5', name='check_rating_range'),
    )

    @classmethod
    def submit_feedback(cls, session, user_id: int, movie_id: int, rating: float) -> Optional['Feedback']:
        """Submit user feedback with star rating (0-5)."""
        try:
            # Validate rating range
            if not 0 <= rating <= 5:
                logger.error(f"Invalid rating value: {rating}. Must be between 0 and 5.")
                return None

            feedback = cls(
                user_id=user_id,
                movie_id=movie_id,
                rating=rating
            )
            session.add(feedback)
            session.commit()
            logger.info(f"Feedback submitted: User {user_id}, Movie {movie_id}, Rating {rating} stars")
            return feedback

        except Exception as e:
            session.rollback()
            logger.error(f"Error submitting feedback: {str(e)}")
            return None

    @classmethod
    def get_user_feedback(cls, session, user_id: int) -> List[Dict]:
        """Get all feedback for a specific user."""
        try:
            feedbacks = session.query(cls).filter_by(user_id=user_id).all()
            return [
                {
                    'movie_id': f.movie_id,
                    'rating': f.rating,
                    'timestamp': f.timestamp.isoformat()
                }
                for f in feedbacks
            ]
        except Exception as e:
            logger.error(f"Error retrieving user feedback: {str(e)}")
            return []

    @classmethod
    def get_movie_feedback(cls, session, movie_id: int) -> Dict:
        """Get aggregated feedback for a specific movie."""
        try:
            feedbacks = session.query(cls).filter_by(movie_id=movie_id).all()
            ratings = [f.rating for f in feedbacks]
            
            if not ratings:
                return {
                    'movie_id': movie_id,
                    'average_rating': None,
                    'total_ratings': 0
                }

            return {
                'movie_id': movie_id,
                'average_rating': sum(ratings) / len(ratings),
                'total_ratings': len(ratings)
            }
        except Exception as e:
            logger.error(f"Error retrieving movie feedback: {str(e)}")
            return {
                'movie_id': movie_id,
                'average_rating': None,
                'total_ratings': 0
            }

    @classmethod
    def get_recent_feedback(cls, session, limit: int = 100) -> List[Dict]:
        """Get most recent feedback entries."""
        try:
            feedbacks = (session.query(cls)
                        .order_by(cls.timestamp.desc())
                        .limit(limit)
                        .all())
            return [
                {
                    'user_id': f.user_id,
                    'movie_id': f.movie_id,
                    'rating': f.rating,
                    'timestamp': f.timestamp.isoformat()
                }
                for f in feedbacks
            ]
        except Exception as e:
            logger.error(f"Error retrieving recent feedback: {str(e)}")
            return []

    @classmethod
    def get_feedback_stats(cls, session) -> Dict:
        """Get overall feedback statistics."""
        try:
            result = session.query(
                func.count(cls.id).label('total_feedbacks'),
                func.avg(cls.rating).label('average_rating'),
                func.count(func.distinct(cls.user_id)).label('unique_users'),
                func.count(func.distinct(cls.movie_id)).label('unique_movies')
            ).first()

            return {
                'total_feedbacks': result.total_feedbacks,
                'average_rating': float(result.average_rating) if result.average_rating else None,
                'unique_users': result.unique_users,
                'unique_movies': result.unique_movies
            }
        except Exception as e:
            logger.error(f"Error retrieving feedback stats: {str(e)}")
            return {
                'total_feedbacks': 0,
                'average_rating': None,
                'unique_users': 0,
                'unique_movies': 0
            } 