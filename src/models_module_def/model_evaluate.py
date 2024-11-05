import pickle
import sys
from pathlib import Path

import dagshub
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

# Add parent directory to path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)


from src.common_utils import save_json
from src.entity import ModelEvaluationConfig
from src.models_module_def.model_predict import make_prediction_by_user


class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig):
        self.config = config

        dagshub.init(
            repo_owner=self.config.repo_owner,
            repo_name=self.config.repo_name,
            mlflow=True,
        )

    # Return a sample of users to test the model
    def get_test_sample(self, users, sample_size=0.2, random_state=42):
        sample = users.drop(columns=["userId"]).sample(
            frac=sample_size, random_state=random_state
        )
        return sample

    # Returns a list of pseudo-ratings for the recommended movies
    def generate_pseudo_ratings(self, indices, distances):
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

    def get_avg_pseudo_rating(self, pseudo_ratings):
        avg_pseudo_rating = np.mean(pseudo_ratings)
        print(f"Average pseudo-rating: {avg_pseudo_rating:.2f} n={len(pseudo_ratings)}")
        return avg_pseudo_rating

    def evaluate(self):
        # Load datasets
        users = pd.read_csv(self.config.user_filename)

        # Get test sample
        user_sample = self.get_test_sample(users)

        # Get predictions
        distances, indices = make_prediction_by_user(user_sample)

        pseudo_ratings = self.generate_pseudo_ratings(indices, distances)
        intra_list_similarity = self.get_avg_pseudo_rating(pseudo_ratings)
        return intra_list_similarity

    def log_into_mlflow(self):
        # Open model
        filehandler = open(self.config.model_path, "rb")
        model = pickle.load(filehandler)
        filehandler.close()

        mlflow.set_registry_uri(self.config.mlflow_uri)

        with mlflow.start_run():
            intra_list_similarity = self.evaluate()

            # Saving metric as local file
            save_json(
                path=Path(self.config.metric_file_name),
                data={"intra_list_similarity": intra_list_similarity},
            )

            # Log the metric into MLflow
            mlflow.log_metric("intra_list_similarity", intra_list_similarity)

            users = pd.read_csv(self.config.user_filename)
            user_sample = self.get_test_sample(users)
            input_example = user_sample.iloc[0].to_dict()

            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name="NearestNeighbors",
                input_example=input_example,
            )
            print(f"Model registered with intra_similarity: {intra_list_similarity}")
