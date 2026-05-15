"""Main FastAPI application"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import init_db
from app.controllers import document_router, draft_router, edit_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("Starting Legal AI System")
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    yield
    
    logger.info("Shutting down Legal AI System")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Docker
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Legal AI System is running"}

# Include routers
app.include_router(document_router)
app.include_router(draft_router)
app.include_router(edit_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Legal AI Document Processing System",
        "version": settings.API_VERSION,
        "status": "active"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }

@app.get("/api/config")
async def get_config():
    """Get configuration info"""
    return {
        "draft_types": ["case_summary", "notice_summary", "checklist", "memo", "title_review"],
        "max_upload_size": settings.MAX_UPLOAD_SIZE,
        "supported_formats": list(settings.ALLOWED_EXTENSIONS),
        "chunk_size": settings.CHUNK_SIZE,
        "top_k_results": settings.TOP_K_RESULTS
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )