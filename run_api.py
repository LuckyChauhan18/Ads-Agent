import uvicorn
import os
import sys

# Ensure the root directory is in the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

if __name__ == "__main__":
    print("Starting AI Ad Generator API...")
    # Run the FastAPI app via Uvicorn
    # Make sure to run this script from the project root.
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
