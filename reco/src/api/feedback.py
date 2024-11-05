from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from src.data.database import get_db
from src.models.user_feedback import add_user_feedback, get_user_feedback

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackCreate(BaseModel):
    user_id: int
    movie_id: int
    rating: float
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: float
    comment: Optional[str]
    timestamp: datetime

@router.post("/", response_model=FeedbackResponse)
def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Submit user feedback for a movie recommendation"""
    try:
        feedback_record = add_user_feedback(
            db,
            user_id=feedback.user_id,
            movie_id=feedback.movie_id,
            rating=feedback.rating,
            comment=feedback.comment
        )
        return feedback_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
def get_user_feedback_history(user_id: int, db: Session = Depends(get_db)):
    """Get feedback history for a specific user"""
    try:
        feedback_history = get_user_feedback(db, user_id)
        return {"feedback": feedback_history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
def get_feedback_statistics(db: Session = Depends(get_db)):
    """Get overall feedback statistics"""
    try:
        query = """
            SELECT 
                COUNT(*) as total_feedback,
                AVG(rating) as avg_rating,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_feedback
        """
        result = db.execute(query).fetchone()
        return {
            "total_feedback": result.total_feedback,
            "average_rating": float(result.avg_rating),
            "unique_users": result.unique_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 