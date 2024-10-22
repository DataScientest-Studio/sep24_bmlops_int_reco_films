import json
import logging

import numpy as np
import pandas as pd
from predict_model import make_predictions


# Return a sample of users to test the model
def get_test_sample(users, sample_size=0.2, random_state=42):
    sample = users.sample(frac=sample_size, random_state=random_state)
    sample_ids = sample["userId"].values
    return sample_ids


# Returns a list of pseudo-ratings for the recommended movies
def generate_pseudo_ratings(indices):
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


def get_avg_pseudo_rating(pseudo_ratings):
    avg_pseudo_rating = np.mean(pseudo_ratings)
    print(f"Average pseudo-rating: {avg_pseudo_rating:.2f} n={len(pseudo_ratings)}")
    return avg_pseudo_rating


def evaluate(indices):
    pseudo_ratings = generate_pseudo_ratings(indices)
    return get_avg_pseudo_rating(pseudo_ratings)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("evaluating model")

    # Set path variables
    user_matrix_filename = "data/processed/user_matrix.csv"
    model_filename = "models/model.pkl"

    # Load datasets
    users = pd.read_csv(user_matrix_filename)

    # Get test sample
    user_sample = get_test_sample(users)

    # Get predictions
    distances, indices = make_predictions(
        user_sample, model_filename, user_matrix_filename
    )

    # Evaluate
    output_path = "metrics/intra_list_similarity.json"

    intra_list_similarity = evaluate(indices)
    with open(output_path, "w") as f:
        json.dump({"intra_list_similarity": intra_list_similarity}, f, indent=4)

    logger.info(f"json file saved at: {output_path}")
