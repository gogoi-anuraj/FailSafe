"""
FAILSAFE — App Configuration
Loads all settings from environment variables or .env file.
In production (Render), env vars are set in the dashboard.
In development, they are loaded from .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_HOST    : str = "localhost"
    DB_PORT    : int = 5432
    DB_NAME    : str = "failsafe_db"
    DB_USER    : str = "postgres"
    DB_PASSWORD: str = ""

    # Supabase / production: set DATABASE_URL directly instead of
    # individual DB_* vars. If set, it overrides the constructed URL.
    DATABASE_URL_OVERRIDE: str = ""

    # JWT
    JWT_SECRET        : str = "changeme"
    JWT_ALGORITHM     : str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL  : str = "llama-3.3-70b-versatile"

    # App
    APP_ENV        : str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def DATABASE_URL(self) -> str:
        # If a full URL is provided (e.g. from Supabase/Render), use it directly
        if self.DATABASE_URL_OVERRIDE:
            url = self.DATABASE_URL_OVERRIDE
            # Ensure psycopg2 driver is specified
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and "+psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        # Otherwise build from individual vars (local development)
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def origins(self) -> list:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    class Config:
        env_file = ".env"


settings = Settings()
