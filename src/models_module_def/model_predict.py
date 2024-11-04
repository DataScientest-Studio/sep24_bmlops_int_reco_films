import pickle

import pandas as pd


def make_prediction_by_user(user_profile):
    # Open model
    filehandler = open("models/model.pkl", "rb")
    model = pickle.load(filehandler)
    filehandler.close()

    # Calculate nearest neighbors
    distances, indices = model.kneighbors(user_profile)

    return distances, indices


def make_prediction_by_movie(movie_id):
    # Read movie_matrix
    movies = pd.read_csv("data/processed/movie_matrix.csv")

    # Filter with the movie_id
    movie = movies[movies["movieId"] == movie_id]

    # Drop movieId
    movie = movie.drop("movieId", axis=1)

    # Open model
    filehandler = open("models/model.pkl", "rb")
    model = pickle.load(filehandler)
    filehandler.close()

    # Calculate nearest neighbors
    distances, indices = model.kneighbors(movie)

    return distances, indices
