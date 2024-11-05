import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.data.database import init_db, get_engine, Base
from sqlalchemy import inspect, text
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    engine = get_engine()
    inspector = inspect(engine)

    # Get all table names
    table_names = inspector.get_table_names()

    # Drop all tables using SQL commands
    with engine.connect() as connection:
        for table in table_names:
            connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        connection.commit()
    print("All existing tables dropped.")

    # Recreate all tables
    init_db()
    print("Database tables recreated successfully.")

if __name__ == "__main__":
    reset_database()
    print("Database reset completed successfully.")
