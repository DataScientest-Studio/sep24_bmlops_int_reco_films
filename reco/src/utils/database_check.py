"""
Utility module for checking database status and connections.
"""

import os
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from src.utils.config import load_config

logger = logging.getLogger(__name__)

class DatabaseChecker:
    def __init__(self, config_path='config/config.yaml'):
        self.config = load_config(config_path)
        self.engine = None
        
    def get_connection_url(self):
        """Get database connection URL from config or environment."""
        db_config = self.config['database']
        return f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
    
    def check_connection(self):
        """Check if database connection is possible."""
        try:
            self.engine = create_engine(self.get_connection_url())
            with self.engine.connect() as conn:
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {str(e)}")
            return False
            
    def check_tables_exist(self):
        """Check if required tables exist in the database."""
        if not self.engine:
            self.check_connection()
            
        required_tables = {
            'users', 'movies', 'ratings', 'feedback', 
            'user_preferences', 'movie_features', 'model_evaluations',
            'links', 'tags', 'genome_tags', 'genome_scores'
        }
        
        try:
            inspector = inspect(self.engine)
            existing_tables = set(inspector.get_table_names())
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                return False
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error checking tables: {str(e)}")
            return False
            
    def check_data_exists(self):
        """Check if data exists in key tables."""
        if not self.engine:
            self.check_connection()
            
        key_tables = ['movies', 'ratings', 'users']
        try:
            with self.engine.connect() as conn:
                for table in key_tables:
                    result = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    if count == 0:
                        logger.warning(f"Table '{table}' is empty")
                        return False
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error checking data: {str(e)}")
            return False
    
    def get_database_status(self):
        """Get comprehensive database status."""
        return {
            'connection': self.check_connection(),
            'tables_exist': self.check_tables_exist(),
            'data_exists': self.check_data_exists()
        }
