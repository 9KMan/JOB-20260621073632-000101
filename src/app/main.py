// src/app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import time
from typing import Callable

from src.app.config import get_settings
from src.app.database import engine, Base
from src.api.v1 import router as api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="3-Way Matching Engine for Invoice × Delivery Note × Purchase Order",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> JSONResponse:
    """Log all incoming requests and their processing time."""
    start_time = time.time()
    request_id = f"{int(start_time * 1000000)}"
    
    logger.info(
        f"Request started | ID: {request_id} | Method: {request.method} | "
        f"Path: {request.url.path}"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed | ID: {request_id} | Status: {response.status_code} | "
            f"Duration: {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed | ID: {request_id} | Error: {str(e)} | "
            f"Duration: {process_time:.3f}s"
        )
        raise


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "body": exc.body,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "An error occurred while processing your request.",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.exception(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize resources on startup."""
    logger.info("Starting FinaRo AP Automation Engine...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables created/verified")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup resources on shutdown."""
    logger.info("Shutting down FinaRo AP Automation Engine...")
    engine.dispose()
    logger.info("Database connections closed")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
