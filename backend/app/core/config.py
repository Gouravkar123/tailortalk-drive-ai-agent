import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LLM Configuration
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Google Drive Configuration
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = "credentials.json"
    GOOGLE_CREDENTIALS_JSON: Optional[str] = None  # Raw JSON string for cloud deploy
    DRIVE_FOLDER_ID: Optional[str] = None

    # App Configuration
    APP_NAME: str = "TailorTalk"
    DEBUG: bool = False
    BACKEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
