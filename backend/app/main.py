from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from app.api import api_router
from app.database.base import Base
from app.database.session import engine
import app.models  # Ensure all models are registered

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="HomeRepair AI API",
    description="Backend API for HomeRepair AI agent system",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Welcome to HomeRepair AI API",
        "docs": "/docs",
        "health": "/api/health"
    }
