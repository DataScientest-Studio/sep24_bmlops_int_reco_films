"""
Utility module for tracking pipeline progress.
"""

import os
from pathlib import Path

class ProgressTracker:
    def __init__(self, progress_dir=None):
        if progress_dir is None:
            # Get project root directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            progress_dir = os.path.join(project_root, 'progress_mark')
        
        self.progress_dir = progress_dir
        Path(self.progress_dir).mkdir(parents=True, exist_ok=True)
    
    def mark_completed(self, step_name: str):
        """Mark a step as completed."""
        step_file = os.path.join(self.progress_dir, f"{step_name}.done")
        Path(step_file).touch()
    
    def is_completed(self, step_name: str) -> bool:
        """Check if a step is completed."""
        step_file = os.path.join(self.progress_dir, f"{step_name}.done")
        return os.path.exists(step_file)
    
    def reset_progress(self):
        """Reset all progress markers."""
        for file in Path(self.progress_dir).glob("*.done"):
            file.unlink()
    
    def get_completed_steps(self):
        """Get list of completed steps."""
        return [f.stem for f in Path(self.progress_dir).glob("*.done")]
