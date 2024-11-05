# tests/test_model.py

import unittest
from src.models.train_model import train_model
import os

class TestModelTraining(unittest.TestCase):
    def test_train_model(self):
        # Assuming a small dataset is available for testing
        data_path = 'data/processed/test_data.csv'
        model_path = 'models/trained_models/test_model.pkl'
        train_model(data_path, model_path)
        self.assertTrue(os.path.exists(model_path))

if __name__ == '__main__':
    unittest.main()
