import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    # Database settings - SQLite by default, easily swapped to postgresql+asyncpg://...
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'app.db'}"

    # Authentication settings
    # APP_USERS format: "username:password,user2:pass2"
    APP_USERS: str = "admin:admin123,kvothe:password123"
    JWT_SECRET: str = "super-secret-jwt-key-for-project-a-production-2026-safe"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # LLM Provider Keys
    GEMINI_API_KEY: Optional[str] = None
    NVIDIA_NIM_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Default model parameters
    DEFAULT_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-3.5-flash"
    DEFAULT_N_TURNS: int = 5
    
    # Threshold in estimated tokens to decide direct injection vs tool retrieval
    MAX_DIRECT_CONTEXT_TOKENS: int = 2500

    @property
    def parsed_users(self) -> Dict[str, str]:
        """Parse APP_USERS string into a dictionary of {username: password}."""
        users = {}
        if not self.APP_USERS:
            return users
        for pair in self.APP_USERS.split(","):
            pair = pair.strip()
            if ":" in pair:
                username, password = pair.split(":", 1)
                users[username.strip()] = password.strip()
        return users

settings = Settings()
