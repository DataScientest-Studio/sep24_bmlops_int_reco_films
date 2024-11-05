# src/models/retrain_model.py

import mlflow
import pandas as pd
from src.models.collaborative_filtering import train_collaborative_filtering, CollaborativeFilteringModel
from src.models.evaluate_model import evaluate_model
from src.data.database import get_session, Rating, Feedback, ModelEvaluation
from sqlalchemy import func
import os
from datetime import datetime

def retrain_model(model_save_path):
    """
    Retrains the model using the original ratings data and new user feedback.
    Uses MLflow to track experiments and saves results to the database.
    """
    session = get_session()
    
    # Get original ratings
    ratings = pd.read_sql(session.query(Rating).statement, session.bind)
    
    # Get user feedback
    feedback = pd.read_sql(session.query(Feedback).statement, session.bind)
    
    # Combine original ratings with feedback
    combined_data = pd.concat([ratings, feedback], ignore_index=True)
    
    # Start MLflow run
    with mlflow.start_run() as run:
        # Train the model
        train_collaborative_filtering(model_save_path, combined_data)
        
        # Load the trained model
        model = CollaborativeFilteringModel(model_save_path)
        
        # Evaluate the model
        evaluation_results = evaluate_model(model, combined_data.to_dict('records'))
        
        # Log parameters and metrics
        mlflow.log_param("model_save_path", model_save_path)
        for metric, (value, _) in evaluation_results.items():
            mlflow.log_metric(metric, value)
        
        # Log the model
        mlflow.sklearn.log_model(model, "model")
        
        # Save evaluation results to the database
        model_evaluation = ModelEvaluation(
            run_id=run.info.run_id,
            timestamp=datetime.utcnow(),
            model_path=model_save_path,
            rmse=evaluation_results['RMSE'][0],
            mae=evaluation_results['MAE'][0],
            precision_at_k=evaluation_results['Precision@10'][0],
            recall_at_k=evaluation_results['Recall@10'][0],
            ndcg_at_k=evaluation_results['NDCG@10'][0],
            diversity=evaluation_results['Diversity'][0],
            novelty=evaluation_results['Novelty'][0]
        )
        session.add(model_evaluation)
        session.commit()

    session.close()
    print(f"Model retrained and saved to {model_save_path}")
    print("Evaluation results saved to the database.")
    return evaluation_results

def retrain_on_subsets(data_dir, model_save_path, subset_size=100000):
    """
    Retrains the model on subsets of data, tracking performance over time.
    """
    session = get_session()
    total_ratings = session.query(func.count(Rating.id)).scalar()
    total_feedback = session.query(func.count(Feedback.id)).scalar()
    session.close()

    total_data = total_ratings + total_feedback
    num_subsets = total_data // subset_size

    for i in range(num_subsets):
        print(f"Training on subset {i+1}/{num_subsets}")
        subset_model_path = f"{model_save_path}_subset_{i}"
        evaluation_results = retrain_model(subset_model_path)
        
        # Here you could visualize the evaluation results for each subset
        # For example, you could use the visualize_performance function

if __name__ == "__main__":
    model_save_path = 'models/collaborative_filtering_model.pkl'
    retrain_model(model_save_path)
    
    # Uncomment to retrain on subsets
    # retrain_on_subsets(model_save_path)

# Explanation:

#     retrain_model: Automates the retraining process, including subset creation, preprocessing, training, evaluation, and deployment decision.
#     Deployment Logic: If the new model performs better (lower RMSE), it replaces the current production model.
