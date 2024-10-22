import pickle

import pandas as pd
from sklearn.neighbors import NearestNeighbors


# Content based filtering: Recommend movies based on the similarity of their genres
def train_model(movie_matrix):
    nbrs = NearestNeighbors(n_neighbors=5, algorithm="kd_tree").fit(
        movie_matrix.drop("movieId", axis=1)
    )
    return nbrs


if __name__ == "__main__":
    movie_matrix = pd.read_csv("data/processed/movie_matrix.csv")
    model = train_model(movie_matrix)
    filehandler = open("models/model.pkl", "wb")
    pickle.dump(model, filehandler)
    filehandler.close()
