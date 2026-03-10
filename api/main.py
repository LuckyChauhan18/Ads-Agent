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
from api.routes.analytics import router as analytics_router
from api.routes.publish import router as publish_router

from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection
from api.services.memory_service import connect_to_ltm, close_ltm_connection

app = FastAPI(
    title="Spectra AI API",
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
    await connect_to_mongo()
    await connect_to_ltm()
    # Initialize analytics & publish indexes
    from api.services.analytics_service import init_analytics_indexes
    from api.services.publish_service import init_publish_indexes
    await init_analytics_indexes()
    await init_publish_indexes()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
    await close_ltm_connection()

# Enable CORS for frontend integration
# IMPORTANT: CORSMiddleware must be added last or near last to wrap other middlewares?
# Actually, in FastAPI, middleware is executed in reverse order of addition for the response.
# So adding it last means it wraps everything else and can add headers to the final response.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_msg = traceback.format_exc()
    with open("global_error_log.txt", "a") as f:
        f.write(f"\n\n--- GLOBAL EXCEPTION HANDLER ---\n")
        f.write(error_msg)
    
    # Return a JSON response that the frontend can actually read
    origin = request.headers.get("origin")
    # If no origin, fallback to one of the allowed origins
    if not origin or origin not in ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"]:
        origin = "http://localhost:5173"

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
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
app.include_router(analytics_router)
app.include_router(publish_router)

@app.get("/", tags=["Health"])
def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok", "message": "Spectra AI API is running"}
