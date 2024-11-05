import os
import sys
import pandas as pd
import numpy as np
from tqdm import tqdm
import logging
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.data.database import get_session, Movie, Rating, User, Link, Tag, GenomeScore, GenomeTag, UserPreference, MovieFeature
from sqlalchemy.exc import IntegrityError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_movies(file_path):
    df = pd.read_csv(file_path)
    session = get_session()
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading movies"):
        movie = Movie(movieId=row['movieId'], title=row['title'], genres=row['genres'])
        try:
            session.add(movie)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"Movie {row['movieId']} already exists. Skipping.")
    session.close()

def load_ratings(file_path):
    df = pd.read_csv(file_path)
    session = get_session()
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading ratings"):
        rating = Rating(userId=row['userId'], movieId=row['movieId'], rating=row['rating'], timestamp=pd.to_datetime(row['timestamp'], unit='s'))
        try:
            session.add(rating)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"Rating for user {row['userId']} and movie {row['movieId']} already exists. Skipping.")
    session.close()

def load_users(file_path):
    df = pd.read_csv(file_path)
    session = get_session()
    for _, row in df.iterrows():
        user = User(id=row['userId'], username=f"user_{row['userId']}", email=f"user_{row['userId']}@example.com", hashed_password="dummy_hash")
        try:
            session.add(user)
            session.commit()
        except IntegrityError:
            session.rollback()
            print(f"User {row['userId']} already exists. Skipping.")
    session.close()

def load_links(file_path):
    df = pd.read_csv(file_path)
    session = get_session()
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading links"):
        link = Link(movieId=row['movieId'], imdbId=row['imdbId'], tmdbId=row['tmdbId'])
        try:
            session.add(link)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"Link for movie {row['movieId']} already exists. Skipping.")
    session.close()

def load_tags(file_path):
    df = pd.read_csv(file_path)
    session = get_session()
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading tags"):
        tag = Tag(userId=row['userId'], movieId=row['movieId'], tag=row['tag'], timestamp=pd.to_datetime(row['timestamp'], unit='s'))
        try:
            session.add(tag)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"Tag for user {row['userId']} and movie {row['movieId']} already exists. Skipping.")
    session.close()

def load_genome_scores(file_path):
    df = pd.read_csv(file_path)
    session = get_session()
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading genome scores"):
        genome_score = GenomeScore(movieId=row['movieId'], tagId=row['tagId'], relevance=row['relevance'])
        try:
            session.add(genome_score)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"Genome score for movie {row['movieId']} and tag {row['tagId']} already exists. Skipping.")
    session.close()

def load_genome_tags(file_path):
    df = pd.read_csv(file_path)
    session = get_session()
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading genome tags"):
        genome_tag = GenomeTag(tagId=row['tagId'], tag=row['tag'])
        try:
            session.add(genome_tag)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"Genome tag {row['tagId']} already exists. Skipping.")
    session.close()

def create_user_features(ratings_df, n_components=20):
    user_item_matrix = ratings_df.pivot(index='userId', columns='movieId', values='rating').fillna(0)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    user_features = svd.fit_transform(user_item_matrix)
    return pd.DataFrame(user_features, index=user_item_matrix.index)

def create_movie_features(movies_df, n_components=20):
    tfidf = TfidfVectorizer(stop_words='english')
    movie_genres = tfidf.fit_transform(movies_df['genres'])
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    movie_features = svd.fit_transform(movie_genres)
    return pd.DataFrame(movie_features, index=movies_df['movieId'])

def load_user_features(user_features_df):
    session = get_session()
    for user_id, features in tqdm(user_features_df.iterrows(), total=len(user_features_df), desc="Loading user features"):
        user_preference = UserPreference(userId=user_id, preferences=json.dumps(features.tolist()))
        try:
            session.add(user_preference)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"User features for user {user_id} already exist. Skipping.")
    session.close()

def load_movie_features(movie_features_df):
    session = get_session()
    for movie_id, features in tqdm(movie_features_df.iterrows(), total=len(movie_features_df), desc="Loading movie features"):
        movie_feature = MovieFeature(movieId=movie_id, features=json.dumps(features.tolist()))
        try:
            session.add(movie_feature)
            session.commit()
        except IntegrityError:
            session.rollback()
            logger.warning(f"Movie features for movie {movie_id} already exist. Skipping.")
    session.close()

if __name__ == "__main__":
    data_dir = os.path.join(project_root, 'src', 'data', 'raw')
    
    # Load basic data
    load_movies(os.path.join(data_dir, 'movies.csv'))
    load_ratings(os.path.join(data_dir, 'ratings.csv'))
    load_links(os.path.join(data_dir, 'links.csv'))
    load_tags(os.path.join(data_dir, 'tags.csv'))
    load_genome_scores(os.path.join(data_dir, 'genome-scores.csv'))
    load_genome_tags(os.path.join(data_dir, 'genome-tags.csv'))
    
    # Create and load user features
    ratings_df = pd.read_csv(os.path.join(data_dir, 'ratings.csv'))
    user_features_df = create_user_features(ratings_df)
    load_user_features(user_features_df)
    
    # Create and load movie features
    movies_df = pd.read_csv(os.path.join(data_dir, 'movies.csv'))
    movie_features_df = create_movie_features(movies_df)
    load_movie_features(movie_features_df)
    
    # Load users
    users_file = os.path.join(data_dir, 'users.csv')
    if not os.path.exists(users_file):
        users_df = ratings_df[['userId']].drop_duplicates()
        users_df.to_csv(users_file, index=False)
    load_users(users_file)
    
    print("All data, including feature matrices, loaded successfully.")
