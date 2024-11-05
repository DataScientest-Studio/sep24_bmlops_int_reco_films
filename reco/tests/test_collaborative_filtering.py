import pytest
from src.models.collaborative_filtering import train_collaborative_filtering, recommend_movies, find_similar_movies
import os

MODEL_PATH = 'models/test_collaborative_filtering_model.pkl'

@pytest.fixture(scope="module")
def trained_model():
    if not os.path.exists(MODEL_PATH):
        train_collaborative_filtering(MODEL_PATH)
    return MODEL_PATH

def test_train_collaborative_filtering(trained_model):
    assert os.path.exists(trained_model)

def test_recommend_movies(trained_model):
    recommendations = recommend_movies(1, trained_model)
    assert len(recommendations) > 0
    assert all(isinstance(rec, dict) for rec in recommendations)

def test_find_similar_movies(trained_model):
    similar_movies = find_similar_movies(1, trained_model)
    assert len(similar_movies) > 0
    assert all(isinstance(movie, dict) for movie in similar_movies)
