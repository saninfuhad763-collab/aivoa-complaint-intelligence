from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AIVOA Complaint Intelligence"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/aivoa_complaints"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "gemma2-9b-it"
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
