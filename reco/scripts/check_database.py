"""
Database status checker script for the recommendation system.
Provides comprehensive information about database state and contents.
"""

import os
import sys
import logging
import pandas as pd
from sqlalchemy import inspect, text
from datetime import datetime
from tabulate import tabulate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.data.database import get_engine, get_session
from src.utils.database_check import DatabaseChecker
from src.utils.config import load_config, get_database_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseStatus:
    def __init__(self, config_path=None):
        try:
            self.config = load_config(config_path)
            self.db_checker = DatabaseChecker(config_path)
            self.engine = get_engine()
            self.session = get_session()
        except Exception as e:
            logger.error(f"Failed to initialize database status checker: {str(e)}")
            # Use environment variables for database connection
            self.config = {
                'database': {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', 5432)),
                    'name': os.getenv('DB_NAME', 'movie_recommendations'),
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': os.getenv('DB_PASSWORD', 'postgres')
                }
            }
            try:
                self.engine = get_engine()
                self.session = get_session()
            except Exception as e:
                logger.error(f"Failed to connect to database with environment variables: {str(e)}")
                self.engine = None
                self.session = None

    def get_table_statistics(self):
        """Get statistics for each table in the database."""
        stats = []
        if not self.engine:
            logger.error("No database connection available")
            return []

        try:
            inspector = inspect(self.engine)
            for table_name in inspector.get_table_names():
                with self.engine.connect() as conn:
                    try:
                        # Get row count
                        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                        row_count = result.scalar()
                        
                        # Get last update time if available
                        last_update = None
                        columns = [col['name'].lower() for col in inspector.get_columns(table_name)]
                        if 'timestamp' in columns:
                            result = conn.execute(text(f'SELECT MAX("timestamp") FROM "{table_name}"'))
                            last_update = result.scalar()
                        
                        # Get table size
                        result = conn.execute(text(f"""
                            SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
                        """))
                        size = result.scalar()
                        
                        stats.append({
                            'table': table_name,
                            'rows': row_count,
                            'size': size,
                            'last_update': last_update
                        })
                    except Exception as e:
                        logger.error(f"Error getting statistics for table {table_name}: {str(e)}")
                        stats.append({
                            'table': table_name,
                            'rows': 'ERROR',
                            'size': 'ERROR',
                            'last_update': None
                        })
            return stats
        except Exception as e:
            logger.error(f"Error getting table statistics: {str(e)}")
            return []
    
    def get_data_summary(self):
        """Get summary of key data in the database."""
        if not self.engine:
            logger.error("No database connection available")
            return None

        try:
            with self.engine.connect() as conn:
                # Users summary
                users_query = text("""
                    SELECT 
                        COUNT(DISTINCT "userId") as total_users,
                        COUNT(DISTINCT "movieId") as movies_rated,
                        AVG(rating) as avg_rating
                    FROM "ratings"
                """)
                users_result = conn.execute(users_query)
                users_summary = users_result.fetchone()
                
                # Movies summary
                movies_query = text("""
                    SELECT 
                        COUNT(*) as total_movies,
                        COUNT(DISTINCT genres) as unique_genres
                    FROM "movies"
                """)
                movies_result = conn.execute(movies_query)
                movies_summary = movies_result.fetchone()
                
                # Ratings distribution
                ratings_query = text("""
                    SELECT 
                        rating,
                        COUNT(*) as count
                    FROM "ratings"
                    GROUP BY rating
                    ORDER BY rating
                """)
                ratings_result = conn.execute(ratings_query)
                ratings_dist = pd.DataFrame(ratings_result.fetchall(), 
                                         columns=['rating', 'count'])
                
                return {
                    'users_summary': users_summary,
                    'movies_summary': movies_summary,
                    'ratings_distribution': ratings_dist
                }
        except Exception as e:
            logger.error(f"Error getting data summary: {str(e)}")
            return None
    
    def print_status_report(self):
        """Print comprehensive database status report."""
        print("\n=== Database Status Report ===")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Database connection info
        db_config = self.config['database']
        print("Database Configuration:")
        print(f"├── Host: {db_config['host']}")
        print(f"├── Port: {db_config['port']}")
        print(f"├── Database: {db_config['name']}")
        print(f"└── User: {db_config['user']}\n")
        
        # Check basic connectivity
        status = self.db_checker.get_database_status()
        print("Connection Status:")
        print(f"├── Connection: {'✓' if status['connection'] else '✗'}")
        print(f"├── Tables Exist: {'✓' if status['tables_exist'] else '✗'}")
        print(f"└── Data Exists: {'✓' if status['data_exists'] else '✗'}\n")
        
        # Table statistics
        print("Table Statistics:")
        stats = self.get_table_statistics()
        if stats:
            print(tabulate(stats, headers='keys', tablefmt='pretty'))
        print()
        
        # Data summary
        summary = self.get_data_summary()
        if summary and summary['users_summary'] and summary['movies_summary']:
            print("Data Summary:")
            print(f"├── Total Users: {summary['users_summary'].total_users:,}")
            print(f"├── Total Movies: {summary['movies_summary'].total_movies:,}")
            print(f"├── Average Rating: {summary['users_summary'].avg_rating:.2f}")
            print(f"└── Unique Genres: {summary['movies_summary'].unique_genres}\n")
            
            if not summary['ratings_distribution'].empty:
                print("Rating Distribution:")
                print(tabulate(summary['ratings_distribution'], 
                             headers=['Rating', 'Count'], 
                             tablefmt='pretty'))
    
    def export_report(self, output_path):
        """Export database status report to file."""
        original_stdout = sys.stdout
        with open(output_path, 'w') as f:
            sys.stdout = f
            self.print_status_report()
            sys.stdout = original_stdout
        logger.info(f"Report exported to {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check database status')
    parser.add_argument('--export', type=str, help='Export report to file')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--init', action='store_true', 
                       help='Initialize default configuration if none exists')
    parser.add_argument('--env-file', type=str, default='.env',
                       help='Path to environment file')
    
    args = parser.parse_args()
    
    # Load environment variables from specified file
    if os.path.exists(args.env_file):
        load_dotenv(args.env_file)
    
    try:
        if args.init:
            config = load_config()  # This will create default config if none exists
            print("Configuration initialized successfully.")
            print(f"Database URL: {get_database_url()}")
            return
        
        db_status = DatabaseStatus(config_path=args.config)
        
        if args.export:
            db_status.export_report(args.export)
        else:
            db_status.print_status_report()
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.info("Try running with --init to create default configuration")
        logger.info("Make sure your database credentials are correctly set in the .env file")
        sys.exit(1)

if __name__ == "__main__":
    main()
