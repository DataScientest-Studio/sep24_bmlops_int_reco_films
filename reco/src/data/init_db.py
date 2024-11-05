import os
import sys
from dotenv import load_dotenv
import argparse
import logging

# Load environment variables from .env file
load_dotenv()

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.data.database import init_db, check_data_exists, get_engine
from src.data.data_processing import process_and_store_data
from sqlalchemy import inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_database_connection():
    """Verify that we can connect to the database."""
    try:
        engine = get_engine()
        connection = engine.connect()
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def verify_data_files(data_dir):
    """Verify that all required data files exist."""
    required_files = [
        "movies.csv",
        "ratings.csv",
        "links.csv",
        "tags.csv",
        "genome-tags.csv",
        "genome-scores.csv"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    return missing_files

def verify_database_schema():
    """Verify that the database schema matches our models."""
    engine = get_engine()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    required_tables = {
        'users', 'movies', 'ratings', 'feedback', 
        'user_preferences', 'movie_features', 'model_evaluations',
        'links', 'tags', 'genome_tags', 'genome_scores'
    }
    
    missing_tables = required_tables - set(existing_tables)
    return list(missing_tables)

def main(force_reset=False, skip_if_exists=False):
    # Verify database connection
    logger.info("Verifying database connection...")
    if not verify_database_connection():
        logger.error("Failed to connect to database. Please check your database configuration.")
        return

    # Verify data files
    logger.info("Verifying data files...")
    data_dir = os.path.join(project_root, 'data', 'raw')
    missing_files = verify_data_files(data_dir)
    if missing_files:
        logger.error("Missing required data files:")
        for file in missing_files:
            logger.error(f"  - {file}")
        return

    logger.info("Initializing database tables...")
    init_db(force_reset=force_reset)
    
    # Verify database schema
    missing_tables = verify_database_schema()
    if missing_tables:
        logger.error("Missing required database tables:")
        for table in missing_tables:
            logger.error(f"  - {table}")
        return
    
    if skip_if_exists and check_data_exists():
        logger.info("Data already exists in the database. Skipping data processing.")
        return
    
    logger.info("Processing and storing data...")
    movies_file = os.path.join(data_dir, "movies.csv")
    ratings_file = os.path.join(data_dir, "ratings.csv")
    links_file = os.path.join(data_dir, "links.csv")
    tags_file = os.path.join(data_dir, "tags.csv")
    genome_tags_file = os.path.join(data_dir, "genome-tags.csv")
    genome_scores_file = os.path.join(data_dir, "genome-scores.csv")

    try:
        process_and_store_data(
            movies_file, ratings_file, links_file, 
            tags_file, genome_tags_file, genome_scores_file
        )
        logger.info("Data processing and storage completed successfully!")
    except Exception as e:
        logger.error(f"Error during data processing: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize database and load data.')
    parser.add_argument('--force-reset', action='store_true', 
                       help='Force reset the database before initialization')
    parser.add_argument('--skip-if-exists', action='store_true',
                       help='Skip data processing if data already exists')
    
    args = parser.parse_args()
    main(force_reset=args.force_reset, skip_if_exists=args.skip_if_exists)
