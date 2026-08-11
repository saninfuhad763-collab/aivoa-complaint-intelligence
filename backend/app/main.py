from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router
from app.api.analysis import router as analysis_router
from app.api.complaints import router as complaints_router

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
# Analysis router must be registered before complaints router so that
# /api/complaints/analyze is matched before /api/complaints/{complaint_id}.
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(complaints_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "Welcome to AIVOA Complaint Intelligence API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "complaints": f"{settings.API_V1_STR}/complaints"
    }
