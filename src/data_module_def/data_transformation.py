import os

import pandas as pd
from sklearn.preprocessing import LabelEncoder

from src.entity import DataTransformationConfig


class DataTransformation:
    def __init__(self, config: DataTransformationConfig):
        self.config = config

    def read_ratings(self) -> pd.DataFrame:
        """
        Reads a ratings.csv from the data/interim folder.

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
        data = pd.read_csv(
            os.path.join(self.config.root_dir, self.config.rating_filename)
        )

        temp = pd.DataFrame(LabelEncoder().fit_transform(data["movieId"]))
        data["movieId"] = temp
        return data

    def read_movies(self) -> pd.DataFrame:
        """
        Reads a movies.csv from the data/interim folder.

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
        df = pd.read_csv(os.path.join(self.config.root_dir, self.config.movie_filename))

        # Split the 'genres' column into individual genres
        genres = df["genres"].str.get_dummies(sep="|")

        # Concatenate the original movieId and title columns with the binary genre columns
        result_df = pd.concat([df[["movieId", "title"]], genres], axis=1)
        return result_df

    def create_user_matrix(self, ratings, movies):
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

    def build_features(self):
        # read user_ratings and movies tables
        user_ratings = self.read_ratings()
        movies = self.read_movies()
        user_matrix = self.create_user_matrix(user_ratings, movies)
        movies = movies.drop("title", axis=1)
        movies.to_csv(
            f"{self.config.target_dir}/{self.config.movie_output_filename}", index=False
        )
        user_matrix.to_csv(
            f"{self.config.target_dir}/{self.config.rating_output_filename}"
        )
