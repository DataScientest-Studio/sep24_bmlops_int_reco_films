import pickle

import pandas as pd
from sklearn.neighbors import NearestNeighbors

from src.entity import ModelTrainerConfig


class ModelTrainer:
    def __init__(self, config: ModelTrainerConfig):
        self.config = config

    # Content based filtering: Recommend movies based on the similarity of their genres
    def train(self):
        movie_matrix = pd.read_csv(self.config.movie_filename)

        model = NearestNeighbors(
            n_neighbors=self.config.n_neighbors, algorithm=self.config.algorithm
        ).fit(movie_matrix.drop("movieId", axis=1))

        filehandler = open(f"{self.config.root_dir}/{self.config.model_name}", "wb")
        pickle.dump(model, filehandler)
        filehandler.close()
