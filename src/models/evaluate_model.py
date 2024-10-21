import numpy as np
import pandas as pd
from predict_model import make_predictions

# Define path variables
user_matrix_filename = "data/processed/user_matrix.csv"
movie_matrix_filename = "data/processed/movie_matrix.csv"
movies_raw = "data/raw/movies.csv"

# Define tracking_uri
# mlflow.set_tracking_uri("http://localhost:8080")

# # Define experiment name, run name and artifact_path name
# movie_experiment = mlflow.set_experiment("reco_movie")
# run_name = "first_run"

# Load the dataset
users = pd.read_csv(user_matrix_filename)
movies = pd.read_csv(movie_matrix_filename)


movies_meta = pd.read_csv(movies_raw)

# Select some random users for testing
# sample = users.sample(frac=0.2, random_state=42)
users_id = [1, 2, 3, 4, 5]

# For the given users find the nearest movies
distances, indices = make_predictions(
    users_id, "models/model.pkl", "data/processed/user_matrix.csv"
)


def get_movie_title(movie_id):
    return movies_meta[movies_meta["movieId"] == movie_id]["title"].values[0]


# Display the results
# for i, user in enumerate(users_id):
#     print(f"Recommendations for user {user}:")
#     for j, movie in enumerate(indices[i]):
#         print(
#             f"{j + 1}: [{movies.iloc[movie].movieId}] {get_movie_title(movies.iloc[movie].movieId)})"
#         )
#     print("##################")


def evaluate(indices):
    pseudo_ratings = []
    for i, user in enumerate(indices):
        user_pseudo_ratings = []
        for j, movie in enumerate(user):
            # Use inverse of distance as similarity (closer movies are more similar)
            similarity = 1 / (distances[i, j] + 1e-5)  # Avoid division by zero
            user_pseudo_ratings.append(similarity)
            # Normalize pseudo-ratings to a 0-5 range
        normalized_rating = 5 * (
            np.mean(user_pseudo_ratings) / np.max(user_pseudo_ratings)
        )
        pseudo_ratings.append(normalized_rating)
    return pseudo_ratings


result = evaluate(indices)
print(result)

# Load the model
# loaded_model = mlflow.sklearn.load_model("models/model.pkl")
# predictions = loaded_model.predict(X_test)
