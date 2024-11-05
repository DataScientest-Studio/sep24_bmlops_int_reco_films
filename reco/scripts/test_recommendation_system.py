import os
import sys
import pandas as pd

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.models.collaborative_filtering import train_collaborative_filtering, recommend_movies
from src.models.user_feedback import collect_user_feedback, get_user_feedback
from src.data.database import Rating, Movie, get_session
from sqlalchemy import func

def test_recommendation_system():
    print("Testing the Movie Recommendation System")
    print("---------------------------------------")

    # 1. Train the collaborative filtering model
    print("\n1. Training the collaborative filtering model...")
    model_path = os.path.join(project_root, 'models', 'collaborative_filtering_model.pkl')
    train_collaborative_filtering(model_path)
    print("Model trained and saved successfully.")

    # 2. Get recommendations for a user
    print("\n2. Getting recommendations for a user...")
    user_id = 1  # You can change this to any user ID in your database
    recommendations = recommend_movies(user_id, model_path, top_n=5)
    print(f"Top 5 recommendations for user {user_id}:")
    for i, movie_id in enumerate(recommendations, 1):
        print(f"  {i}. Movie ID: {movie_id}")

    # 3. Collect user feedback
    print("\n3. Collecting user feedback...")
    for movie_id in recommendations[:2]:  # Provide feedback for the first two recommendations
        rating = 4.5  # Simulating a positive rating
        collect_user_feedback(user_id, movie_id, rating)
        print(f"Feedback recorded: User {user_id} rated movie {movie_id} with {rating} stars.")

    # 4. Retrieve and display user feedback
    print("\n4. Retrieving user feedback...")
    feedback = get_user_feedback()
    print("Recent user feedback:")
    print(feedback.tail())

    # 5. Get some statistics from the database
    print("\n5. Database statistics:")
    session = get_session()
    
    movie_count = session.query(func.count(Movie.movieId)).scalar()
    print(f"Total number of movies: {movie_count}")
    
    rating_count = session.query(func.count(Rating.id)).scalar()
    print(f"Total number of ratings: {rating_count}")
    
    user_count = session.query(func.count(Rating.userId.distinct())).scalar()
    print(f"Total number of users: {user_count}")
    
    session.close()

if __name__ == "__main__":
    test_recommendation_system()
