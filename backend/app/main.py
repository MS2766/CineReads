from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path

from app.routers import recommendations
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 CineReads API starting up...")
    
    # Ensure cache directory exists
    cache_dir = Path(settings.cache_dir)
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / "recommendations").mkdir(exist_ok=True)
    (cache_dir / "books").mkdir(exist_ok=True)
    
    print(f"📁 Cache directory: {cache_dir.absolute()}")
    print(f"🔑 OpenAI API key: {'✅ Set' if settings.openai_api_key else '❌ Missing'}")
    print(f"🔑 Hardcover API key: {'✅ Set' if settings.hardcover_api_key else '❌ Missing'}")
    
    yield
    
    # Shutdown
    print("👋 CineReads API shutting down...")

app = FastAPI(
    title="CineReads API", 
    version="1.0.0",
    description="Turn your favorite movies into book recommendations",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative dev port
        "https://cinereads.vercel.app",  # Production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"}
        )

# Include routers
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])

@app.get("/")
async def root():
    return {
        "message": "CineReads API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    cache_dir = Path(settings.cache_dir)
    
    return {
        "status": "healthy",
        "cache_dir_exists": cache_dir.exists(),
        "openai_configured": bool(settings.openai_api_key),
        "hardcover_configured": bool(settings.hardcover_api_key),
        "debug_mode": settings.debug
    }