"""
This module handles the processing of raw data files for the movie recommendation system.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.data.database import (
    Movie, Rating, Link, Tag, GenomeScore, GenomeTag, 
    User, UserPreference, MovieFeature, Feedback, 
    init_db, get_session
)
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import os
import time
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_csv(file_name, data_dir="data/raw"):
    return pd.read_csv(os.path.join(data_dir, file_name))

def extract_year(title):
    import re
    match = re.search(r'\((\d{4})\)$', title)
    return int(match.group(1)) if match else None

def load_existing_features(processed_data_path: str):
    """Load existing feature matrices from processed data directory."""
    user_matrix_path = os.path.join(processed_data_path, 'user_matrix.csv')
    movie_matrix_path = os.path.join(processed_data_path, 'movie_matrix.csv')
    
    user_features = pd.read_csv(user_matrix_path) if os.path.exists(user_matrix_path) else None
    movie_features = pd.read_csv(movie_matrix_path) if os.path.exists(movie_matrix_path) else None
    
    return user_features, movie_features

def store_features_in_db(session: Session, user_features: pd.DataFrame, movie_features: pd.DataFrame):
    """Store the feature matrices in the database."""
    logger.info("Storing user features in database...")
    if user_features is not None:
        for _, row in user_features.iterrows():
            user_id = row['userId'] if 'userId' in row else None
            if user_id:
                features = row.drop('userId' if 'userId' in row else []).to_dict()
                user_pref = UserPreference(
                    userId=user_id,
                    preferences=json.dumps(features)
                )
                session.merge(user_pref)
    
    logger.info("Storing movie features in database...")
    if movie_features is not None:
        for _, row in movie_features.iterrows():
            movie_id = row['movieId'] if 'movieId' in row else None
            if movie_id:
                features = row.drop('movieId' if 'movieId' in row else []).to_dict()
                movie_feature = MovieFeature(
                    movieId=movie_id,
                    features=json.dumps(features)
                )
                session.merge(movie_feature)
    
    session.commit()
    logger.info("Features stored successfully in database.")

def process_and_store_data(movies_file, ratings_file, links_file, tags_file, genome_tags_file, genome_scores_file):
    """Process and store all data including existing features."""
    session = get_session()
    processed_data_path = os.path.dirname(os.path.dirname(movies_file)) + '/processed'
    
    try:
        # First, process all users from ratings
        logger.info("Processing ratings to create users...")
        ratings_df = pd.read_csv(ratings_file)
        max_user_id = ratings_df['userId'].max()
        
        logger.info(f"Creating users (1 to {max_user_id})...")
        # Check existing users first
        existing_user_ids = {user[0] for user in session.query(User.id).all()}
        users = []
        for i in range(1, int(max_user_id) + 1):  # Convert max_user_id to int
            if i not in existing_user_ids:
                user = User(
                    id=i,
                    username=f"user_{i}",
                    email=f"user_{i}@example.com",
                    hashed_password="dummy_hash"
                )
                users.append(user)
        
        if users:
            session.bulk_save_objects(users)
            session.commit()
            logger.info(f"Created {len(users)} new users.")
        else:
            logger.info("No new users to create.")

        # Process movies
        logger.info("Processing movies...")
        movies_df = pd.read_csv(movies_file)
        for _, row in movies_df.iterrows():
            movie = Movie(
                movieId=int(row['movieId']),  # Convert to int
                title=str(row['title']),
                genres=str(row['genres']),
                year=extract_year(row['title'])
            )
            session.merge(movie)
        session.commit()
        logger.info(f"Processed {len(movies_df)} movies")

        # Process ratings with explicit type conversion
        logger.info("Processing ratings...")
        batch_size = 1000
        ratings = []
        
        for _, row in ratings_df.iterrows():
            rating = Rating(
                userId=int(row['userId']),      # Convert to int
                movieId=int(row['movieId']),    # Convert to int
                rating=float(row['rating']),    # Convert to float
                timestamp=datetime.fromtimestamp(int(row['timestamp']))  # Convert to int before timestamp
            )
            ratings.append(rating)
            
            # Process in batches to save memory
            if len(ratings) >= batch_size:
                session.bulk_save_objects(ratings)
                session.commit()
                ratings = []
        
        # Process any remaining ratings
        if ratings:
            session.bulk_save_objects(ratings)
            session.commit()
        
        logger.info(f"Processed {len(ratings_df)} ratings")

        # Process links
        logger.info("Processing links...")
        links_df = pd.read_csv(links_file)
        for _, row in links_df.iterrows():
            link = Link(
                movieId=int(row['movieId']),
                imdbId=str(row['imdbId']),  # Convert to string to preserve leading zeros
                tmdbId=str(row['tmdbId']) if pd.notna(row['tmdbId']) else None  # Handle potential NaN values
            )
            session.merge(link)
        session.commit()
        logger.info(f"Processed {len(links_df)} links")

        # Process tags
        logger.info("Processing tags...")
        tags_df = pd.read_csv(tags_file)
        for _, row in tags_df.iterrows():
            tag = Tag(
                userId=row['userId'],
                movieId=row['movieId'],
                tag=str(row['tag']),
                timestamp=datetime.fromtimestamp(row['timestamp'])
            )
            session.merge(tag)
        session.commit()
        logger.info(f"Processed {len(tags_df)} tags")

        # Process genome tags and scores
        logger.info("Processing genome tags and scores...")
        genome_tags_df = pd.read_csv(genome_tags_file)
        genome_scores_df = pd.read_csv(genome_scores_file)
        
        # Process genome tags with explicit type conversion
        for _, row in genome_tags_df.iterrows():
            genome_tag = GenomeTag(
                tagId=int(row['tagId']),  # Convert to int
                tag=str(row['tag'])       # Convert to str
            )
            session.merge(genome_tag)
        session.commit()
        
        # Process genome scores in batches with explicit type conversion
        batch_size = 1000
        genome_scores = []
        
        for _, row in genome_scores_df.iterrows():
            genome_score = GenomeScore(
                movieId=int(row['movieId']),  # Convert to int
                tagId=int(row['tagId']),      # Convert to int
                relevance=float(row['relevance'])  # Convert to float
            )
            genome_scores.append(genome_score)
            
            # Process in batches to save memory
            if len(genome_scores) >= batch_size:
                session.bulk_save_objects(genome_scores)
                session.commit()
                genome_scores = []
        
        # Process any remaining genome scores
        if genome_scores:
            session.bulk_save_objects(genome_scores)
            session.commit()
        
        logger.info(f"Processed {len(genome_tags_df)} genome tags and {len(genome_scores_df)} genome scores")

        # Load and store existing features
        logger.info("Loading existing feature matrices...")
        user_features, movie_features = load_existing_features(processed_data_path)
        if user_features is not None or movie_features is not None:
            store_features_in_db(session, user_features, movie_features)
        else:
            logger.warning("No existing feature matrices found in processed data directory")

    except Exception as e:
        logger.error(f"Error during data processing: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

    logger.info("All data processing and storage completed successfully!")

if __name__ == "__main__":
    # Define paths relative to the project root
    data_dir = "data/raw"
    movies_file = os.path.join(data_dir, "movies.csv")
    ratings_file = os.path.join(data_dir, "ratings.csv")
    links_file = os.path.join(data_dir, "links.csv")
    tags_file = os.path.join(data_dir, "tags.csv")
    genome_tags_file = os.path.join(data_dir, "genome-tags.csv")
    genome_scores_file = os.path.join(data_dir, "genome-scores.csv")
    
    process_and_store_data(
        movies_file, ratings_file, links_file, 
        tags_file, genome_tags_file, genome_scores_file
    )
