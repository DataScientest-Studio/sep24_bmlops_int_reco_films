# tests/test_data.py

import unittest
import pandas as pd
from src.data.make_dataset import initial_preprocessing

class TestDataProcessing(unittest.TestCase):
    def test_initial_preprocessing(self):
        data = pd.DataFrame({
            'user_id': [1, 2, None],
            'movie_id': [10, None, 30],
            'rating': [5, 4, 3]
        })
        processed_data = initial_preprocessing(data)
        self.assertFalse(processed_data.isnull().values.any())

if __name__ == '__main__':
    unittest.main()
