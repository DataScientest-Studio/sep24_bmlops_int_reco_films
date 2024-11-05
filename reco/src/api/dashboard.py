from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
import pandas as pd
from sqlalchemy.orm import Session
from src.data.database import get_db
from src.models.collaborative_filtering import CollaborativeFiltering
import plotly.express as px
import plotly.graph_objects as go

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/metrics")
def get_model_metrics(db: Session = Depends(get_db)):
    """Get current model performance metrics"""
    query = """
        SELECT * FROM model_evaluations 
        ORDER BY timestamp DESC 
        LIMIT 10
    """
    df = pd.read_sql(query, db.bind)
    
    metrics = {
        "rmse": df['rmse'].tolist(),
        "precision": df['precision_at_k'].tolist(),
        "recall": df['recall_at_k'].tolist(),
        "timestamps": df['timestamp'].tolist()
    }
    
    return metrics

@router.get("/user-activity")
def get_user_activity(db: Session = Depends(get_db)):
    """Get user activity statistics"""
    query = """
        SELECT DATE(timestamp) as date, COUNT(*) as count 
        FROM user_feedback 
        GROUP BY DATE(timestamp) 
        ORDER BY date DESC 
        LIMIT 30
    """
    df = pd.read_sql(query, db.bind)
    
    return {
        "dates": df['date'].tolist(),
        "counts": df['count'].tolist()
    }

@router.get("/genre-distribution")
def get_genre_distribution(db: Session = Depends(get_db)):
    """Get distribution of movie genres"""
    query = """
        SELECT genres, COUNT(*) as count 
        FROM movies 
        GROUP BY genres
    """
    df = pd.read_sql(query, db.bind)
    
    return {
        "genres": df['genres'].tolist(),
        "counts": df['count'].tolist()
    }

@router.get("/recommendation-stats")
def get_recommendation_stats(db: Session = Depends(get_db)):
    """Get recommendation statistics"""
    stats = {
        "total_users": db.query("SELECT COUNT(DISTINCT userId) FROM ratings").scalar(),
        "total_movies": db.query("SELECT COUNT(*) FROM movies").scalar(),
        "total_ratings": db.query("SELECT COUNT(*) FROM ratings").scalar(),
        "avg_rating": db.query("SELECT AVG(rating) FROM ratings").scalar()
    }
    return stats 