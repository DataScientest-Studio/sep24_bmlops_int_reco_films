from typing import Dict, Any, List
import pytest
import logging
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TestService:
    def __init__(self, config: Dict):
        """Initialize test service with configuration."""
        self.config = config
        self.test_data = {}
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """Set up test environment with temporary database."""
        # Create test database URL
        test_db_url = self.config['database']['test_url']
        self.engine = create_engine(test_db_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def generate_test_data(self, data_type: str, size: int = 100) -> pd.DataFrame:
        """Generate synthetic test data."""
        if data_type == "users":
            return pd.DataFrame({
                'userId': range(1, size + 1),
                'username': [f'test_user_{i}' for i in range(1, size + 1)],
                'email': [f'user{i}@test.com' for i in range(1, size + 1)]
            })
        elif data_type == "movies":
            return pd.DataFrame({
                'movieId': range(1, size + 1),
                'title': [f'Test Movie {i}' for i in range(1, size + 1)],
                'genres': np.random.choice(['Action', 'Comedy', 'Drama'], size)
            })
        elif data_type == "ratings":
            return pd.DataFrame({
                'userId': np.random.randint(1, size + 1, size),
                'movieId': np.random.randint(1, size + 1, size),
                'rating': np.random.uniform(1, 5, size),
                'timestamp': [datetime.now() - timedelta(days=i) for i in range(size)]
            })
        else:
            raise ValueError(f"Unknown data type: {data_type}")
            
    def setup_test_database(self):
        """Set up test database with sample data."""
        from src.data.database import Base
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Generate and insert test data
        session = self.Session()
        try:
            users_df = self.generate_test_data("users", 100)
            movies_df = self.generate_test_data("movies", 200)
            ratings_df = self.generate_test_data("ratings", 1000)
            
            # Store data for tests
            self.test_data = {
                "users": users_df,
                "movies": movies_df,
                "ratings": ratings_df
            }
            
            # Insert data into database
            for df, table in [
                (users_df, 'users'),
                (movies_df, 'movies'),
                (ratings_df, 'ratings')
            ]:
                df.to_sql(table, self.engine, if_exists='append', index=False)
                
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting up test database: {str(e)}")
            raise
        finally:
            session.close()
            
    def teardown_test_database(self):
        """Clean up test database."""
        from src.data.database import Base
        Base.metadata.drop_all(self.engine)
        
    def create_test_user(self, session) -> Dict[str, Any]:
        """Create a test user for authentication testing."""
        from src.services.auth_service import AuthService
        
        auth_service = AuthService(self.config)
        test_user = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "test_password"
        }
        
        user = auth_service.create_user(
            username=test_user["username"],
            email=test_user["email"],
            password=test_user["password"]
        )
        
        return {
            "user": user,
            "raw_password": test_user["password"]
        }
        
    def create_test_recommendations(self, user_id: int, n_recommendations: int = 5) -> List[Dict]:
        """Create test movie recommendations."""
        movies_df = self.test_data["movies"]
        sample_movies = movies_df.sample(n=n_recommendations)
        
        recommendations = []
        for _, movie in sample_movies.iterrows():
            recommendations.append({
                "movieId": int(movie["movieId"]),
                "title": movie["title"],
                "score": round(np.random.uniform(0.5, 1.0), 2)
            })
            
        return recommendations
        
    def verify_recommendation_format(self, recommendations: List[Dict]) -> bool:
        """Verify the format of recommendations."""
        required_fields = {"movieId", "title", "score"}
        
        for rec in recommendations:
            if not all(field in rec for field in required_fields):
                return False
            if not isinstance(rec["movieId"], int):
                return False
            if not isinstance(rec["score"], (int, float)):
                return False
            if rec["score"] < 0 or rec["score"] > 1:
                return False
                
        return True
        
    def save_test_results(self, results: Dict[str, Any], output_path: str):
        """Save test results to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4, default=str)
            
    def load_test_results(self, input_path: str) -> Dict[str, Any]:
        """Load test results from file."""
        with open(input_path, 'r') as f:
            return json.load(f)
            
    def compare_test_results(self, old_results: Dict, new_results: Dict) -> Dict:
        """Compare old and new test results."""
        comparison = {}
        
        for metric in old_results:
            if metric in new_results:
                old_value = float(old_results[metric])
                new_value = float(new_results[metric])
                comparison[metric] = {
                    "old": old_value,
                    "new": new_value,
                    "change": new_value - old_value,
                    "change_percent": ((new_value - old_value) / old_value) * 100
                }
                
        return comparison 