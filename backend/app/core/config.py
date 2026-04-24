from pathlib import Path
import os


class Settings:
    """Runtime configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        self.app_name = os.getenv("APP_NAME", "Bellini Scheduling API")
        self.api_prefix = os.getenv("API_PREFIX", "/api/v1")
        self.database_path = Path(
            os.getenv("DATABASE_PATH", self.project_root / "database.sqlite")
        ).resolve()
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        cors_origins_raw = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
        )
        self.cors_origins = [
            origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()
        ]


settings = Settings()
