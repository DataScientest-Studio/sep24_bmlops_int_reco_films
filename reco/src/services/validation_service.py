from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pydantic import BaseModel, validator
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

class ValidationService:
    def __init__(self, schema_dir: str = "config/schemas"):
        self.schema_dir = Path(schema_dir)
        self.schemas = self._load_schemas()
        self.validation_results = []
        
    def _load_schemas(self) -> Dict:
        """Load validation schemas from JSON files."""
        schemas = {}
        try:
            for schema_file in self.schema_dir.glob("*.json"):
                with open(schema_file, 'r') as f:
                    schemas[schema_file.stem] = json.load(f)
            return schemas
        except Exception as e:
            logger.error(f"Error loading schemas: {str(e)}")
            raise
            
    def validate_dataframe(
        self,
        df: pd.DataFrame,
        schema_name: str
    ) -> Dict[str, Any]:
        """Validate DataFrame against schema."""
        if schema_name not in self.schemas:
            raise ValueError(f"Schema {schema_name} not found")
            
        schema = self.schemas[schema_name]
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'schema': schema_name,
            'n_rows': len(df),
            'errors': [],
            'warnings': []
        }
        
        # Check required columns
        missing_cols = set(schema['required_columns']) - set(df.columns)
        if missing_cols:
            validation_results['errors'].append(
                f"Missing required columns: {missing_cols}"
            )
            
        # Check data types
        for col, dtype in schema['column_types'].items():
            if col in df.columns:
                if not df[col].dtype.name == dtype:
                    validation_results['errors'].append(
                        f"Column {col} has type {df[col].dtype.name}, expected {dtype}"
                    )
                    
        # Check value ranges
        for col, ranges in schema.get('value_ranges', {}).items():
            if col in df.columns:
                if 'min' in ranges and df[col].min() < ranges['min']:
                    validation_results['errors'].append(
                        f"Column {col} has values below minimum {ranges['min']}"
                    )
                if 'max' in ranges and df[col].max() > ranges['max']:
                    validation_results['errors'].append(
                        f"Column {col} has values above maximum {ranges['max']}"
                    )
                    
        # Check for nulls
        for col in schema.get('no_nulls', []):
            if col in df.columns and df[col].isnull().any():
                validation_results['errors'].append(
                    f"Column {col} contains null values"
                )
                
        # Check unique constraints
        for col in schema.get('unique_columns', []):
            if col in df.columns and not df[col].is_unique:
                validation_results['errors'].append(
                    f"Column {col} contains duplicate values"
                )
                
        # Check categorical values
        for col, valid_values in schema.get('categorical_values', {}).items():
            if col in df.columns:
                invalid_values = set(df[col].unique()) - set(valid_values)
                if invalid_values:
                    validation_results['errors'].append(
                        f"Column {col} contains invalid values: {invalid_values}"
                    )
                    
        # Add warnings for potential issues
        for col in df.columns:
            # Check for high cardinality in categorical columns
            if df[col].dtype == 'object' and len(df[col].unique()) > 1000:
                validation_results['warnings'].append(
                    f"Column {col} has high cardinality: {len(df[col].unique())} unique values"
                )
                
            # Check for highly skewed numerical columns
            if np.issubdtype(df[col].dtype, np.number):
                skew = df[col].skew()
                if abs(skew) > 3:
                    validation_results['warnings'].append(
                        f"Column {col} is highly skewed: {skew:.2f}"
                    )
                    
        validation_results['is_valid'] = len(validation_results['errors']) == 0
        self.validation_results.append(validation_results)
        
        return validation_results
        
    def validate_model_input(
        self,
        data: Dict,
        schema_name: str
    ) -> bool:
        """Validate model input data."""
        if schema_name not in self.schemas:
            raise ValueError(f"Schema {schema_name} not found")
            
        schema = self.schemas[schema_name]
        
        # Create Pydantic model dynamically
        class InputModel(BaseModel):
            pass
            
        for field_name, field_type in schema['fields'].items():
            setattr(InputModel, field_name, field_type)
            
        try:
            InputModel(**data)
            return True
        except Exception as e:
            logger.error(f"Input validation error: {str(e)}")
            return False
            
    def save_validation_results(self, output_dir: str = "metrics/validation"):
        """Save validation results to file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_path / f"validation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.validation_results, f, indent=4)
            
        logger.info(f"Validation results saved to {filename}") 