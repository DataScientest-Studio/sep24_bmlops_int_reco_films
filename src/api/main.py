import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI

# Add parent directory to path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

from src.models_module_def.model_predict import make_prediction_by_movie

app = FastAPI()

movie_path = "data/processed/movie_matrix.csv"
user_path = "data/processed/user_matrix.csv"
movie_meta_path = "data/interim/movies.csv"

movie_matrix = pd.read_csv(movie_path)
user_matrix = pd.read_csv(user_path)
movie_meta = pd.read_csv(movie_meta_path)


@app.get("/")
async def status():
    return {"status": 1}


@app.post("/movies/{movie_id}/similar")
async def get_similar_movie(movieId: int):
    _, indices = make_prediction_by_movie(movieId)

    movie_ids = movie_matrix.iloc[indices[0]].movieId.values
    movies = movie_meta.loc[movie_meta["movieId"].isin(movie_ids)][["movieId", "title"]]
    return movies.to_dict(orient="records")
