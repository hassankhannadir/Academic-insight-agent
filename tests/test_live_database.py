import mysql.connector
import pytest

from academic_insight.config import load_database_settings
from academic_insight.database import AcademicDatabase, DatabaseAccessError
from academic_insight.sql_guard import SafeQuery, validate_sql


def test_live_database_connectivity_and_counts():
    db = AcademicDatabase(load_database_settings())
    query = validate_sql(
        "SELECT COUNT(*) AS student_count FROM students"
    )
    assert db.fetch(query)[0]["student_count"] == 30


def test_live_highest_marks_per_course_query():
    db = AcademicDatabase(load_database_settings())
    query = validate_sql(
        """SELECT c.course_code, s.full_name, m.obtained_marks
        FROM marks AS m JOIN courses AS c ON c.course_id = m.course_id
        JOIN students AS s ON s.student_id = m.student_id
        LEFT JOIN marks AS higher ON higher.course_id = m.course_id
          AND higher.obtained_marks > m.obtained_marks
        WHERE higher.record_id IS NULL ORDER BY c.course_code, s.full_name"""
    )
    rows = db.fetch(query)
    assert {row["course_code"] for row in rows} == {"CS101", "CS203", "CS305", "CS402", "CY501", "CY604"}


def test_live_account_cannot_update():
    settings = load_database_settings()
    connection = mysql.connector.connect(
        host=settings.host, port=settings.port, database=settings.database,
        user=settings.user, password=settings.password, connection_timeout=5,
    )
    try:
        cursor = connection.cursor()
        with pytest.raises(mysql.connector.Error) as error:
            cursor.execute("UPDATE students SET full_name = full_name WHERE student_id = 1")
        assert error.value.errno == 1142
    finally:
        connection.close()


def test_database_layer_rejects_unvalidated_sql():
    db = AcademicDatabase(load_database_settings())
    with pytest.raises(DatabaseAccessError, match="safety"):
        db.fetch(SafeQuery("DELETE FROM students", 100, False))
