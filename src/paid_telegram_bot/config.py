"""Configuration management — loads from environment variables and JSON config file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


DEFAULT_DATA_DIR = Path.home() / ".paid-telegram-bot"
CONFIG_FILE = "config.json"


@dataclass
class BotConfig:
    """Bot-specific configuration."""
    token: str = ""
    access_mode: str = "open"  # whitelist | open | approval
    group_mode: bool = False
    group_activation: str = "mention"  # mention | command
    welcome_message: str = "Welcome! I'm powered by an AI agent."
    max_outbound_per_hour_free: int = 50


@dataclass
class ServerConfig:
    """Top-level server configuration."""
    data_dir: str = str(DEFAULT_DATA_DIR)
    bot: BotConfig = field(default_factory=BotConfig)
    owner_chat_id: Optional[int] = None

    # Derived paths
    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def db_path(self) -> Path:
        return self.data_path / "data.db"

    @property
    def files_path(self) -> Path:
        return self.data_path / "files"

    @property
    def config_file_path(self) -> Path:
        return self.data_path / CONFIG_FILE

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.files_path.mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        """Persist configuration to JSON file."""
        self.ensure_dirs()
        data = asdict(self)
        with open(self.config_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls) -> "ServerConfig":
        """Load configuration from environment + JSON file.

        Priority: environment variables > JSON file > defaults.
        """
        config = cls()

        # Load from JSON if it exists
        if config.config_file_path.exists():
            try:
                with open(config.config_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "data_dir" in data:
                    config.data_dir = data["data_dir"]
                if "owner_chat_id" in data:
                    config.owner_chat_id = data["owner_chat_id"]
                if "bot" in data:
                    bot_data = data["bot"]
                    for key in ("token", "access_mode", "group_mode",
                                "group_activation", "welcome_message",
                                "max_outbound_per_hour_free"):
                        if key in bot_data:
                            setattr(config.bot, key, bot_data[key])
            except (json.JSONDecodeError, OSError):
                pass

        # Environment overrides
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if token:
            config.bot.token = token

        data_dir = os.environ.get("PAID_TELEGRAM_BOT_DATA_DIR", "")
        if data_dir:
            config.data_dir = data_dir

        owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
        if owner:
            try:
                config.owner_chat_id = int(owner)
            except ValueError:
                pass

        config.ensure_dirs()
        return config


# Singleton
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = ServerConfig.load()
    return _config


def reset_config() -> None:
    """Reset the global configuration (for testing)."""
    global _config
    _config = None
