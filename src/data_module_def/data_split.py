import os

import pandas as pd

from src.entity import DataSplitConfig


class DataSplit:
    def __init__(self, config: DataSplitConfig):
        self.config = config

    def get_start_end_year(
        self,
    ):
        ratings = pd.read_csv(f"{self.config.root_dir}/{self.config.rating_filename}")

        # Format Unix-timestamp to datetime
        ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")
        ratings["year"] = ratings["timestamp"].dt.year

        start_year = ratings["year"].min()
        end_year = ratings["year"].max()

        return start_year, end_year

    def split_dataset(self, df, start_year, end_year, dir):
        while start_year <= end_year:
            next_start_year = start_year + self.config.step

            tmp_df = df[(df["year"] >= start_year) & (df["year"] <= next_start_year)]
            tmp_df = tmp_df.drop(columns=["year"])

            if not os.path.exists(f"{self.config.target_dir}/{dir}"):
                os.makedirs(f"{self.config.target_dir}/{dir}")

            tmp_df.to_csv(
                f"{self.config.target_dir}/{dir}/{dir}_{start_year}_{next_start_year}.csv",
                index=False,
            )
            start_year += self.config.step + 1

    def split_ratings(self, start_year, end_year):
        """Splits ratings into time intervals based on the timestamp column.

        Args:
            input_filepath (_type_): path to raw data directory
            output_filepath (_type_): path to interim data directory
        """

        ratings = pd.read_csv(f"{self.config.root_dir}/{self.config.rating_filename}")

        # Format Unix-timestamp to datetime
        ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")
        ratings["year"] = ratings["timestamp"].dt.year

        splitted = self.split_dataset(
            ratings, start_year, end_year, self.config.rating_filename.split(".")[0]
        )
        return splitted

    def split_movies(self, start_year, end_year):
        """Splits movies into time intervals.

        Args:
            input_filepath (_type_): path to raw data directory
            output_filepath (_type_): path to interim data directory
        """
        movies = pd.read_csv(f"{self.config.root_dir}/{self.config.movie_filename}")

        # Extract the year from the title
        movies["year"] = movies["title"].str.extract("\((\d{4})\)")
        movies["year"] = pd.to_numeric(movies["year"])

        splitted = self.split_dataset(
            movies, start_year, end_year, self.config.movie_filename.split(".")[0]
        )
        return splitted

    def split_data(self):
        start_year, end_year = self.get_start_end_year()

        self.split_ratings(start_year, end_year)
        self.split_movies(start_year, end_year)
