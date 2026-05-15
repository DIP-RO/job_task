"""Utils for the system"""

import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logging(log_file: str = None, level: str = "INFO"):
    """Setup logging configuration"""
    if log_file is None:
        log_file = f"data/logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def ensure_directories():
    """Ensure all necessary directories exist"""
    directories = [
        "data/uploads",
        "data/db",
        "data/vector_db",
        "data/logs",
        "data/samples"
    ]
    
    for d in directories:
        Path(d).mkdir(parents=True, exist_ok=True)

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return Path(file_path).stat().st_size

def format_file_size(bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Replace invalid characters
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('._')
    return sanitized
