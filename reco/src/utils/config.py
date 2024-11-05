"""
Configuration utility for the recommendation system.
"""

import os
import yaml
from pathlib import Path

def load_config(config_path=None):
    """
    Load configuration from YAML file.
    
    Args:
        config_path (str): Path to config file. If None, uses default location.
        
    Returns:
        dict: Configuration dictionary
    """
    if config_path is None:
        # Get project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    # Check if config file exists
    if not os.path.exists(config_path):
        # Create default config if it doesn't exist
        default_config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'movie_recommendations',
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'postgres')
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000
            },
            'model': {
                'path': 'models/trained_models/model.pkl',
                'version': '1.0.0'
            }
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Save default config
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        return default_config
    
    # Load existing config
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise Exception(f"Error loading config from {config_path}: {str(e)}")

def get_database_url():
    """Get database URL from config or environment variables."""
    config = load_config()
    db_config = config['database']
    
    # Check for environment variables first
    host = os.getenv('DB_HOST', db_config['host'])
    port = os.getenv('DB_PORT', db_config['port'])
    name = os.getenv('DB_NAME', db_config['name'])
    user = os.getenv('DB_USER', db_config['user'])
    password = os.getenv('DB_PASSWORD', db_config['password'])
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

def update_config(updates, config_path=None):
    """
    Update configuration values.
    
    Args:
        updates (dict): Dictionary of updates to apply
        config_path (str): Path to config file
    """
    config = load_config(config_path)
    
    def deep_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    
    config = deep_update(config, updates)
    
    if config_path is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
