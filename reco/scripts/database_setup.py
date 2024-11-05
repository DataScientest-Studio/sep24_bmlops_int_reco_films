import os
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from typing import List, Dict
import pandas as pd
from pathlib import Path
import yaml
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(self, config_path: str = 'config/database_config.yaml'):
        self.config = self.load_config(config_path)
        self.engine = self.create_engine()
        self.Session = sessionmaker(bind=self.engine)
        
    def load_config(self, config_path: str) -> Dict:
        """Load database configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def create_engine(self):
        """Create SQLAlchemy engine from configuration."""
        db_config = self.config['database']
        url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        return create_engine(url)
    
    def check_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def create_tables(self):
        """Create all database tables."""
        from src.data.database import Base
        Base.metadata.create_all(self.engine)
        logger.info("Created database tables")
    
    def drop_tables(self):
        """Drop all database tables."""
        from src.data.database import Base
        Base.metadata.drop_all(self.engine)
        logger.info("Dropped all database tables")
    
    def load_initial_data(self, data_dir: str):
        """Load initial data from CSV files into database."""
        session = self.Session()
        try:
            # Load movies
            movies_df = pd.read_csv(os.path.join(data_dir, 'movies.csv'))
            for _, row in movies_df.iterrows():
                movie = Movie(
                    movieId=row['movieId'],
                    title=row['title'],
                    genres=row['genres']
                )
                session.merge(movie)
            
            # Load ratings
            ratings_df = pd.read_csv(os.path.join(data_dir, 'ratings.csv'))
            for _, row in ratings_df.iterrows():
                rating = Rating(
                    userId=row['userId'],
                    movieId=row['movieId'],
                    rating=row['rating'],
                    timestamp=datetime.fromtimestamp(row['timestamp'])
                )
                session.merge(rating)
            
            session.commit()
            logger.info("Loaded initial data successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error loading initial data: {str(e)}")
            raise
        finally:
            session.close()
    
    def verify_data(self) -> Dict:
        """Verify data in database tables."""
        session = self.Session()
        try:
            stats = {}
            for table_name, model in [
                ('movies', Movie),
                ('ratings', Rating),
                ('users', User)
            ]:
                count = session.query(model).count()
                stats[table_name] = count
            return stats
        finally:
            session.close()
    
    def create_indexes(self):
        """Create database indexes for better performance."""
        with self.engine.connect() as conn:
            # Create index on ratings
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ratings_user_movie 
                ON ratings (userId, movieId)
            """))
            # Create index on movies
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_movies_title 
                ON movies (title)
            """))
            conn.commit()
        logger.info("Created database indexes")
    
    def setup_database(self, force_reset: bool = False, load_data: bool = True):
        """Complete database setup process."""
        if not self.check_connection():
            raise Exception("Could not connect to database")
        
        if force_reset:
            self.drop_tables()
        
        self.create_tables()
        self.create_indexes()
        
        if load_data:
            data_dir = self.config['data_dir']
            self.load_initial_data(data_dir)
        
        stats = self.verify_data()
        logger.info("Database setup completed successfully")
        logger.info("Data statistics:")
        for table, count in stats.items():
            logger.info(f"  {table}: {count} records")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Set up database')
    parser.add_argument('--config', default='config/database_config.yaml',
                       help='Path to database configuration file')
    parser.add_argument('--reset', action='store_true',
                       help='Force reset the database')
    parser.add_argument('--no-data', action='store_true',
                       help='Skip loading initial data')
    
    args = parser.parse_args()
    
    setup = DatabaseSetup(args.config)
    setup.setup_database(force_reset=args.reset, load_data=not args.no_data)

if __name__ == "__main__":
    main() 