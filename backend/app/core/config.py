from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    blue_env: str = "development"
    blue_data_mode: str = "demo"
    blue_database_url: str = "sqlite:///./blue_rescue.db"
    blue_cache_dir: Path = Path("./data-cache")
    blue_demo_data_dir: Path = Path(__file__).resolve().parents[3] / "demo-data"
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
