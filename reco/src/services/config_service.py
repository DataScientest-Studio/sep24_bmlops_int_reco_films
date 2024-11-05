from typing import Dict, Any, Optional
import yaml
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or 'config/config.yaml'
        self.config = self._load_config()
        self._load_environment_variables()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {}
            
    def _load_environment_variables(self) -> None:
        """Load environment variables from .env file."""
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Environment variables loaded from .env file")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def get_database_url(self) -> str:
        """Get database URL from configuration or environment."""
        db_config = self.config.get('database', {})
        return (
            os.getenv('DATABASE_URL') or
            f"postgresql://{db_config.get('user')}:{db_config.get('password')}@"
            f"{db_config.get('host')}:{db_config.get('port')}/{db_config.get('name')}"
        )
        
    def get_api_settings(self) -> Dict:
        """Get API settings."""
        return self.config.get('api', {})
        
    def get_model_settings(self) -> Dict:
        """Get model training settings."""
        return self.config.get('model', {})
        
    def get_monitoring_settings(self) -> Dict:
        """Get monitoring settings."""
        return self.config.get('monitoring', {})
        
    def get_mlflow_settings(self) -> Dict:
        """Get MLflow settings."""
        return self.config.get('mlflow', {})
        
    def update_config(self, key: str, value: Any) -> None:
        """Update configuration value."""
        try:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                config = config.setdefault(k, {})
            config[keys[-1]] = value
            
            # Save updated configuration
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f)
            logger.info(f"Configuration updated: {key} = {value}")
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            raise
            
    def validate_config(self) -> bool:
        """Validate configuration."""
        required_keys = [
            'database.host',
            'database.port',
            'database.name',
            'database.user',
            'model.algorithm',
            'model.params',
            'api.host',
            'api.port'
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
                
        if missing_keys:
            logger.error(f"Missing required configuration keys: {missing_keys}")
            return False
        return True 