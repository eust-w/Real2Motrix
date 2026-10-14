from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Real2Motrix"
    host: str = "127.0.0.1"
    port: int = 8000
    database_path: Path = Field(default=Path("data/real2motrix.sqlite3"))
    data_dir: Path = Field(default=Path("data/projects"))
    output_dir: Path = Field(default=Path("outputs"))
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    worker_poll_seconds: float = 2.0

    model_config = SettingsConfigDict(
        env_prefix="REAL2MOTRIX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolved(self, base_dir: Path) -> "Settings":
        data = self.model_dump()
        for key in ("database_path", "data_dir", "output_dir"):
            value = Path(data[key])
            data[key] = value if value.is_absolute() else base_dir / value
        return Settings(**data)


def get_settings() -> Settings:
    return Settings().resolved(Path(__file__).resolve().parents[1])
