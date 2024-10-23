import pickle

import pandas as pd


def make_prediction_by_user(users_id):
    # Read user_matrix
    users = pd.read_csv("data/processed/user_matrix.csv")

    # Filter with the list of users_id
    users = users[users["userId"].isin(users_id)]

    # Delete userId
    users = users.drop("userId", axis=1)

    # Open model
    filehandler = open("models/model.pkl", "rb")
    model = pickle.load(filehandler)
    filehandler.close()

    # Calculate nearest neighbors
    distances, indices = model.kneighbors(users)

    return distances, indices


def make_prediction_by_movie(movie_id):
    # Read movie_matrix
    movies = pd.read_csv("data/processed/movie_matrix.csv")

    # Filter with the movie_id
    movie = movies[movies["movieId"] == movie_id]

    print(movie)
    # Drop movieId
    movie = movie.drop("movieId", axis=1)

    # Open model
    filehandler = open("models/model.pkl", "rb")
    model = pickle.load(filehandler)
    filehandler.close()

    print("Model loaded")

    # Calculate nearest neighbors
    distances, indices = model.kneighbors(movie)

    print(distances, indices)

    return distances, indices
