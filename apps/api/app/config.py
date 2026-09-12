import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Sports News AI API"
    app_version: str = "0.1.0"
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sports_news_ai")
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    environment: str = os.getenv("ENVIRONMENT", "development")


settings = Settings()
