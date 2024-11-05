# src/data/create_evaluation_set.py

import pandas as pd
import os
from sklearn.model_selection import train_test_split

def create_evaluation_set(cleaned_data_path, evaluation_dir, test_size=0.1):
    """
    Split the cleaned data to create an evaluation set.
    """
    # Load cleaned data
    data = pd.read_csv(cleaned_data_path)

    # Split data
    _, eval_set = train_test_split(data, test_size=test_size, random_state=42)

    # Save evaluation set
    os.makedirs(evaluation_dir, exist_ok=True)
    eval_set.to_csv(os.path.join(evaluation_dir, 'eval_set_1.csv'), index=False)
    print(f"Evaluation set saved to {evaluation_dir}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CLEANED_DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'cleaned_data.csv')
    EVALUATION_DIR = os.path.join(BASE_DIR, 'data', 'evaluation')
    print(f"Looking for file at: {CLEANED_DATA_PATH}")
    create_evaluation_set(CLEANED_DATA_PATH, EVALUATION_DIR)
