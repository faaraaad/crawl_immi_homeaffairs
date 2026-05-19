from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    BASE_URL: str = "https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list"
    CONCURRENCY: int = 4
    OUTPUT_DIR: str = "output"
    PAGE_LOAD_TIMEOUT: int = 30000  # In milliseconds (30 seconds)
    
    # Infrastructure Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/immi_crawler"
    CHROMEDRIVER_ADDR: Optional[str] = "/usr/lib/chromium-browser/chromedriver"
    
    # Output Settings
    OUTPUT_FORMAT: str = "postgres"  # Choice of: json, csv, sqlite, postgres
    
    # Notification Settings
    NOTIFIER_BACKEND: str = "email"  # email, telegram, both
    
    # SMTP Configuration (defaults for local dev using Mailpit / standard SMTP)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SENDER: str = "crawler@example.com"
    SMTP_RECIPIENT: str = "admin@example.com"
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Load from .env file at workspace root
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure output directory exists
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
