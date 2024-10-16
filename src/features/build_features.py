import os

import pandas as pd
from sklearn.preprocessing import LabelEncoder


def read_ratings(
    ratings_csv,
    ti_max,
    data_dir="data/raw",
) -> pd.DataFrame:
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


def read_movies(
    movies_csv,
    ti_max,
    data_dir="data/raw",
) -> pd.DataFrame:
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


def create_user_matrix(ratings, movies):
    # merge the 2 tables together
    movie_ratings = ratings.merge(movies, on="movieId", how="inner")

    # Drop useless features
    movie_ratings = movie_ratings.drop(
        ["movieId", "timestamp", "title", "rating"], axis=1
    )

    # Calculate user_matrix
    user_matrix = movie_ratings.groupby("userId").agg(
        "mean",
    )

    return user_matrix


if __name__ == "__main__":
    ti_max = 1

    # read user_ratings and movies tables
    user_ratings = read_ratings("ratings.csv", ti_max=ti_max)
    movies = read_movies("movies.csv", ti_max=ti_max)
    user_matrix = create_user_matrix(user_ratings, movies)
    movies = movies.drop("title", axis=1)
    movies.to_csv("data/processed/movie_matrix_TI1.csv", index=False)
    user_matrix.to_csv("data/processed/user_matrix_TI1.csv")
