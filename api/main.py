from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Load environment variables before any other imports that might use them
load_dotenv()

from api.routes.inputs import router as inputs_router
from api.routes.outputs import router as outputs_router
from api.routes.workflow import router as workflow_router
from api.routes.ai_assist import router as ai_assist_router
from api.routes.files import router as files_router
from api.routes.auth import router as auth_router

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="AI Ad Generator API",
    description="Backend API for the automated ad generation pipeline",
    version="1.0.0",
)

@app.middleware("http")
async def log_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        with open("global_error_log.txt", "a") as f:
            f.write(f"\n\n--- ERROR AT {os.path.basename(__file__)} ---\n")
            f.write(traceback.format_exc())
        raise e

@app.on_event("startup")
async def startup_db_client():
    # Connect to MongoDB for all storage requirements
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Specific origin required when allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount Static Files
app.mount("/videos", StaticFiles(directory=os.path.join(BASE_DIR, "agents", "video")), name="videos")
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets")

# Include Routers
app.include_router(auth_router)
app.include_router(files_router)
app.include_router(inputs_router)
app.include_router(outputs_router)
app.include_router(workflow_router)
app.include_router(ai_assist_router)

@app.get("/", tags=["Health"])
def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok", "message": "AI Ad Generator API is running"}
