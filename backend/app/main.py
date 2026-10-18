import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_models import router as models_router
from app.api.routes_threads import router as threads_router
from app.config import settings
from app.db.init_db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Auto-initialize SQLAlchemy database tables
    logger.info("Starting up FastAPI application...")
    await init_db()
    yield
    # Shutdown: Clean up resources
    logger.info("Shutting down FastAPI application...")
    from app.db.session import engine
    await engine.dispose()

app = FastAPI(
    title="Multi-Turn Chatbot API",
    description="Production-grade AI Chatbot backend with LangGraph, hybrid document reading, and streaming.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # Allows all origins for local dev flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(models_router)
app.include_router(threads_router)
app.include_router(documents_router)
app.include_router(chat_router)

@app.get("/api/health")
async def health_check():
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "database": settings.DATABASE_URL.split("://")[0],
        "default_provider": settings.DEFAULT_PROVIDER,
        "default_model": settings.DEFAULT_MODEL,
        "n_turns": settings.DEFAULT_N_TURNS,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
