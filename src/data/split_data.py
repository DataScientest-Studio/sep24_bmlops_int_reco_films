import os

import click
import pandas as pd

from src.data.check_structure import check_existing_file, check_existing_folder


def split_ratings(input_filepath, output_filepath):
    """Splits ratings into 4 time intervals based on the timestamp column.

    Args:
        input_filepath (_type_): path to raw data directory
        output_filepath (_type_): path to interim data directory
    """

    ratings = pd.read_csv(f"{input_filepath}/ratings.csv")
    # Format Unix-timestamp to datetime
    ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")

    # Split data into 4 parts
    ratings["time_interval"] = pd.cut(
        ratings["timestamp"], bins=4, labels=["TI1", "TI2", "TI3", "TI4"]
    )

    if check_existing_folder(output_filepath):
        os.makedirs(output_filepath)

    # Save splitted data into csv files
    for i in range(1, 5):
        if check_existing_file(f"{output_filepath}/ratings_TI{i}.csv"):
            # df = ratings[ratings["time_interval"] == f"TI{i}"]
            # print(
            #     f"Time interval {i}: {df['timestamp'].min()} - {df['timestamp'].max()} ({len(df)} ratings)"
            # )
            ratings[ratings["time_interval"] == f"TI{i}"].to_csv(
                f"{output_filepath}/ratings_TI{i}.csv", index=False
            )
    return


def split_movies(input_filepath, output_filepath):
    """Splits movies into time intervals (all 5 years).

    Args:
        input_filepath (_type_): path to raw data directory
        output_filepath (_type_): path to interim data directory
    """
    movies = pd.read_csv(f"{input_filepath}/movies.csv")

    # Extract the year from the title
    movies["year"] = movies["title"].str.extract("\((\d{4})\)")
    movies["year"] = pd.to_numeric(movies["year"])

    if check_existing_folder(output_filepath):
        os.makedirs(output_filepath)

    # Split movies into corresponding time intervals
    for index, year in enumerate(range(1995, 2020, 5)):
        print(year)
        if check_existing_file(f"{output_filepath}/movies_TI{index + 1}.csv"):
            df = movies[(movies["year"] >= year) & (movies["year"] <= year + 5)]
            # print(f"TI{index + 1}: Movies from {year} to {year + 5}: {len(df)}")
            df.to_csv(f"{output_filepath}/movies_TI{index + 1 }.csv", index=False)
    return


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
def main(input_filepath, output_filepath):
    split_ratings(input_filepath, output_filepath)
    split_movies(input_filepath, output_filepath)


if __name__ == "__main__":
    main()
