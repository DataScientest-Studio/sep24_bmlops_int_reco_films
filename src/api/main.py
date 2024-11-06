import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

# Add parent directory to path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

from src.models_module_def.model_predict import (
    make_prediction_by_movie,
    make_prediction_by_user,
)

app = FastAPI()

# Setup Prometheus metrics
Instrumentator().instrument(app).expose(app)

movie_path = "data/processed/movie_matrix.csv"
user_path = "data/processed/user_matrix.csv"
movie_meta_path = "data/interim/movies.csv"

movie_matrix = pd.read_csv(movie_path)
user_matrix = pd.read_csv(user_path)
movie_meta = pd.read_csv(movie_meta_path)


class UserGenreProfile(BaseModel):
    no_genres_listed: int = 0
    action: int
    adventure: int
    animation: int
    children: int
    comedy: int
    crime: int
    documentary: int
    drama: int
    fantasy: int
    film_noir: int
    horror: int
    imax: int
    musical: int
    mystery: int
    romance: int
    sci_fi: int
    thriller: int
    war: int
    western: int


@app.get("/status")
async def get_status():
    """Returns 1 if the API is up"""
    return {"status": 1}


@app.get("/movies/{movie_id}/similar")
async def get_similar_movies(movie_id: int):
    """Returns 5 similar movies to the given movieId"""
    _, indices = make_prediction_by_movie(movie_id)

    movie_ids = movie_matrix.iloc[indices[0]].movieId.values
    movies = movie_meta.loc[movie_meta["movieId"].isin(movie_ids)][["movieId", "title"]]
    return movies.to_dict(orient="records")


@app.post("/users/recommendations")
async def get_movies_by_user_genre_profile(genre_profile: UserGenreProfile):
    """Returns 5 movie recommendations for the given user profile"""
    profile_df = pd.DataFrame([genre_profile.dict()])
    profile_df.columns = profile_df.columns.str.capitalize()

    profile_df = profile_df.rename(
        columns={
            "No_genres_listed": "(no genres listed)",
            "Sci_fi": "Sci-Fi",
            "Film_noir": "Film-Noir",
            "Imax": "IMAX",
        }
    )
    _, indices = make_prediction_by_user(profile_df)

    movie_ids = movie_matrix.iloc[indices[0]].movieId.values
    movies = movie_meta.loc[movie_meta["movieId"].isin(movie_ids)][["movieId", "title"]]
    return movies.to_dict(orient="records")
