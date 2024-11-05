"""
Validate environment variables script.
"""
import os
from dotenv import load_dotenv

required_vars = [
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'JWT_SECRET_KEY',
    'MLFLOW_TRACKING_URI',
]

def validate_env():
    load_dotenv()
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    
    print("All required environment variables are set.")
    return True

if __name__ == "__main__":
    if not validate_env():
        exit(1)
