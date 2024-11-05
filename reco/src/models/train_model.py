# src/models/train_model.py

import os
import sys
import pandas as pd
import logging
from pathlib import Path

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model(data_path=None, model_save_path=None):
    """
    Train the recommendation model and save it.
    """
    try:
        # Set default paths relative to project root
        if data_path is None:
            data_path = os.path.join(project_root, 'src', 'data', 'processed', 'processed_ratings.csv')
        
        if model_save_path is None:
            model_save_path = os.path.join(project_root, 'models', 'collaborative_filtering_model.pkl')

        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)

        # Check if data file exists
        if not os.path.exists(data_path):
            # Try alternative path
            alt_data_path = os.path.join(project_root, 'data', 'processed', 'processed_ratings.csv')
            if os.path.exists(alt_data_path):
                data_path = alt_data_path
                logger.info(f"Using alternative data path: {data_path}")
            else:
                logger.error(f"Error: Data file not found at {data_path} or {alt_data_path}")
                return False

        # Load training data
        logger.info(f"Loading data from {data_path}")
        data = pd.read_csv(data_path)
        
        # Initialize and train the model
        from src.models.collaborative_filtering import train_collaborative_filtering
        train_collaborative_filtering(model_save_path)
        
        logger.info(f"Model saved to {model_save_path}")
        return True

    except Exception as e:
        logger.error(f"Error during model training: {str(e)}")
        return False

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs(os.path.join(project_root, 'models'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'data', 'processed'), exist_ok=True)
    
    # Set up the paths
    data_path = os.path.join(project_root, 'data', 'processed', 'processed_ratings.csv')
    model_save_path = os.path.join(project_root, 'models', 'collaborative_filtering_model.pkl')
    
    logger.info(f"Using data path: {data_path}")
    logger.info(f"Using model save path: {model_save_path}")
    
    # Train the model
    success = train_model(data_path, model_save_path)
    
    if success:
        logger.info("Model training completed successfully!")
    else:
        logger.error("Model training failed!")
