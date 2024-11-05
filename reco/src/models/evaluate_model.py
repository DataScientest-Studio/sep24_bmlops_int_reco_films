"""
This module handles the evaluation of the movie recommendation system.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from collections import defaultdict
from surprise import accuracy
import logging
from sqlalchemy import text
import random
import time
from sklearn.neighbors import NearestNeighbors
import json
from datetime import datetime
from tqdm import tqdm
from functools import lru_cache
from joblib import Memory, Parallel, delayed
import os.path as op
from pathlib import Path

# Fix the path issue by adding the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from src.data.database import get_engine, Rating, Movie
from src.models.collaborative_filtering import CollaborativeFilteringModel, find_similar_movies

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE = 500000  # Adjust chunk size for memory management
MAX_WORKERS = 8
PERSONALIZATION_SAMPLE = 1000

# Setup caching
cache_dir = Path(project_root) / 'cache'
cache_dir.mkdir(exist_ok=True)
memory = Memory(cache_dir, verbose=0)

@lru_cache(maxsize=1024)
def get_movie_details_cached(movie_id, engine_url):
    """Cached version of get_movie_details."""
    engine = get_engine()
    return get_movie_details(movie_id, engine)

@memory.cache
def load_movie_genres(engine):
    """Cached loading of movie genres."""
    query = text("""
        SELECT "movieId", genres 
        FROM movies
    """)
    
    with engine.connect() as connection:
        result = connection.execute(query)
        movie_genres = pd.DataFrame(result.fetchall(), columns=['movieId', 'genres'])
        return movie_genres.set_index('movieId')['genres'].to_dict()

def parallel_user_predictions(user_group, model):
    """Process predictions for a group of users in parallel."""
    predictions = []
    for _, row in user_group.iterrows():
        try:
            pred = model.predict(row['userId'], row['movieId'])
            predictions.append((row['userId'], row['movieId'], row['rating'], pred, row.get('timestamp')))
        except Exception as e:
            continue
    return predictions

def evaluate_model(model, ratings_data, k=10):
    """Optimized model evaluation with caching and parallel processing."""
    start_time = time.time()
    logger.info("Starting model evaluation...")

    try:
        # Use cached movie genres
        engine = get_engine()
        movie_genres = load_movie_genres(engine)
        logger.info("Loaded movie genres from cache or database")
        
        # Split data into user groups for parallel processing
        user_groups = np.array_split(ratings_data, MAX_WORKERS)
        
        # Generate predictions in parallel
        logger.info("Generating predictions in parallel...")
        predictions = []
        with Parallel(n_jobs=MAX_WORKERS, prefer="threads") as parallel:
            prediction_groups = list(tqdm(parallel(
                delayed(parallel_user_predictions)(group, model)
                for group in user_groups
            ), desc="Processing user groups"))
            predictions = [p for group in prediction_groups for p in group]

        if not predictions:
            logger.error("No valid predictions generated!")
            return {}

        logger.info(f"Generated {len(predictions)} predictions in {time.time() - start_time:.2f} seconds")

        # Calculate metrics in parallel
        logger.info("Calculating metrics in parallel...")
        
        # Group metrics by dependency for parallel processing
        metric_groups = {
            'accuracy': {
                'rmse': lambda: (accuracy.rmse(predictions), "Root Mean Square Error"),
                'mae': lambda: (accuracy.mae(predictions), "Mean Absolute Error")
            },
            'ranking': {
                f'precision@{k}': lambda: (precision_at_k(predictions, k), f"Precision at {k}"),
                f'recall@{k}': lambda: (recall_at_k(predictions, k), f"Recall at {k}"),
                f'ndcg@{k}': lambda: (calculate_ndcg(predictions, k), f"NDCG at {k}")
            },
            'diversity': {
                'diversity': lambda: (diversity(predictions, set(iid for _, iid, _, _, _ in predictions)), "Aggregate diversity"),
                'temporal_diversity': lambda: (temporal_diversity(predictions), "Temporal diversity"),
                'category_coverage': lambda: (category_coverage(predictions, movie_genres), "Category coverage")
            }
        }

        # Calculate metrics in parallel
        metrics = {}
        with Parallel(n_jobs=MAX_WORKERS, prefer="threads") as parallel:
            for group_name, group_metrics in metric_groups.items():
                results = parallel(
                    delayed(metric_func)()
                    for metric_func in group_metrics.values()
                )
                for (metric_name, _), value in zip(group_metrics.items(), results):
                    metrics[metric_name] = value

        # Calculate remaining metrics that can't be easily parallelized
        remaining_metrics = calculate_remaining_metrics(
            predictions, movie_genres, model, ratings_data, k
        )
        metrics.update(remaining_metrics)

        # Add predictions to metrics for later use
        metrics['predictions'] = predictions

        # Format and print results
        print_evaluation_results(metrics, predictions, model, engine, k)
        
        return metrics

    except Exception as e:
        logger.error(f"Error in evaluation: {str(e)}")
        raise

@memory.cache
def calculate_ndcg(predictions, k):
    """Cached NDCG calculation."""
    user_ratings = defaultdict(list)
    for uid, _, true_r, est, _ in predictions:
        user_ratings[uid].append((est, true_r))
    
    ndcg_scores = []
    for uid in user_ratings:
        true_r = [r[1] for r in user_ratings[uid]]
        pred_r = [r[0] for r in user_ratings[uid]]
        ndcg_scores.append(ndcg_at_k(true_r, pred_r, k))
    
    return np.mean(ndcg_scores)

def calculate_remaining_metrics(predictions, movie_genres, model, ratings_sample, k):
    """Calculate metrics that can't be easily parallelized."""
    metrics = {}
    
    # Create user profiles once
    user_profiles = create_user_profiles(ratings_sample, movie_genres)
    
    # Calculate metrics
    metrics.update({
        'serendipity': (serendipity(predictions, user_profiles), 
            "How surprising and relevant the recommendations are (0-1)"),
        'novelty': (novelty(predictions, set(iid for _, iid, _, _, _ in predictions)), 
            "Average popularity rank of recommended items"),
        'personalization': (personalization(predictions), 
            "Dissimilarity between users' recommendation lists")
    })
    
    return metrics

def precision_at_k(predictions, k=10, threshold=3.5):
    """Calculate precision@k for each user."""
    user_est_true = defaultdict(list)
    for uid, _, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))

    precisions = {}
    for uid, user_ratings in user_est_true.items():
        user_ratings.sort(key=lambda x: x[0], reverse=True)
        n_rel = sum((true_r >= threshold) for (_, true_r) in user_ratings[:k])
        precisions[uid] = n_rel / k if k != 0 else 0

    return np.mean(list(precisions.values()))

def recall_at_k(predictions, k=10, threshold=3.5):
    """Calculate recall@k for each user."""
    user_est_true = defaultdict(list)
    for uid, _, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))

    recalls = {}
    for uid, user_ratings in user_est_true.items():
        user_ratings.sort(key=lambda x: x[0], reverse=True)
        n_rel = sum((true_r >= threshold) for (_, true_r) in user_ratings)
        n_rel_k = sum((true_r >= threshold) for (_, true_r) in user_ratings[:k])
        recalls[uid] = n_rel_k / n_rel if n_rel != 0 else 0

    return np.mean(list(recalls.values()))

def ndcg_at_k(true_ratings, pred_ratings, k):
    k = min(k, len(true_ratings))
    if k == 0:
        return 0

    dcg = np.sum((np.power(2, pred_ratings[:k]) - 1) / np.log2(np.arange(2, k + 2)))
    idcg = np.sum((np.power(2, np.sort(true_ratings)[::-1][:k]) - 1) / np.log2(np.arange(2, k + 2)))
    return dcg / idcg if idcg > 0 else 0

def novelty(predictions, all_items):
    """Calculate novelty (mean self-information)."""
    item_pop = defaultdict(int)
    for uid, iid, _, _, _ in predictions:
        item_pop[iid] += 1
    n_users = len(set(uid for uid, _, _, _, _ in predictions))
    return np.mean([np.log2(n_users / (item_pop[item] + 1)) for item in all_items])

def diversity(predictions, all_items):
    """Calculate aggregate diversity."""
    rec_items = set(iid for _, iid, _, _, _ in predictions)
    return len(rec_items) / len(all_items)

def coverage(predictions, all_items):
    """Calculate catalog coverage."""
    recommended_items = set(iid for _, iid, _, _, _ in predictions)
    return len(recommended_items) / len(all_items)

def personalization(predictions):
    """Optimized personalization calculation with sampling."""
    logger.info("Calculating personalization metric...")
    
    # Sample users for faster calculation
    user_recs = defaultdict(set)
    for uid, iid, _, _, _ in predictions:
        user_recs[uid].add(iid)
    
    # Sample users if there are too many
    user_list = list(user_recs.keys())
    if len(user_list) > PERSONALIZATION_SAMPLE:
        user_list = random.sample(user_list, PERSONALIZATION_SAMPLE)
    
    n_users = len(user_list)
    if n_users < 2:
        return 0
    
    total_diff = 0
    comparisons = 0
    
    # Calculate total number of comparisons for progress bar
    total_comparisons = (n_users * (n_users - 1)) // 2
    
    with tqdm(total=total_comparisons, desc="Calculating personalization") as pbar:
        for i, u1 in enumerate(user_list):
            for u2 in user_list[i+1:]:
                intersection = len(user_recs[u1].intersection(user_recs[u2]))
                union = len(user_recs[u1].union(user_recs[u2]))
                total_diff += 1 - (intersection / union if union > 0 else 0)
                comparisons += 1
                pbar.update(1)
    
    return 2 * total_diff / (n_users * (n_users - 1)) if comparisons > 0 else 0

def calculate_pseudo_ratings(model, testset, k=10):
    """Calculate pseudo-ratings for users based on similar movies."""
    logger.info("Calculating pseudo-ratings...")
    
    try:
        # Ensure model features are loaded
        if not hasattr(model, 'movie_features') or not hasattr(model, 'movie_ids'):
            model.load_features()
            
        movie_features = np.array([model.movie_features[mid] for mid in model.movie_ids])
        
        nn = NearestNeighbors(n_neighbors=k+1, metric='cosine', n_jobs=-1)
        nn.fit(movie_features)
        
        pseudo_ratings = {}
        batch_size = 100
        
        # Convert testset to list if it's a DataFrame
        if isinstance(testset, pd.DataFrame):
            testset_list = testset.to_dict('records')
        else:
            testset_list = testset
            
        total_batches = len(testset_list) // batch_size + (1 if len(testset_list) % batch_size else 0)
        
        with tqdm(total=total_batches, desc="Processing pseudo-ratings") as pbar:
            for i in range(0, len(testset_list), batch_size):
                batch = testset_list[i:i + batch_size]
                valid_movies = []
                
                for row in batch:
                    movie_id = row['movieId']
                    if movie_id in model.movie_to_index:
                        valid_movies.append((movie_id, row))
                
                if not valid_movies:
                    pbar.update(1)
                    continue
                
                movie_indices = [model.movie_to_index[mid] for mid, _ in valid_movies]
                batch_features = movie_features[movie_indices]
                distances, indices = nn.kneighbors(batch_features)
                
                for (movie_id, row), dist in zip(valid_movies, distances):
                    similarities = 1 - dist[1:]
                    avg_similarity = np.mean(similarities)
                    normalized_rating = 5 * avg_similarity
                    pseudo_ratings[(row['userId'], movie_id)] = normalized_rating
                
                pbar.update(1)
                
        return pseudo_ratings
        
    except Exception as e:
        logger.error(f"Error in pseudo-ratings calculation: {str(e)}")
        return {}

def evaluate_similarity(model, predictions, k=10):
    """Evaluate the similarity-based recommendations."""
    logger.info("Evaluating similarity-based recommendations...")
    similarity_scores = []
    sample_predictions = random.sample(predictions, min(1000, len(predictions)))
    
    for uid, iid, _, _, _ in tqdm(sample_predictions, desc="Calculating similarities"):
        try:
            similar_movies = find_similar_movies(iid, model.model_path, top_n=k)
            if similar_movies:
                avg_similarity = np.mean([movie['similarity'] for movie in similar_movies])
                similarity_scores.append(avg_similarity)
        except Exception as e:
            logger.warning(f"Error calculating similarity for movie {iid}: {str(e)}")
            continue
            
    return np.mean(similarity_scores) if similarity_scores else 0

def generate_predictions_batch(model, test_data_batch):
    """Generate predictions for a batch of test data."""
    predictions = []
    for _, row in test_data_batch.iterrows():
        try:
            pred = model.predict(row['userId'], row['movieId'])
            predictions.append((row['userId'], row['movieId'], row['rating'], pred, None))
        except Exception as e:
            continue
    return predictions

def get_movie_details(movie_id, engine):
    """Get movie details from database."""
    try:
        query = text("""
            SELECT m.title, m.genres, 
                   AVG(r.rating) as avg_rating,
                   COUNT(r.rating) as num_ratings
            FROM movies m
            LEFT JOIN ratings r ON m."movieId" = r."movieId"
            WHERE m."movieId" = :movie_id
            GROUP BY m."movieId", m.title, m.genres
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"movie_id": movie_id})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            else:
                logger.warning(f"No details found for movie ID {movie_id}")
    except Exception as e:
        logger.error(f"Error fetching movie details: {str(e)}")
    return None

def format_movie_recommendation(movie_details, predicted_rating, similarity=None):
    """Format movie recommendation output."""
    if not movie_details:
        return "Movie details not available"
    
    output = [
        f"Title: {movie_details['title']}",
        f"Genre: {movie_details['genres']}",
        f"Predicted Rating: {predicted_rating:.2f}/5.0",
        f"Average User Rating: {movie_details.get('avg_rating', 0):.2f}/5.0 ({movie_details.get('num_ratings', 0)} ratings)"
    ]
    
    if similarity is not None:
        output.append(f"Similarity Score: {similarity:.3f}")
    
    return "\n    ".join(output)

def print_recommendations(user_id, predictions, model, engine, k=10):
    """Print formatted movie recommendations."""
    # Filter predictions for the specified user
    user_preds = [(est, iid) for uid, iid, _, est, _ in predictions if uid == user_id]
    user_preds.sort(reverse=True)
    
    if not user_preds:
        logger.warning(f"No recommendations found for user {user_id}")
        return

    logger.info("\n" + "="*100)
    logger.info(f"Top {k} Movie Recommendations for User {user_id}")
    logger.info("="*100)
    
    for i, (est, movie_id) in enumerate(user_preds[:k], 1):
        # Get movie details
        movie_details = get_movie_details(movie_id, engine)
        
        if movie_details:
            # Get similarity score
            similar_movies = find_similar_movies(movie_id, model.model_path, top_n=1)
            similarity = similar_movies[0]['similarity'] if similar_movies else None
            
            logger.info(f"\n{i}. {format_movie_recommendation(movie_details, est, similarity)}")
        else:
            logger.info(f"\n{i}. Movie details not available for Movie ID {movie_id}")
    
    logger.info("="*100)

def print_movie_based_recommendations(movie_id, model, engine, k=10):
    """Print recommendations based on a selected movie."""
    similar_movies = find_similar_movies(movie_id, model.model_path, top_n=k)
    
    logger.info("\n" + "="*100)
    logger.info(f"Top {k} Movies Similar to Movie ID {movie_id}")
    logger.info("="*100)
    
    for i, movie in enumerate(similar_movies, 1):
        movie_details = get_movie_details(movie['movieId'], engine)
        logger.info(f"\n{i}. {format_movie_recommendation(movie_details, movie['similarity'])}")
    
    logger.info("="*100)

def serendipity(predictions, user_profiles, k=10, threshold=3.5):
    """Calculate serendipity - how surprising and relevant the recommendations are."""
    logger.info("Calculating serendipity...")
    
    def expected_items(user_profile):
        """Get items user would expect based on their profile."""
        genres = defaultdict(int)
        for _, genre in user_profile:
            genres[genre] += 1
        return set(genre for genre, count in genres.items() if count > threshold)
    
    user_serendipity = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        if uid in user_profiles and est >= threshold:
            expected = expected_items(user_profiles[uid])
            unexpected = 1 - (len(expected) / (len(expected) + 1))  # Normalize
            relevance = true_r / 5.0  # Normalize rating
            user_serendipity[uid].append(unexpected * relevance)
    
    return np.mean([np.mean(scores[:k]) for scores in user_serendipity.values()])

def temporal_diversity(predictions, time_window=30):
    """Calculate how recommendations vary over time."""
    logger.info("Calculating temporal diversity...")
    
    user_recs_time = defaultdict(lambda: defaultdict(set))
    for uid, iid, _, _, timestamp in predictions:
        # Ensure timestamp is an integer
        if isinstance(timestamp, pd.Timestamp):
            timestamp = int(timestamp.timestamp())
        period = timestamp // (time_window * 24 * 3600)  # Convert to periods
        user_recs_time[uid][period].add(iid)
    
    diversity_scores = []
    for uid, periods in user_recs_time.items():
        period_pairs = [(p1, p2) for p1 in periods for p2 in periods if p1 < p2]
        if period_pairs:
            scores = []
            for p1, p2 in period_pairs:
                intersection = len(periods[p1].intersection(periods[p2]))
                union = len(periods[p1].union(periods[p2]))
                scores.append(1 - (intersection / union if union > 0 else 0))
            diversity_scores.append(np.mean(scores))
    
    return np.mean(diversity_scores) if diversity_scores else 0

def category_coverage(predictions, movie_genres):
    """Calculate coverage across different genres."""
    logger.info("Calculating genre coverage...")
    
    all_genres = set()
    recommended_genres = set()
    
    for _, genres in movie_genres.items():
        all_genres.update(genres.split('|'))
    
    for _, iid, _, _, _ in predictions:
        if iid in movie_genres:
            recommended_genres.update(movie_genres[iid].split('|'))
    
    return len(recommended_genres) / len(all_genres)

def long_tail_ratio(predictions, popularity_threshold=0.9):
    """Calculate proportion of non-popular items recommended."""
    logger.info("Calculating long-tail ratio...")
    
    item_counts = defaultdict(int)
    for _, iid, _, _, _ in predictions:
        item_counts[iid] += 1
    
    sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
    n_popular = int(len(sorted_items) * popularity_threshold)
    popular_items = set(iid for iid, _ in sorted_items[:n_popular])
    
    long_tail_recs = sum(1 for _, iid, _, _, _ in predictions if iid not in popular_items)
    return long_tail_recs / len(predictions)

def user_coverage(predictions, all_users):
    """Calculate percentage of users who receive recommendations."""
    recommended_users = set(uid for uid, _, _, _, _ in predictions)
    return len(recommended_users) / len(all_users)

def cold_start_performance(predictions, user_history, item_history, threshold=5):
    """Evaluate performance on cold-start users and items."""
    logger.info("Evaluating cold-start performance...")
    
    # Cold-start users (few ratings)
    cold_users = {uid for uid, count in user_history.items() if count < threshold}
    cold_user_preds = [p for p in predictions if p[0] in cold_users]
    
    # Cold-start items (few ratings)
    cold_items = {iid for iid, count in item_history.items() if count < threshold}
    cold_item_preds = [p for p in predictions if p[1] in cold_items]
    
    metrics = {
        'cold_user_rmse': accuracy.rmse(cold_user_preds) if cold_user_preds else None,
        'cold_item_rmse': accuracy.rmse(cold_item_preds) if cold_item_preds else None,
    }
    
    return metrics

def diversity_in_top_k(predictions, movie_genres, k=10):
    """Calculate genre diversity in top K recommendations."""
    logger.info("Calculating top-K diversity...")
    
    user_recs = defaultdict(list)
    for uid, iid, _, est, _ in predictions:
        user_recs[uid].append((est, iid))
    
    diversity_scores = []
    for uid, recs in user_recs.items():
        # Get top K recommendations
        top_k = sorted(recs, reverse=True)[:k]
        genres = set()
        for _, iid in top_k:
            if iid in movie_genres:
                genres.update(movie_genres[iid].split('|'))
        diversity_scores.append(len(genres))
    
    return np.mean(diversity_scores) / len(set(g for genres in movie_genres.values() for g in genres.split('|')))

# Add this function to create user profiles
def create_user_profiles(ratings_data, movie_genres):
    """Create user profiles based on their rating history and movie genres."""
    user_profiles = defaultdict(list)
    
    for _, row in ratings_data.iterrows():
        if row['movieId'] in movie_genres:
            genres = movie_genres[row['movieId']].split('|')
            for genre in genres:
                user_profiles[row['userId']].append((row['rating'], genre))
    
    return user_profiles

def load_all_data():
    """Load all ratings data from the database."""
    engine = get_engine()
    query = text("SELECT * FROM ratings")
    
    with engine.connect() as connection:
        result = connection.execute(query)
        return pd.DataFrame(result.fetchall(), columns=result.keys())

def print_evaluation_results(metrics, predictions, model, engine, k):
    """Print the evaluation results in a structured format."""
    logger.info("\nEvaluation Results by Category:")
    logger.info("="*100)
    
    categories = {
        "Accuracy Metrics": ['rmse', 'mae', 'pseudo_rating_rmse'],
        "Ranking Metrics": [f'precision@{k}', f'recall@{k}', f'ndcg@{k}'],
        "Diversity Metrics": ['diversity', 'temporal_diversity', 'diversity_in_top_k'],
        "Coverage Metrics": ['coverage', 'user_coverage', 'long_tail_ratio'],
        "User Experience": ['novelty', 'serendipity', 'personalization'],
        "Similarity Metrics": ['avg_similarity', 'avg_pseudo_rating']
    }
    
    for category, metric_names in categories.items():
        logger.info(f"\n{category}:")
        logger.info("-" * 50)
        for metric in metric_names:
            if metric in metrics:
                value, description = metrics[metric]
                logger.info(f"{metric}:")
                logger.info(f"  Value: {value:.4f}")
                logger.info(f"  Description: {description}")
    
    # Example recommendations
    logger.info("\nExample Recommendations for User 1:")
    logger.info("="*100)
    print_recommendations(1, predictions, model, engine, k=10)

def save_evaluation_results(metrics, output_file='data/processed/evaluation_results.json'):
    """Save evaluation results to a JSON file."""
    try:
        # Convert timestamps to strings for JSON serialization
        results = {
            k: {
                'value': float(v[0]) if isinstance(v[0], (int, float)) else v[0],
                'description': v[1]
            } for k, v in metrics.items()
        }
        # Convert predictions to a serializable format
        if 'predictions' in metrics:
            results['predictions'] = [
                (uid, iid, true_r, est, str(timestamp) if isinstance(timestamp, pd.Timestamp) else timestamp)
                for uid, iid, true_r, est, timestamp in metrics['predictions']
            ]
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        logger.info(f"Evaluation results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving evaluation results: {str(e)}")

def main():
    try:
        # Load model
        model_path = op.join(project_root, 'models', 'collaborative_filtering_model.pkl')
        if not op.exists(model_path):
            logger.error(f"Model not found at {model_path}")
            return
            
        model = CollaborativeFilteringModel(model_path)
        
        # Load all data
        logger.info("Loading all ratings data...")
        data = load_all_data()
        logger.info(f"Loaded {len(data)} ratings for evaluation")
        
        # Evaluate
        metrics = evaluate_model(model, data)
        
        # Save results
        save_evaluation_results(metrics)
        
        # Print recommendations
        engine = get_engine()
        print_movie_based_recommendations(1, model, engine, k=10)
        print_recommendations(1, metrics['predictions'], model, engine, k=10)
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        return

if __name__ == "__main__":
    main()
