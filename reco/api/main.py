# src/api/main.py

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from src.models.collaborative_filtering import recommend_movies, find_similar_movies, CollaborativeFiltering
from src.models.user_feedback import collect_user_feedback, get_user_feedback, add_user_feedback
from src.data.database import get_session, User, Movie
import os
from dotenv import load_dotenv
from prometheus_client import make_asgi_app, Counter, Histogram
import time
from sqlalchemy.orm import Session
from src.data.database import get_db
import logging

load_dotenv()

app = FastAPI()

# Add prometheus asgi middleware to route /metrics requests
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define some metrics
RECOMMENDATIONS_COUNTER = Counter('recommendations_total', 'Total number of recommendations made')
FEEDBACK_COUNTER = Counter('feedback_total', 'Total number of feedback submissions')
REQUEST_TIME = Histogram('request_processing_seconds', 'Time spent processing request')

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

model_path = os.path.join('models', 'collaborative_filtering_model.pkl')

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserInDB(BaseModel):
    id: int
    username: str
    email: str
    hashed_password: str

class FeedbackInput(BaseModel):
    movie_id: int
    rating: float

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    session = get_session()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    session = get_session()
    user = session.query(User).filter(User.username == token_data.username).first()
    session.close()
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=Token)
async def register_user(user: UserCreate):
    session = get_session()
    db_user = session.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    session.close()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/recommendations")
@REQUEST_TIME.time()
async def get_recommendations(current_user: User = Depends(get_current_user)):
    recommendations = recommend_movies(current_user.id, model_path)
    RECOMMENDATIONS_COUNTER.inc()
    return {"recommendations": recommendations}

@app.get("/similar_movies/{movie_id}")
async def get_similar_movies(movie_id: int):
    similar_movies = find_similar_movies(movie_id, model_path)
    return {"similar_movies": similar_movies}

@app.post("/feedback")
@REQUEST_TIME.time()
async def submit_feedback(feedback: FeedbackInput, current_user: User = Depends(get_current_user)):
    success = collect_user_feedback(current_user.id, feedback.movie_id, feedback.rating)
    if success:
        FEEDBACK_COUNTER.inc()
        return {"message": "Feedback submitted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@app.get("/feedback")
async def get_user_feedback_api(current_user: User = Depends(get_current_user)):
    feedback = get_user_feedback(current_user.id)
    return {"feedback": feedback}

@app.post("/users")
async def create_user(user: UserCreate):
    session = get_session()
    db_user = session.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    session.close()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/movies")
async def get_movies(skip: int = 0, limit: int = 100):
    session = get_session()
    movies = session.query(Movie).offset(skip).limit(limit).all()
    session.close()
    return [{"id": movie.id, "title": movie.title, "genres": movie.genres} for movie in movies]

@app.post("/feedback")
def submit_feedback(user_id: int, movie_id: int, rating: float, db: Session = Depends(get_db)):
    logger.info(f"Received feedback submission: user {user_id}, movie {movie_id}, rating {rating}")
    add_user_feedback(db, user_id, movie_id, rating)
    return {"message": "Feedback submitted successfully"}

@app.get("/feedback/{user_id}")
def retrieve_feedback(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Retrieving feedback for user {user_id}")
    feedback = get_user_feedback(db, user_id)
    return {"feedback": feedback}

@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Generating recommendations for user {user_id}")
    cf_model = CollaborativeFiltering()
    # Assume we have a function to load ratings from the database
    ratings = load_ratings_from_db(db)
    cf_model.fit(ratings)
    recommendations = cf_model.recommend(user_id)
    return {"recommendations": recommendations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
