import pytest
from src.data.database import get_session, Movie, Rating, User
from sqlalchemy import func

def test_database_connection():
    session = get_session()
    assert session is not None

def test_movie_table():
    session = get_session()
    movie_count = session.query(func.count(Movie.movieId)).scalar()
    assert movie_count > 0

def test_rating_table():
    session = get_session()
    rating_count = session.query(func.count(Rating.id)).scalar()
    assert rating_count > 0

def test_user_table():
    session = get_session()
    user_count = session.query(func.count(User.id)).scalar()
    assert user_count > 0
