import pandas as pd
from src.data.database import Feedback, get_session, UserFeedback
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import os

FEEDBACK_FILE = 'data/feedback/user_feedback.csv'

logger = logging.getLogger(__name__)

def collect_user_feedback(user_id, movie_id, rating):
    """
    Collects and stores user feedback in the database.

    Args:
        user_id (int): ID of the user providing feedback.
        movie_id (int): ID of the movie being rated.
        rating (float): User's rating for the movie (0-5 scale).
    """
    session = get_session()
    try:
        feedback = Feedback(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=datetime.utcnow())
        session.add(feedback)
        session.commit()
        return True
    except Exception as e:
        print(f"Error collecting user feedback: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_user_feedback():
    """
    Retrieves all stored user feedback from the database.

    Returns:
        pd.DataFrame: DataFrame containing all user feedback.
    """
    session = get_session()
    feedback = pd.read_sql(session.query(Feedback).statement, session.bind)
    session.close()
    return feedback

def clear_feedback():
    """
    Clears all stored user feedback.
    """
    if os.path.exists(FEEDBACK_FILE):
        os.remove(FEEDBACK_FILE)
        print("All user feedback has been cleared.")
    else:
        print("No feedback file found.")

def get_user_feedback(user_id):
    """
    Retrieves user feedback for a specific user.

    Args:
        user_id (int): ID of the user.

    Returns:
        list: List of dictionaries containing user feedback.
    """
    session = get_session()
    try:
        feedback = session.query(Feedback).filter(Feedback.user_id == user_id).all()
        return [{'movie_id': f.movie_id, 'rating': f.rating, 'timestamp': f.timestamp} for f in feedback]
    except Exception as e:
        print(f"Error retrieving user feedback: {e}")
        return []
    finally:
        session.close()

def add_user_feedback(session: Session, user_id: int, movie_id: int, rating: float):
    logger.info(f"Adding feedback for user {user_id} on movie {movie_id}")
    feedback = UserFeedback(userId=user_id, movieId=movie_id, rating=rating)
    session.add(feedback)
    session.commit()
    logger.info("Feedback added successfully")

def get_user_feedback(session: Session, user_id: int):
    logger.info(f"Retrieving feedback for user {user_id}")
    feedback = session.query(UserFeedback).filter(UserFeedback.userId == user_id).all()
    return feedback
