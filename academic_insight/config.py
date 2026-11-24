"""Separate, validated database and Groq settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConfigurationError(Exception):
    """A required local setting is missing or unsafe."""


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)


@dataclass(frozen=True)
class GroqSettings:
    api_key: str = field(repr=False)
    model: str = ""

    @property
    def ready(self) -> bool:
        return bool(self.api_key and self.model)


def _settings(path: Path, keys: tuple[str, ...]) -> dict[str, str]:
    file_values = dotenv_values(path) if path.exists() else {}
    return {key: str(os.environ.get(key, file_values.get(key) or "")).strip() for key in keys}


def load_database_settings(path: Path | None = None) -> DatabaseSettings:
    values = _settings(
        path or PROJECT_ROOT / ".env",
        ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"),
    )
    if values["DB_HOST"] != "127.0.0.1" or values["DB_NAME"] != "academic_db":
        raise ConfigurationError("Academic database settings must point to local academic_db.")
    if values["DB_USER"] != "academic_agent_ro":
        raise ConfigurationError("The academic agent must use its dedicated read-only account.")
    if not values["DB_PASSWORD"]:
        raise ConfigurationError("The academic database password is missing from .env.")
    try:
        port = int(values["DB_PORT"])
    except ValueError as exc:
        raise ConfigurationError("The academic database port is invalid.") from exc
    if not 1 <= port <= 65535:
        raise ConfigurationError("The academic database port is invalid.")
    return DatabaseSettings(
        host=values["DB_HOST"],
        port=port,
        database=values["DB_NAME"],
        user=values["DB_USER"],
        password=values["DB_PASSWORD"],
    )


def load_groq_settings(path: Path | None = None) -> GroqSettings:
    values = _settings(path or PROJECT_ROOT / ".env.groq", ("GROQ_API_KEY", "GROQ_MODEL"))
    return GroqSettings(api_key=values["GROQ_API_KEY"], model=values["GROQ_MODEL"])
