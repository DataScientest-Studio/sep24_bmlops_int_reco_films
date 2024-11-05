# src/models/collaborative_filtering.py

import os
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
import joblib
from src.data.database import Rating, Movie, UserPreference, MovieFeature, get_session, get_engine
from sqlalchemy import func
import gc
from sklearn.metrics.pairwise import cosine_similarity
import json
import logging
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Explanation:

#     Imports: We import necessary libraries for modeling and saving the model.

#     Function train_collaborative_filtering:

#         Loads preprocessed ratings data.

#         Creates a user-item rating matrix.

#         Performs SVD to reduce dimensionality.

#         Computes a similarity matrix based on the latent features.

#         Saves the model components (SVD model, user-item matrix, similarity matrix) using joblib.

#     Function recommend_movies:

#         Loads the saved model components.

#         Identifies the user index in the user-item matrix.

#         Retrieves similarity scores for the target user.

#         Finds similar users.

#         Aggregates ratings from similar users for movies not yet rated by the target user.

#         Generates top N movie recommendations.

#     Main Block:

#         Trains the collaborative filtering model.

#         Provides an example of generating recommendations for a user.



def train_collaborative_filtering(model_save_path, n_components=100, chunk_size=100000):
    """
    Trains a collaborative filtering model using SVD and NearestNeighbors.
    Processes data in chunks to handle large datasets.
    """
    session = get_session()
    
    # Get total number of ratings
    total_ratings = session.query(func.count(Rating.id)).scalar()
    print(f"Total ratings: {total_ratings}")

    # Get unique users and movies
    users = session.query(Rating.userId).distinct().all()
    movies = session.query(Rating.movieId).distinct().all()
    
    user_ids = [user[0] for user in users]
    movie_ids = [movie[0] for movie in movies]
    
    user_to_index = {id: index for index, id in enumerate(user_ids)}
    movie_to_index = {id: index for index, id in enumerate(movie_ids)}
    
    # Initialize sparse matrix
    row, col, data = [], [], []
    
    # Process ratings in chunks
    offset = 0
    while offset < total_ratings:
        ratings = session.query(Rating).order_by(Rating.id).offset(offset).limit(chunk_size).all()
        
        for rating in ratings:
            user_index = user_to_index[rating.userId]
            movie_index = movie_to_index[rating.movieId]
            row.append(user_index)
            col.append(movie_index)
            data.append(rating.rating)
        
        offset += chunk_size
        print(f"Processed {offset} ratings")
        
        # Free up memory
        del ratings
        gc.collect()
    
    # Create sparse matrix
    user_item_matrix = csr_matrix((data, (row, col)), shape=(len(user_ids), len(movie_ids)))
    
    # Perform SVD
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    latent_matrix = svd.fit_transform(user_item_matrix)
    
    # Train NearestNeighbors model
    nn_model = NearestNeighbors(metric='cosine', algorithm='brute')
    nn_model.fit(latent_matrix)
    
    # After SVD
    user_features = svd.transform(user_item_matrix)
    movie_features = svd.components_.T
    
    # Store features in the database
    session = get_session()
    for i, user_id in enumerate(user_ids):
        session.merge(UserPreference(userId=user_id, preferences=json.dumps(user_features[i].tolist())))
    session.commit()
    session.close()
    
    # Save the model components
    joblib.dump({
        'svd_model': svd,
        'nn_model': nn_model,
        'user_ids': user_ids,
        'movie_ids': movie_ids,
        'user_to_index': user_to_index,
        'movie_to_index': movie_to_index
    }, model_save_path)
    
    print("Collaborative filtering model trained and saved.")

def recommend_movies(user_id, model_path, top_n=10):
    """
    Recommends movies for a given user based on the trained model.
    """
    # Load the model components
    model_data = joblib.load(model_path)
    svd = model_data['svd_model']
    nn_model = model_data['nn_model']
    user_ids = model_data['user_ids']
    movie_ids = model_data['movie_ids']
    user_to_index = model_data['user_to_index']
    movie_to_index = model_data['movie_to_index']
    
    session = get_session()
    user_preference = session.query(UserPreference).filter_by(userId=user_id).first()
    
    if user_preference:
        user_vector = np.array(json.loads(user_preference.preferences))
    else:
        if user_id not in user_to_index:
            print(f"User {user_id} not found in the training data.")
            return []
        user_index = user_to_index[user_id]
        user_vector = svd.transform(csr_matrix((1, len(movie_ids))))
    
    distances, indices = nn_model.kneighbors(user_vector.reshape(1, -1), n_neighbors=top_n+1)
    similar_users = [user_ids[idx] for idx in indices.flatten()[1:]]
    
    similar_users_ratings = session.query(Rating).filter(Rating.userId.in_(similar_users)).all()
    
    user_rated_movies = set(rating.movieId for rating in session.query(Rating).filter_by(userId=user_id).all())
    movie_ratings = {}
    for rating in similar_users_ratings:
        if rating.movieId not in user_rated_movies:
            if rating.movieId not in movie_ratings:
                movie_ratings[rating.movieId] = []
            movie_ratings[rating.movieId].append(rating.rating)
    
    avg_ratings = [(movieId, np.mean(ratings)) for movieId, ratings in movie_ratings.items()]
    avg_ratings.sort(key=lambda x: x[1], reverse=True)
    
    top_recommendations = []
    for movie_id, avg_rating in avg_ratings[:top_n]:
        movie = session.query(Movie).filter_by(movieId=movie_id).first()
        if movie:
            top_recommendations.append({
                'movieId': movie.movieId,
                'title': movie.title,
                'genres': movie.genres,
                'year': movie.year,
                'avg_rating': avg_rating
            })
    
    session.close()
    return top_recommendations

def find_similar_movies(movie_id, model_path, top_n=10):
    """
    Finds similar movies based on a given movie ID using cosine similarity.
    
    Args:
        movie_id (int): ID of the movie to find similarities for.
        model_path (str): Path to the saved model.
        top_n (int): Number of similar movies to return.
    
    Returns:
        list: List of dictionaries containing similar movie information and similarity scores.
    """
    model_data = joblib.load(model_path)
    svd = model_data['svd_model']
    movie_ids = model_data['movie_ids']
    movie_to_index = model_data['movie_to_index']
    
    if movie_id not in movie_to_index:
        print(f"Movie ID {movie_id} not found in the training data.")
        return []
    
    movie_index = movie_to_index[movie_id]
    movie_factors = svd.components_[:, movie_index]
    
    # Compute cosine similarities
    similarities = cosine_similarity(movie_factors.reshape(1, -1), svd.components_.T)[0]
    
    # Find indices of top_n+1 most similar movies (including the movie itself)
    indices = similarities.argsort()[::-1][:top_n+1]
    
    similar_movies = []
    session = get_session()
    for idx in indices[1:]:  # Skip the first one as it's the movie itself
        similar_movie_id = movie_ids[idx]
        movie = session.query(Movie).filter_by(movieId=similar_movie_id).first()
        if movie:
            similar_movies.append({
                'movieId': movie.movieId,
                'title': movie.title,
                'genres': movie.genres,
                'year': movie.year,
                'similarity': similarities[idx]
            })
    session.close()
    return similar_movies

class CollaborativeFilteringModel:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model_data = joblib.load(model_path)
        self.svd = self.model_data['svd_model']
        self.nn_model = self.model_data['nn_model']
        self.user_ids = self.model_data['user_ids']
        self.movie_ids = self.model_data['movie_ids']
        self.user_to_index = self.model_data['user_to_index']
        self.movie_to_index = self.model_data['movie_to_index']
        self.user_features = None
        self.movie_features = None

    def fit(self, trainset):
        # The model is already trained, so we don't need to do anything here
        pass

    def test(self, testset):
        return [(row['userId'], row['movieId'], row['rating'], self.predict(row['userId'], row['movieId']), None) for row in testset]

    def predict(self, uid, iid):
        if self.user_features is None or self.movie_features is None:
            self.load_features()
        if uid not in self.user_features or iid not in self.movie_features:
            return 0
        return np.dot(self.user_features[uid], self.movie_features[iid])

    def load_features(self):
        session = get_session()
        self.user_features = {uf.userId: np.array(json.loads(uf.preferences)) for uf in session.query(UserPreference).all()}
        self.movie_features = {mf.movieId: np.array(json.loads(mf.features)) for mf in session.query(MovieFeature).all()}
        session.close()

    def generate_features(self, movies_df):
        """Generate features from movie metadata."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize
        
        # Process genres
        genres_vectorizer = TfidfVectorizer()
        genres_features = genres_vectorizer.fit_transform(movies_df['genres'].fillna(''))
        
        # Normalize features
        features = normalize(genres_features, norm='l2')
        
        # Store features
        self.movie_features = {}
        self.movie_ids = movies_df['movieId'].tolist()
        
        for idx, movie_id in enumerate(self.movie_ids):
            self.movie_features[movie_id] = features[idx].toarray().flatten()
            self.movie_to_index[movie_id] = idx

    def save_features(self):
        """Save features to the model file."""
        import pickle
        
        # Save features along with the model
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'movie_features': self.movie_features,
                'movie_ids': self.movie_ids,
                'movie_to_index': self.movie_to_index
            }, f)

    def load_features(self):
        """Load features from the model file."""
        import pickle
        
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                
            if isinstance(data, dict):
                self.movie_features = data.get('movie_features', {})
                self.movie_ids = data.get('movie_ids', [])
                self.movie_to_index = data.get('movie_to_index', {})
            else:
                # Old format - only model
                self.movie_features = {}
                self.movie_ids = []
                self.movie_to_index = {}
                
        except Exception as e:
            logger.error(f"Error loading features: {str(e)}")
            self.movie_features = {}
            self.movie_ids = []
            self.movie_to_index = {}

class CollaborativeFiltering:
    def __init__(self, n_neighbors=5):
        self.model = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=n_neighbors, n_jobs=-1)
        self.user_item_matrix = None
        self.user_mapper = None
        self.item_mapper = None
        self.user_inv_mapper = None
        self.item_inv_mapper = None

    def fit(self, ratings):
        logger.info("Fitting collaborative filtering model")
        user_ids = ratings['userId'].unique()
        item_ids = ratings['movieId'].unique()

        self.user_mapper = {user: i for i, user in enumerate(user_ids)}
        self.item_mapper = {item: i for i, item in enumerate(item_ids)}
        self.user_inv_mapper = {i: user for user, i in self.user_mapper.items()}
        self.item_inv_mapper = {i: item for item, i in self.item_mapper.items()}

        user_index = [self.user_mapper[user] for user in ratings['userId']]
        item_index = [self.item_mapper[item] for item in ratings['movieId']]
        ratings_values = ratings['rating'].values

        self.user_item_matrix = csr_matrix((ratings_values, (user_index, item_index)), shape=(len(user_ids), len(item_ids)))
        self.model.fit(self.user_item_matrix)
        logger.info("Collaborative filtering model fitted successfully")

    def recommend(self, user_id, n_recommendations=10):
        logger.info(f"Generating recommendations for user {user_id}")
        user_index = self.user_mapper.get(user_id)
        if user_index is None:
            logger.warning(f"User {user_id} not found in the training data")
            return []

        user_vector = self.user_item_matrix[user_index]
        _, neighbor_indices = self.model.kneighbors(user_vector, n_neighbors=n_recommendations+1)
        neighbor_indices = neighbor_indices.flatten()[1:]  # Exclude the user itself

        recommendations = []
        for item_index in neighbor_indices:
            item_id = self.item_inv_mapper[item_index]
            recommendations.append(item_id)

        return recommendations

    def load_features(self):
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        self.movie_features = {mf.movieId: np.array(json.loads(mf.features)) for mf in session.query(MovieFeature).all()}
        
        session.close()

def main():
    model_save_path = 'models/collaborative_filtering_model.pkl'
    
    if not os.path.exists(model_save_path):
        try:
            train_collaborative_filtering(model_save_path)
            print(f"Collaborative filtering model trained and saved to {model_save_path}")
        except Exception as e:
            print(f"Error training collaborative filtering model: {str(e)}")
            return
    else:
        print(f"Collaborative filtering model already exists at {model_save_path}. Skipping training.")
    
    # Example recommendation
    user_id_example = 1
    try:
        recommended_movies = recommend_movies(user_id_example, model_save_path, top_n=10)
        print(f"Recommended movies for user {user_id_example}:")
        for movie in recommended_movies:
            print(f"Movie ID: {movie['movieId']}, Title: {movie['title']}, Year: {movie['year']}, Genres: {movie['genres']}, Avg Rating: {movie['avg_rating']:.2f}")
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")

    # Example of finding similar movies
    sample_movie_id = 1  # Toy Story
    try:
        similar_movies = find_similar_movies(sample_movie_id, model_save_path)
        print(f"\nMovies similar to movie ID {sample_movie_id}:")
        for movie in similar_movies:
            print(f"Movie ID: {movie['movieId']}, Title: {movie['title']}, Year: {movie['year']}, Genres: {movie['genres']}, Similarity: {movie['similarity']:.4f}")
    except Exception as e:
        print(f"Error finding similar movies: {str(e)}")

if __name__ == "__main__":
    main()

