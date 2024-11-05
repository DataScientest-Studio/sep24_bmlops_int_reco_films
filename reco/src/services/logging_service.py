import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import os
from logging.handlers import RotatingFileHandler
import traceback

class LoggingService:
    def __init__(
        self,
        app_name: str,
        log_dir: str = "logs",
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up loggers
        self.setup_app_logger(max_bytes, backup_count)
        self.setup_error_logger(max_bytes, backup_count)
        self.setup_access_logger(max_bytes, backup_count)
        
    def setup_app_logger(self, max_bytes: int, backup_count: int):
        """Set up main application logger."""
        app_logger = logging.getLogger(self.app_name)
        app_logger.setLevel(logging.INFO)
        
        # File handler
        handler = RotatingFileHandler(
            self.log_dir / f"{self.app_name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        handler.setFormatter(self._get_formatter())
        app_logger.addHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._get_formatter())
        app_logger.addHandler(console_handler)
        
    def setup_error_logger(self, max_bytes: int, backup_count: int):
        """Set up error logger."""
        error_logger = logging.getLogger(f"{self.app_name}.error")
        error_logger.setLevel(logging.ERROR)
        
        handler = RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        handler.setFormatter(self._get_formatter())
        error_logger.addHandler(handler)
        
    def setup_access_logger(self, max_bytes: int, backup_count: int):
        """Set up access logger for API requests."""
        access_logger = logging.getLogger(f"{self.app_name}.access")
        access_logger.setLevel(logging.INFO)
        
        handler = RotatingFileHandler(
            self.log_dir / "access.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        handler.setFormatter(self._get_formatter())
        access_logger.addHandler(handler)
        
    def _get_formatter(self):
        """Get log formatter."""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict] = None
    ):
        """Log error with context."""
        error_logger = logging.getLogger(f"{self.app_name}.error")
        
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        error_logger.error(json.dumps(error_data))
        
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: Optional[int] = None
    ):
        """Log API request."""
        access_logger = logging.getLogger(f"{self.app_name}.access")
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'user_id': user_id
        }
        
        access_logger.info(json.dumps(log_data))
        
    def log_model_metrics(
        self,
        metrics: Dict[str, float],
        model_version: str
    ):
        """Log model performance metrics."""
        app_logger = logging.getLogger(self.app_name)
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'model_version': model_version,
            'metrics': metrics
        }
        
        app_logger.info(f"Model Metrics: {json.dumps(log_data)}")
        
    def log_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ):
        """Log custom event."""
        app_logger = logging.getLogger(self.app_name)
        
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'data': data
        }
        
        app_logger.info(f"Event: {json.dumps(log_data)}") 