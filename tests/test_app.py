from unittest.mock import patch
from pathlib import Path

from streamlit.testing.v1 import AppTest

from academic_insight.agent import AcademicInsightAgent

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_streamlit_shows_missing_groq_configuration(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    app = AppTest.from_file(APP_PATH, default_timeout=20).run()
    assert not app.exception
    assert any("Groq API key" in item.value for item in app.info)


def test_streamlit_chat_uses_live_database_with_mocked_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "mock-key")
    monkeypatch.setenv("GROQ_MODEL", "mock-model")
    sql = "SELECT full_name, registration_number FROM students ORDER BY student_id LIMIT 2"
    with patch.object(AcademicInsightAgent, "_complete", side_effect=[sql, '{"highlight_rows":[1,2]}']):
        app = AppTest.from_file(APP_PATH, default_timeout=20).run()
        suggestion = next(button for button in app.button if button.label == "Who scored the highest marks in each course?")
        app = suggestion.click().run()
    assert not app.exception
    assert any("Found 2 matching records" in item.value for item in app.markdown)
    assert any(
        list(element.value.columns) == ["full_name", "registration_number"]
        for element in app.dataframe
    )
