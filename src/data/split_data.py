import logging
import os

import click
import pandas as pd

from src.data.check_structure import check_existing_folder


def get_start_end_year(input_filepath):
    ratings = pd.read_csv(f"{input_filepath}/ratings.csv")

    # Format Unix-timestamp to datetime
    ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")
    ratings["year"] = ratings["timestamp"].dt.year

    start_year = ratings["year"].min()
    end_year = ratings["year"].max()

    return start_year, end_year


def split_dataset(df, start_year, end_year, step, output_filepath, file_indicator):
    while start_year <= end_year:
        next_start_year = start_year + step

        tmp_df = df[(df["year"] >= start_year) & (df["year"] <= next_start_year)]
        tmp_df = tmp_df.drop(columns=["year"])

        if check_existing_folder(f"{output_filepath}/{file_indicator}"):
            os.makedirs(f"{output_filepath}/{file_indicator}")

        tmp_df.to_csv(
            f"{output_filepath}/{file_indicator}/{file_indicator}_{start_year}_{next_start_year}.csv",
            index=False,
        )
        print(f"Saving {file_indicator} data from {start_year} to {next_start_year}")

        start_year += step + 1


def split_ratings(input_filepath, output_filepath, start_year, end_year, step):
    """Splits ratings into time intervals based on the timestamp column.

    Args:
        input_filepath (_type_): path to raw data directory
        output_filepath (_type_): path to interim data directory
    """

    ratings = pd.read_csv(f"{input_filepath}/ratings.csv")

    # Format Unix-timestamp to datetime
    ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")
    ratings["year"] = ratings["timestamp"].dt.year

    splitted = split_dataset(
        ratings, start_year, end_year, step, output_filepath, "ratings"
    )
    return splitted


def split_movies(input_filepath, output_filepath, start_year, end_year, step):
    """Splits movies into time intervals.

    Args:
        input_filepath (_type_): path to raw data directory
        output_filepath (_type_): path to interim data directory
    """
    movies = pd.read_csv(f"{input_filepath}/movies.csv")

    # Extract the year from the title
    movies["year"] = movies["title"].str.extract("\((\d{4})\)")
    movies["year"] = pd.to_numeric(movies["year"])

    splitted = split_dataset(
        movies, start_year, end_year, step, output_filepath, "movies"
    )
    return splitted


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
@click.argument("step", type=click.INT)
def main(input_filepath, output_filepath, step):
    logger = logging.getLogger(__name__)
    logger.info(f"split data into chunks of {step} years")

    start_year, end_year = get_start_end_year(input_filepath)

    split_ratings(input_filepath, output_filepath, start_year, end_year, step)
    split_movies(input_filepath, output_filepath, start_year, end_year, step)

    logger.info(f"Data Splitting done. Data saved in {output_filepath}.")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
