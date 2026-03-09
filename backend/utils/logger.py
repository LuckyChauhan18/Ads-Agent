import logging
import os
import sys

# Define base directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "extra", "logs")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")

def setup_logger(name="spectra_ai"):
    """
    Creates or retrieves a configured logger that streams outputs
    simultaneously to the terminal (stdout) and the pipeline.log file.
    """
    logger = logging.getLogger(name)
    
    # Only configure if it hasn't been configured yet
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Log format
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File Handler
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO) # Keep console slightly cleaner
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

# Create a default instance to import
logger = setup_logger()
