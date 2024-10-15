import os

import pandas as pd

from src.data.check_structure import check_existing_folder

interim_data_relative_path = "../data/interim/"

# Import data
ratings = pd.read_csv("../data/raw/ratings.csv")

# Format Unix-timestamp to datetime
ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")


# Split data into 4 parts

ratings["time_interval"] = pd.cut(
    ratings["timestamp"], bins=4, labels=["TI1", "TI2", "TI3", "TI4"]
)

# Save splitted data into csv files

for i in range(1, 5):
    df = ratings[ratings["time_interval"] == f"TI{i}"]
    print(
        f"Time interval {i}: {df['timestamp'].min()} - {df['timestamp'].max()} ({len(df)} ratings)"
    )
    if check_existing_folder(interim_data_relative_path):
        os.makedirs(interim_data_relative_path)
    ratings[ratings["time_interval"] == f"TI{i}"].to_csv(
        f"{interim_data_relative_path}/ratings_TI{i}.csv", index=False
    )


# Do the same for the movies
movies = pd.read_csv("../data/raw/movies.csv")

# Extract the year from the title
movies["year"] = movies["title"].str.extract("\((\d{4})\)")
movies["year"] = pd.to_numeric(movies["year"])

# Split movies into corresponding time intervals
for index, year in enumerate(range(1995, 2020, 5)):
    df = movies[(movies["year"] >= year) & (movies["year"] < year + 5)]
    print(f"TI{index + 1}: Movies from {year} to {year + 5}: {len(df)}")
    df.to_csv(f"../data/interim/movies_TI{index +1 }.csv", index=False)
