import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.models.evaluate_model import (
    evaluate_model, get_movie_details, format_movie_recommendation,
    print_recommendations, serendipity, temporal_diversity, category_coverage,
    long_tail_ratio, user_coverage, cold_start_performance, diversity_in_top_k,
    novelty, diversity, coverage, personalization, calculate_pseudo_ratings
)
from src.models.collaborative_filtering import CollaborativeFilteringModel
from src.data.database import get_engine

@pytest.fixture(scope="module")
def model():
    return CollaborativeFilteringModel('models/collaborative_filtering_model.pkl')

@pytest.fixture(scope="module")
def engine():
    return get_engine()

@pytest.fixture(scope="module")
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_users = 100
    n_items = 50
    n_ratings = 1000
    
    # Generate random ratings
    data = {
        'userId': np.random.randint(1, n_users + 1, n_ratings),
        'movieId': np.random.randint(1, n_items + 1, n_ratings),
        'rating': np.random.uniform(1, 5, n_ratings),
        'timestamp': [
            int((datetime.now() + timedelta(days=i)).timestamp())
            for i in range(n_ratings)
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture(scope="module")
def sample_predictions():
    """Create sample predictions for testing metrics."""
    return [
        (1, 1, 4.0, 3.8, 1000),  # uid, iid, true_r, est, timestamp
        (1, 2, 3.5, 3.2, 1001),
        (2, 1, 5.0, 4.8, 1002),
        (2, 2, 2.0, 2.5, 1003),
    ]

@pytest.fixture(scope="module")
def movie_genres():
    """Sample movie genres for testing."""
    return {
        1: "Action|Adventure",
        2: "Drama|Romance",
        3: "Comedy",
        4: "Action|Sci-Fi"
    }

@pytest.fixture(scope="module")
def user_profiles(sample_data, movie_genres):
    """Create sample user profiles for testing."""
    return create_user_profiles(sample_data, movie_genres)

def test_basic_metrics(model, sample_data):
    """Test basic accuracy metrics."""
    results = evaluate_model(model, sample_data)
    
    # Test RMSE and MAE
    assert 'rmse' in results
    assert 'mae' in results
    assert 0 <= results['rmse'][0] <= 5
    assert 0 <= results['mae'][0] <= 5

def test_ranking_metrics(model, sample_data):
    """Test ranking-based metrics."""
    results = evaluate_model(model, sample_data)
    
    # Test precision, recall, and NDCG
    assert 'precision@10' in results
    assert 'recall@10' in results
    assert 'ndcg@10' in results
    assert 0 <= results['precision@10'][0] <= 1
    assert 0 <= results['recall@10'][0] <= 1
    assert 0 <= results['ndcg@10'][0] <= 1

def test_diversity_metrics(sample_predictions, movie_genres):
    """Test diversity-related metrics."""
    all_items = set(iid for _, iid, _, _, _ in sample_predictions)
    
    # Test basic diversity
    div = diversity(sample_predictions, all_items)
    assert 0 <= div <= 1
    
    # Test temporal diversity
    temp_div = temporal_diversity(sample_predictions)
    assert 0 <= temp_div <= 1
    
    # Test category coverage
    cat_cov = category_coverage(sample_predictions, movie_genres)
    assert 0 <= cat_cov <= 1
    
    # Test diversity in top-k
    div_top_k = diversity_in_top_k(sample_predictions, movie_genres)
    assert 0 <= div_top_k <= 1

def test_coverage_metrics(sample_predictions, sample_data):
    """Test coverage-related metrics."""
    all_items = set(iid for _, iid, _, _, _ in sample_predictions)
    all_users = set(sample_data['userId'])
    
    # Test basic coverage
    cov = coverage(sample_predictions, all_items)
    assert 0 <= cov <= 1
    
    # Test user coverage
    user_cov = user_coverage(sample_predictions, all_users)
    assert 0 <= user_cov <= 1
    
    # Test long-tail ratio
    lt_ratio = long_tail_ratio(sample_predictions)
    assert 0 <= lt_ratio <= 1

def test_personalization_metrics(sample_predictions):
    """Test personalization-related metrics."""
    # Test basic personalization
    pers = personalization(sample_predictions)
    assert 0 <= pers <= 1

def test_cold_start_metrics(sample_predictions, sample_data):
    """Test cold-start performance metrics."""
    user_history = sample_data.groupby('userId').size().to_dict()
    item_history = sample_data.groupby('movieId').size().to_dict()
    
    cold_start_metrics = cold_start_performance(sample_predictions, user_history, item_history)
    
    if cold_start_metrics['cold_user_rmse']:
        assert 0 <= cold_start_metrics['cold_user_rmse'] <= 5
    if cold_start_metrics['cold_item_rmse']:
        assert 0 <= cold_start_metrics['cold_item_rmse'] <= 5

def test_pseudo_ratings(model, sample_data):
    """Test pseudo-ratings calculation."""
    sample = sample_data.head(100)
    pseudo_ratings = calculate_pseudo_ratings(model, sample)
    
    if pseudo_ratings:
        # Check if pseudo-ratings are within valid range
        ratings = list(pseudo_ratings.values())
        assert all(0 <= r <= 5 for r in ratings)

def test_recommendation_format_details(capsys):
    """Test detailed formatting of recommendations output."""
    engine = get_engine()
    movie_details = get_movie_details(1, engine)
    formatted = format_movie_recommendation(movie_details, 4.2, 0.85)
    
    # Check all required elements
    assert 'Title:' in formatted
    assert 'Genre:' in formatted
    assert 'Year:' in formatted
    assert 'Predicted Rating:' in formatted
    assert 'Average User Rating:' in formatted
    assert 'Similarity Score:' in formatted
    
    # Check formatting
    assert '4.20/5.0' in formatted
    assert '0.850' in formatted

def test_full_evaluation_pipeline(model, sample_data, movie_genres):
    """Test the complete evaluation pipeline."""
    results = evaluate_model(model, sample_data)
    
    # Check if all metric categories are present
    metric_categories = {
        "Accuracy Metrics": ['rmse', 'mae', 'pseudo_rating_rmse'],
        "Ranking Metrics": ['precision@10', 'recall@10', 'ndcg@10'],
        "Diversity Metrics": ['diversity', 'temporal_diversity', 'diversity_in_top_k'],
        "Coverage Metrics": ['coverage', 'user_coverage', 'long_tail_ratio'],
        "User Experience": ['novelty', 'serendipity', 'personalization'],
        "Similarity Metrics": ['avg_similarity', 'avg_pseudo_rating']
    }
    
    for category, metrics in metric_categories.items():
        for metric in metrics:
            assert any(metric in key for key in results.keys()), f"Missing metric: {metric}"
        
    # Check if all values are within valid ranges
    for metric, (value, _) in results.items():
        if 'rmse' in metric.lower() or 'mae' in metric.lower():
            assert 0 <= value <= 5, f"Invalid range for {metric}"
        else:
            assert 0 <= value <= 1, f"Invalid range for {metric}"

def test_error_handling(model):
    """Test error handling in evaluation."""
    # Test with empty dataset
    empty_data = pd.DataFrame(columns=['userId', 'movieId', 'rating'])
    with pytest.raises(Exception):
        evaluate_model(model, empty_data)
    
    # Test with invalid data
    invalid_data = pd.DataFrame({
        'userId': ['a', 'b'],
        'movieId': [1, 2],
        'rating': [4.0, 5.0]
    })
    with pytest.raises(Exception):
        evaluate_model(model, invalid_data)

def test_serendipity(sample_predictions, user_profiles):
    """Test serendipity calculation."""
    serendipity_score = serendipity(sample_predictions, user_profiles)
    assert 0 <= serendipity_score <= 1
