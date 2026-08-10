from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])


@app.get("/")
def root():
    return {
        "message": "Welcome to AIVOA Complaint Intelligence API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
