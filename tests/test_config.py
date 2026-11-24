import pytest

from academic_insight.config import (
    ConfigurationError,
    load_database_settings,
    load_groq_settings,
)


def test_missing_groq_configuration_is_graceful(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    config = tmp_path / ".env.groq"
    config.write_text("GROQ_API_KEY=\nGROQ_MODEL=\n", encoding="utf-8")
    assert not load_groq_settings(config).ready


def test_database_configuration_rejects_admin_account(tmp_path, monkeypatch):
    for name in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    config = tmp_path / ".env"
    config.write_text(
        "DB_HOST=127.0.0.1\nDB_PORT=3306\nDB_NAME=academic_db\nDB_USER=root\nDB_PASSWORD=bad\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="read-only account"):
        load_database_settings(config)
