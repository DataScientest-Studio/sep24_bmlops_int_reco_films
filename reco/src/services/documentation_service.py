import os
import logging
from pathlib import Path
import pdoc
import yaml
from typing import List, Dict
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentationService:
    def __init__(self, project_root: str, output_dir: str = "docs/api"):
        self.project_root = Path(project_root)
        self.output_dir = self.project_root / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_api_docs(self, modules: List[str]):
        """Generate API documentation using pdoc."""
        logger.info("Generating API documentation...")
        
        try:
            # Configure pdoc
            context = pdoc.Context()
            modules = [pdoc.Module(mod, context=context) for mod in modules]
            
            # Generate HTML documentation
            pdoc.html_package(
                modules,
                output_directory=str(self.output_dir),
                template_directory=str(self.project_root / "docs/templates")
            )
            
            logger.info(f"API documentation generated in {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error generating API documentation: {str(e)}")
            raise
            
    def generate_model_docs(self, model_config: Dict):
        """Generate model documentation from configuration."""
        logger.info("Generating model documentation...")
        
        try:
            doc_path = self.output_dir / "model_documentation.md"
            
            with open(doc_path, 'w') as f:
                f.write("# Model Documentation\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Model Architecture
                f.write("## Model Architecture\n\n")
                f.write(f"Algorithm: {model_config['algorithm']}\n\n")
                
                # Hyperparameters
                f.write("## Hyperparameters\n\n")
                f.write("| Parameter | Value |\n")
                f.write("|-----------|-------|\n")
                for param, value in model_config['params'].items():
                    f.write(f"| {param} | {value} |\n")
                
                # Training Configuration
                if 'training' in model_config:
                    f.write("\n## Training Configuration\n\n")
                    for key, value in model_config['training'].items():
                        f.write(f"- **{key}**: {value}\n")
                
            logger.info(f"Model documentation generated at {doc_path}")
            
        except Exception as e:
            logger.error(f"Error generating model documentation: {str(e)}")
            raise
            
    def generate_metrics_docs(self, metrics_config: Dict):
        """Generate documentation for monitoring metrics."""
        logger.info("Generating metrics documentation...")
        
        try:
            doc_path = self.output_dir / "metrics_documentation.md"
            
            with open(doc_path, 'w') as f:
                f.write("# Metrics Documentation\n\n")
                
                for category, metrics in metrics_config.items():
                    f.write(f"## {category.title()}\n\n")
                    
                    if isinstance(metrics, dict):
                        for metric, config in metrics.items():
                            f.write(f"### {metric}\n\n")
                            if isinstance(config, dict):
                                for key, value in config.items():
                                    f.write(f"- **{key}**: {value}\n")
                            else:
                                f.write(f"- {config}\n")
                    f.write("\n")
                    
            logger.info(f"Metrics documentation generated at {doc_path}")
            
        except Exception as e:
            logger.error(f"Error generating metrics documentation: {str(e)}")
            raise
            
    def generate_api_endpoints_docs(self, app):
        """Generate documentation for API endpoints."""
        logger.info("Generating API endpoints documentation...")
        
        try:
            doc_path = self.output_dir / "api_endpoints.md"
            
            with open(doc_path, 'w') as f:
                f.write("# API Endpoints Documentation\n\n")
                
                for route in app.routes:
                    f.write(f"## {route.path}\n\n")
                    f.write(f"Method: {route.methods}\n\n")
                    
                    if route.description:
                        f.write(f"Description: {route.description}\n\n")
                        
                    if hasattr(route, 'response_model'):
                        f.write("Response Model:\n")
                        f.write("```python\n")
                        f.write(str(route.response_model))
                        f.write("\n```\n\n")
                        
            logger.info(f"API endpoints documentation generated at {doc_path}")
            
        except Exception as e:
            logger.error(f"Error generating API endpoints documentation: {str(e)}")
            raise
            
    def generate_deployment_docs(self, deployment_config: Dict):
        """Generate deployment documentation."""
        logger.info("Generating deployment documentation...")
        
        try:
            doc_path = self.output_dir / "deployment_guide.md"
            
            with open(doc_path, 'w') as f:
                f.write("# Deployment Guide\n\n")
                
                # Docker Configuration
                if 'docker' in deployment_config:
                    f.write("## Docker Configuration\n\n")
                    f.write("```yaml\n")
                    yaml.dump(deployment_config['docker'], f)
                    f.write("```\n\n")
                
                # Kubernetes Configuration
                if 'kubernetes' in deployment_config:
                    f.write("## Kubernetes Configuration\n\n")
                    f.write("```yaml\n")
                    yaml.dump(deployment_config['kubernetes'], f)
                    f.write("```\n\n")
                
                # Environment Variables
                if 'environment' in deployment_config:
                    f.write("## Environment Variables\n\n")
                    f.write("| Variable | Description | Required |\n")
                    f.write("|----------|-------------|----------|\n")
                    for var, config in deployment_config['environment'].items():
                        f.write(f"| {var} | {config['description']} | {config['required']} |\n")
                
            logger.info(f"Deployment documentation generated at {doc_path}")
            
        except Exception as e:
            logger.error(f"Error generating deployment documentation: {str(e)}")
            raise
            
    def generate_all_documentation(self, config_path: str):
        """Generate all documentation from configuration."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Generate each type of documentation
            if 'model' in config:
                self.generate_model_docs(config['model'])
                
            if 'metrics' in config:
                self.generate_metrics_docs(config['metrics'])
                
            if 'deployment' in config:
                self.generate_deployment_docs(config['deployment'])
                
            # Generate API documentation
            if 'api_modules' in config:
                self.generate_api_docs(config['api_modules'])
                
            logger.info("All documentation generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            raise 