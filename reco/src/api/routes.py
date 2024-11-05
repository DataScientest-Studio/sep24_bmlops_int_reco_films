# src/api/routes.py

from fastapi import APIRouter, HTTPException
from src.models.collaborative_filtering import recommend_movies
import pandas as pd

router = APIRouter()

# Load movies data
movies_df = pd.read_csv('../../data/processed/movies_clean.csv')

@router.get("/recommend/{user_id}")
def get_recommendations(user_id: int, top_n: int = 10):
    """
    API endpoint to get movie recommendations for a user.

    Args:
        user_id (int): The ID of the user.
        top_n (int): Number of recommendations to return.

    Returns:
        dict: A dictionary containing user ID and recommended movies.
    """
    try:
        recommended_movie_ids = recommend_movies(user_id, '../../models/collaborative_filtering_model.pkl', top_n)
        recommended_movies = movies_df[movies_df['movieId'].isin(recommended_movie_ids)][['movieId', 'title', 'genres']]
        return {
            "user_id": user_id,
            "recommended_movies": recommended_movies.to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Explanation:

#     Imports: We import APIRouter, HTTPException, and the recommend_movies function.

#     Router Initialization: We create an instance of APIRouter.

#     Load Movies Data: We load the preprocessed movies data to provide movie details in the response.

#     Endpoint /recommend/{user_id}:

#         Parameters:

#             user_id: The user ID for whom to generate recommendations.

#             top_n: The number of recommendations to return (default is 10).

#         Process:

#             Calls recommend_movies to get recommended movie IDs.

#             Retrieves movie details from movies_df.

#             Returns a dictionary containing the user ID and a list of recommended movies.

#         Error Handling: Catches exceptions and returns an HTTP 500 error if something goes wrong.