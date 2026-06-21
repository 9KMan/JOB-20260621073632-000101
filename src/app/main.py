// src/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from src.app.config import settings
from src.app.database import engine, Base
from src.api.v1 import routes
from src.models.models import PurchaseOrder, Invoice, DeliveryNote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="3-Way Matching Engine for Accounts Payable Automation",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include API routes
app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
