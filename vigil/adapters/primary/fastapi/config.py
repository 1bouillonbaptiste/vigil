from pathlib import Path

import yaml
from pydantic import BaseModel


class AppConfig(BaseModel):
    """Application configuration."""

    model: str = "yolov8n"

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load configuration from a YAML file."""
        return cls.model_validate(yaml.safe_load(path.read_text()))
