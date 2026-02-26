"""Configuration management for paper-tracker."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Settings:
    """Application settings."""

    # API Keys
    anthropic_api_key: str | None = None

    # Categories to track
    categories: list[str] = field(
        default_factory=lambda: ["cs.AI", "cs.LG", "cs.CL", "cs.SE", "cs.CR"]
    )

    # Keywords to filter papers
    keywords: list[str] = field(default_factory=list)

    # Paths
    config_dir: Path = field(default_factory=lambda: Path.home() / ".paper-tracker")
    data_dir: Path = field(default_factory=lambda: Path.home() / ".paper-tracker" / "data")
    reports_dir: Path = field(
        default_factory=lambda: Path.home() / ".paper-tracker" / "reports"
    )

    # Database
    db_path: Path = field(init=False)

    # ArXiv settings
    arxiv_base_url: str = "http://export.arxiv.org/api/query"

    # Summarization settings
    max_papers_per_batch: int = 10
    summary_model: str = "claude-sonnet-4-6"

    def __post_init__(self):
        """Set derived paths."""
        # Set db_path based on data_dir
        object.__setattr__(self, "db_path", self.data_dir / "papers.db")

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, path: Path | str | None = None) -> "Settings":
        """Load settings from YAML file.

        Args:
            path: Path to config file. If None, uses default location.

        Returns:
            Settings instance
        """
        if path is None:
            path = Path.home() / ".paper-tracker" / "config.yaml"
        else:
            path = Path(path)

        if not path.exists():
            return cls()

        with path.open() as f:
            data = yaml.safe_load(f) or {}

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables.

        Returns:
            Settings instance
        """
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    def merge(self, other: "Settings") -> "Settings":
        """Merge another settings instance into this one.

        Args:
            other: Settings to merge from

        Returns:
            New Settings instance with merged values
        """
        result = Settings()
        for key in self.__dataclass_fields__:
            self_val = getattr(self, key)
            other_val = getattr(other, key)

            # Use other value if set, otherwise use self value
            if other_val is not None and other_val != []:
                if isinstance(other_val, list) and other_val == []:
                    setattr(result, key, self_val)
                else:
                    setattr(result, key, other_val)
            else:
                setattr(result, key, self_val)

        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dataclass_fields__.items()
            if not k.startswith("_")
        }


def load_config() -> Settings:
    """Load configuration from file and environment.

    Environment variables take precedence over file settings.

    Returns:
        Settings instance
    """
    file_settings = Settings.from_yaml()
    env_settings = Settings.from_env()
    return file_settings.merge(env_settings)
