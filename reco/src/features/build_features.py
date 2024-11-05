"""
This module handles feature engineering for the movie recommendation system.
"""

import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import csr_matrix, save_npz
from src.data.database import Movie, Rating, get_session
from sqlalchemy import func

def read_ratings(ratings_csv, data_dir="data/raw") -> pd.DataFrame:
    """
    Reads a ratings.csv from the data/raw folder.

    Parameters
    -------
    ratings_csv : str
        The csv file that will be read. Must be corresponding to a rating file.

    Returns
    -------
    pd.DataFrame
        The ratings DataFrame. Its columns are, in order:
        "userId", "movieId", "rating" and "timestamp".
    """
    data = pd.read_csv(os.path.join(data_dir, ratings_csv))

    temp = pd.DataFrame(LabelEncoder().fit_transform(data["movieId"]))
    data["movieId"] = temp
    return data


def read_movies(movies_csv, data_dir="data/raw") -> pd.DataFrame:
    """
    Reads a movies.csv from the data/raw folder.

    Parameters
    -------
    movies_csv : str
        The csv file that will be read. Must be corresponding to a movie file.

    Returns
    -------
    pd.DataFrame
        The movies DataFrame. Its columns are binary and represent the movie genres.
    """
    # Read the CSV file
    df = pd.read_csv(os.path.join(data_dir, movies_csv))

    # Split the 'genres' column into individual genres
    genres = df["genres"].str.get_dummies(sep="|")

    # Concatenate the original movieId and title columns with the binary genre columns
    result_df = pd.concat([df[["movieId", "title"]], genres], axis=1)
    return result_df


def create_user_matrix():
    session = get_session()
    user_matrix = pd.read_sql(
        session.query(
            Rating.userId,
            func.avg(Rating.rating).label('avg_rating'),
            func.count(Rating.movieId).label('movie_count')
        ).group_by(Rating.userId).statement,
        session.bind
    )
    session.close()
    return user_matrix.set_index('userId')


def create_movie_matrix():
    session = get_session()
    movie_matrix = pd.read_sql(
        session.query(Movie).statement,
        session.bind
    )
    session.close()
    return movie_matrix.set_index('movieId')


def create_sparse_rating_matrix():
    session = get_session()
    ratings = pd.read_sql(
        session.query(Rating.userId, Rating.movieId, Rating.rating).statement,
        session.bind
    )
    session.close()

    users = ratings['userId'].unique()
    movies = ratings['movieId'].unique()
    user_to_index = {user: index for index, user in enumerate(users)}
    movie_to_index = {movie: index for index, movie in enumerate(movies)}
    
    row = ratings['userId'].map(user_to_index)
    col = ratings['movieId'].map(movie_to_index)
    data = ratings['rating']
    
    sparse_matrix = csr_matrix((data, (row, col)), shape=(len(users), len(movies)))
    return sparse_matrix, user_to_index, movie_to_index


def main():
    # Ensure the processed directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    # Create and save user matrix
    if not os.path.exists("data/processed/user_matrix.csv"):
        try:
            user_matrix = create_user_matrix()
            user_matrix.to_csv("data/processed/user_matrix.csv")
            print("User matrix created and saved successfully.")
        except Exception as e:
            print(f"Error creating user matrix: {str(e)}")
            return
    else:
        print("User matrix already exists. Skipping creation.")
    
    # Create and save movie matrix
    if not os.path.exists("data/processed/movie_matrix.csv"):
        try:
            movie_matrix = create_movie_matrix()
            movie_matrix.to_csv("data/processed/movie_matrix.csv", index=False)
            print("Movie matrix created and saved successfully.")
        except Exception as e:
            print(f"Error creating movie matrix: {str(e)}")
            return
    else:
        print("Movie matrix already exists. Skipping creation.")
    
    # Create sparse rating matrix
    if not os.path.exists("data/processed/sparse_rating_matrix.npz"):
        try:
            sparse_rating_matrix, user_to_index, movie_to_index = create_sparse_rating_matrix()
            save_npz("data/processed/sparse_rating_matrix.npz", sparse_rating_matrix)
            pd.DataFrame.from_dict(user_to_index, orient='index', columns=['index']).to_csv("data/processed/user_to_index.csv")
            pd.DataFrame.from_dict(movie_to_index, orient='index', columns=['index']).to_csv("data/processed/movie_to_index.csv")
            print("Sparse rating matrix and index mappings created and saved successfully.")
        except Exception as e:
            print(f"Error creating sparse rating matrix: {str(e)}")
            return
    else:
        print("Sparse rating matrix already exists. Skipping creation.")
    
    print("All matrices and mappings processed successfully.")

if __name__ == "__main__":
    main()
