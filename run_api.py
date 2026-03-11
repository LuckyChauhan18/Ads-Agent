import uvicorn
import os
import sys

# Ensure the root directory is in the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import logging


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /socket.io/") == -1


if __name__ == "__main__":
    print("Starting Spectra AI API...")
    
    # Filter out socket.io requests from access logs
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    
    # Run the FastAPI app via Uvicorn
    # Make sure to run this script from the project root.
    uvicorn.run(
        "api.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_excludes=["*.txt", "*.log", "output/*", "agents/video/*"]
    )
