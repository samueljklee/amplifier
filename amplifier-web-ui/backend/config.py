from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AMPLIFIER_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Amplifier Web UI"
    version: str = "0.1.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Paths
    scenarios_path: Path = Field(default_factory=lambda: (Path(__file__).parent.parent.parent / "scenarios").absolute())
    data_path: Path = Field(default_factory=lambda: (Path(__file__).parent.parent / ".data").absolute())

    # Execution limits
    max_concurrent_executions: int = 10
    execution_timeout: int = 3600

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 100

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
