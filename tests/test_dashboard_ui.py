from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from academic_insight.dashboard import load_dashboard_data
from academic_insight.database import AcademicDatabase, DatabaseAccessError


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_four_tabs_and_dashboard_work_without_groq(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    load_dashboard_data.clear()
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Ask Academic Insight", "Students", "Courses", "Academic Analytics"
    ]
    assert len(app.metric) == 5
    assert app.metric[0].value == "30"
    assert app.metric[1].value == "6"
    assert any("Groq API key" in info.value for info in app.info)


def test_course_filter_and_refresh_are_interactive():
    load_dashboard_data.clear()
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    course_filter = next(item for item in app.multiselect if item.label == "Courses")
    app = course_filter.set_value(["CS101"]).run()
    assert not app.exception
    extreme_table = next(
        item.value for item in app.dataframe if "Standing" in item.value.columns
    )
    assert set(extreme_table["Course"]) == {"CS101"}
    refresh = next(button for button in app.button if button.label == "Refresh data")
    app = refresh.click().run()
    assert not app.exception
    assert app.metric[0].value == "30"


def test_dashboard_handles_missing_records():
    load_dashboard_data.clear()
    try:
        with patch.object(AcademicDatabase, "dashboard_snapshot", return_value={
            "students": [], "courses": [], "marks": [], "attendance": [],
        }):
            app = AppTest.from_file(APP_PATH, default_timeout=30).run()
        assert not app.exception
        assert app.metric[0].value == "0"
        assert any("No student records" in item.value for item in app.info)
        assert any("Add student and course records" in item.value for item in app.info)
    finally:
        load_dashboard_data.clear()


def test_dashboard_handles_database_failure():
    load_dashboard_data.clear()
    try:
        with patch.object(AcademicDatabase, "dashboard_snapshot", side_effect=DatabaseAccessError("Database unavailable")):
            app = AppTest.from_file(APP_PATH, default_timeout=30).run()
        assert not app.exception
        assert len(app.error) >= 3
        assert all("Database unavailable" in item.value for item in app.error)
    finally:
        load_dashboard_data.clear()
