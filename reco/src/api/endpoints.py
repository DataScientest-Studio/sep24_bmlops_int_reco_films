# src/api/endpoints.py

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List
import os
from src.models.predict_model import recommend_movies
from src.api.auth import (
    Token,
    authenticate_user,
    create_access_token,
    get_current_user,
    oauth2_scheme,
)
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

router = APIRouter()

# Define request and response models
class RecommendationRequest(BaseModel):
    candidate_movie_ids: List[int]
    top_n: int = 10

class RecommendationResponse(BaseModel):
    user_id: str
    recommended_movie_ids: List[int]

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint to authenticate user and provide JWT token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data with username and password.

    Returns:
        Token: Access token and token type.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/recommend", response_model=RecommendationResponse)
def get_recommendations(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Protected endpoint to get movie recommendations for a user.

    Args:
        request (RecommendationRequest): Request data.
        current_user (dict): Current authenticated user.

    Returns:
        RecommendationResponse: Recommended movies.
    """
    MODEL_PATH = os.path.join('models', 'trained_models', 'current_model.pkl')
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=500, detail="Model not found.")

    user_id = current_user['username']
    recommended_movie_ids = recommend_movies(
        user_id=user_id,
        movie_ids=request.candidate_movie_ids,
        model_path=MODEL_PATH,
        top_n=request.top_n
    )

    return RecommendationResponse(
        user_id=user_id,
        recommended_movie_ids=recommended_movie_ids
    )


# src/api/endpoints.py

from src.api.auth import get_password_hash

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@router.post("/users", status_code=201)
def create_user(user: UserCreate):
    """
    Endpoint to create a new user.
    """
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already exists.")
    hashed_password = get_password_hash(user.password)
    new_user = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password
    }
    # Save the new user to the database
    # For this example, we'll add to the fake_users_db
    fake_users_db[user.username] = new_user
    return {"message": "User created successfully."}

# Explanation:

#     RecommendationRequest: Defines the expected request body.
#     RecommendationResponse: Defines the response format.
#     get_recommendations: API endpoint that returns movie recommendations.
# Added /token endpoint to obtain JWT tokens.
# Modified /recommend endpoint to require authentication.
# Uses get_current_user dependency to retrieve the authenticated user.