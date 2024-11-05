import os
import sys
from sqlalchemy import create_engine, inspect
import pandas as pd

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.data.database import get_engine

def view_database():
    engine = get_engine()
    inspector = inspect(engine)

    # Get list of tables
    tables = inspector.get_table_names()
    print("Tables in the database:", tables)

    # View sample data from each table
    for table in tables:
        print(f"\nSample data from {table}:")
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 5", engine)
        print(df)

    # Print table schemas
    for table in tables:
        print(f"\nSchema for {table}:")
        columns = inspector.get_columns(table)
        for column in columns:
            print(f"  {column['name']}: {column['type']}")

if __name__ == "__main__":
    view_database()
