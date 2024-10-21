# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path

import click
import pandas as pd
from dotenv import find_dotenv, load_dotenv


# Append all files which names ends before a specific year
def append_files(input_filepath, output_filepath, file_indicator, end_year):
    files = [
        f
        for f in os.listdir(f"{input_filepath}/{file_indicator}")
        if f.endswith(".csv")
    ]

    dfs = []
    for file in files:
        year = int(file.split("_")[-1].split(".")[0])
        if year <= end_year:
            dfs.append(pd.read_csv(f"{input_filepath}/{file_indicator}/{file}"))

    df = pd.concat(dfs, ignore_index=True)
    df.to_csv(f"{output_filepath}/{file_indicator}.csv", index=False)


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
@click.argument("last_year", type=click.INT)
def main(input_filepath, output_filepath, last_year):
    """Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../processed).
    """

    logger = logging.getLogger(__name__)
    logger.info(f"making final data set from raw data until {last_year}")

    append_files(input_filepath, output_filepath, "ratings", last_year)
    append_files(input_filepath, output_filepath, "movies", last_year)
    logger.info(f"Done. Data saved in {output_filepath}.")


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
