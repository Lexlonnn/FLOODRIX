"""FastAPI application initialization, lifecycle state management, and router assembly."""

from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.predictor import FloodPredictor
from app.routers import (
    alerts,
    closures,
    health,
    map_risk,
    predict,
    routes,
    simulation,
    trips,
    weather,
)
from app.services.closure_service import ClosureService
from ml.config import METADATA_FILE, MODEL_FILE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("floodrix.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: loads ML model once and initializes shared services."""
    logger.info("Initializing FLOODRIX Backend lifespan...")
    
    # 1. Initialize Predictor
    predictor = FloodPredictor(model_path=MODEL_FILE, metadata_path=METADATA_FILE)
    try:
        predictor.load()
    except Exception as e:
        logger.error(f"FATAL: Failed to load model artifacts: {e}")
        # Loud failure as mandated by plan.md
        raise RuntimeError(f"Startup failed: Unable to load flood prediction model artifacts: {e}") from e

    app.state.predictor = predictor
    app.state.closure_service = ClosureService()
    logger.info("FLOODRIX Backend successfully initialized and ready for inference.")

    yield

    logger.info("Shutting down FLOODRIX Backend...")


# Initialize FastAPI application
app = FastAPI(
    title="FLOODRIX: Flood-Aware Logistics Planner ML Backend",
    description=(
        "AI-Powered Flood Hazard Prediction & Resilient Logistics Routing API for Kerala. "
        "Scores calibrated flood probabilities for road segments and optimizes logistics routes."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 1. CORS Middleware (allows Flutter web, emulator, and mobile clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Latency and Request Logging Middleware
@app.middleware("http")
async def latency_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f} ms)")
    return response


# 3. Mount Direct Root Endpoints (as defined in model-plan.md)
app.include_router(health.router)
app.include_router(predict.router)

# 4. Mount /api/v1 Prefix (as defined in FLOODRIX Mobile API Specification)
app.include_router(health.router, prefix="/api/v1")
app.include_router(predict.router, prefix="/api/v1")
app.include_router(routes.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")
app.include_router(map_risk.router, prefix="/api/v1")
app.include_router(closures.router, prefix="/api/v1")
app.include_router(trips.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "service": "FLOODRIX Flood-Aware Logistics Planner",
        "status": "online",
        "documentation": "/docs",
        "api_v1": "/api/v1",
    }
