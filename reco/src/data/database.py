from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os
from dotenv import load_dotenv
from sqlalchemy.types import JSON
from datetime import datetime  # Add this import

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Movie(Base):
    __tablename__ = 'movies'

    movieId = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    genres = Column(String)
    year = Column(Integer)
    links = relationship("Link", back_populates="movie")

class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('users.id'))
    movieId = Column(Integer, ForeignKey('movies.movieId'))
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('users.id'))
    movieId = Column(Integer, ForeignKey('movies.movieId'))
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class UserPreference(Base):
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('users.id'))
    preferences = Column(String)  # JSON string of user preferences

class MovieFeature(Base):
    __tablename__ = 'movie_features'

    movieId = Column(Integer, primary_key=True)
    features = Column(String)  # Stored as a JSON string

class ModelEvaluation(Base):
    __tablename__ = 'model_evaluations'

    id = Column(Integer, primary_key=True)
    run_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    model_path = Column(String, nullable=False)
    rmse = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    precision_at_k = Column(Float, nullable=False)
    recall_at_k = Column(Float, nullable=False)
    ndcg_at_k = Column(Float, nullable=False)
    diversity = Column(Float, nullable=False)
    novelty = Column(Float, nullable=False)

class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    movieId = Column(Integer, ForeignKey('movies.movieId'))
    imdbId = Column(String)  # Changed from Integer to String to handle leading zeros
    tmdbId = Column(String)  # Changed from Integer to String
    movie = relationship("Movie", back_populates="links")

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('users.id'))
    movieId = Column(Integer, ForeignKey('movies.movieId'))
    tag = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class GenomeTag(Base):
    __tablename__ = 'genome_tags'

    tagId = Column(Integer, primary_key=True)
    tag = Column(String, nullable=False)

class GenomeScore(Base):
    __tablename__ = 'genome_scores'

    id = Column(Integer, primary_key=True)
    movieId = Column(Integer, ForeignKey('movies.movieId'))
    tagId = Column(Integer, ForeignKey('genome_tags.tagId'))
    relevance = Column(Float, nullable=False)

class TrainingSubset(Base):
    __tablename__ = 'training_subsets'
    
    id = Column(Integer, primary_key=True)
    subset_number = Column(Integer)
    subset_type = Column(String)  # 'train' or 'test'
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    time_range_start = Column(DateTime)
    time_range_end = Column(DateTime)
    n_samples = Column(Integer)
    n_users = Column(Integer)
    n_movies = Column(Integer)
    subset_metadata = Column(JSON)  # Changed from 'metadata' to 'subset_metadata'

def get_engine():
    DATABASE_URL = os.getenv("DATABASE_URL")
    return create_engine(DATABASE_URL, future=True)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine, future=True)
    return Session()

def check_data_exists():
    """Check if data already exists in the database."""
    session = get_session()
    try:
        movie_count = session.query(Movie).count()
        rating_count = session.query(Rating).count()
        user_count = session.query(User).count()
        return movie_count > 0 and rating_count > 0 and user_count > 0
    except Exception as e:
        print(f"Error checking data: {e}")
        return False
    finally:
        session.close()

def reset_database():
    """Reset the database by dropping and recreating all tables."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset completed.")

def init_db(force_reset=False):
    """Initialize the database and optionally reset it."""
    engine = get_engine()
    if force_reset:
        reset_database()
        return

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    required_tables = {'users', 'movies', 'ratings', 'feedback', 'user_preferences', 
                      'movie_features', 'model_evaluations', 'links', 'tags', 
                      'genome_tags', 'genome_scores'}
    
    if not required_tables.issubset(existing_tables):
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    else:
        print("Database tables exist. Checking data...")
        if not check_data_exists():
            print("Tables exist but no data found. Ready for data import.")
        else:
            print("Data already exists in the database.")

def add_training_subsets_table():
    """Add training_subsets table without affecting existing data."""
    engine = get_engine()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if 'training_subsets' not in existing_tables:
        # Only create the training_subsets table
        TrainingSubset.__table__.create(bind=engine)
        print("Training subsets table added successfully.")
    else:
        print("Training subsets table already exists.")

if __name__ == "__main__":
    init_db()
    add_training_subsets_table()
