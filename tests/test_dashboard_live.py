import mysql.connector

from academic_insight.analytics import calculate_metrics, prepare_dashboard_data
from academic_insight.config import load_database_settings
from academic_insight.database import AcademicDatabase


def test_live_dashboard_values_match_independent_sql_aggregates():
    settings = load_database_settings()
    snapshot = AcademicDatabase(settings).dashboard_snapshot()
    data = prepare_dashboard_data(snapshot)
    metrics = calculate_metrics(data)
    connection = mysql.connector.connect(
        host=settings.host, port=settings.port, database=settings.database,
        user=settings.user, password=settings.password, connection_timeout=5,
    )
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        students = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM courses")
        courses = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM marks")
        marks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance = cursor.fetchone()[0]
        cursor.execute("SELECT ROUND(AVG(100 * obtained_marks / NULLIF(total_marks, 0)), 2) FROM marks")
        average_marks = float(cursor.fetchone()[0])
        cursor.execute("SELECT ROUND(AVG(100 * attended_classes / NULLIF(total_classes, 0)), 2) FROM attendance")
        average_attendance = float(cursor.fetchone()[0])
        cursor.execute("""SELECT COUNT(*) FROM (
            SELECT student_id FROM attendance GROUP BY student_id
            HAVING 100 * SUM(attended_classes) / NULLIF(SUM(total_classes), 0) < 75
        ) AS low_students""")
        low_students = cursor.fetchone()[0]
    finally:
        connection.close()
    assert len(data.students) == students == metrics.total_students
    assert len(data.courses) == courses == metrics.total_courses
    assert len(data.marks) == marks
    assert len(data.attendance) == attendance
    assert metrics.average_marks_percent == average_marks
    assert metrics.average_attendance_percent == average_attendance
    assert metrics.students_below_75 == low_students


def test_live_dashboard_uses_read_only_account():
    settings = load_database_settings()
    assert settings.user == "academic_agent_ro"
    connection = mysql.connector.connect(
        host=settings.host, port=settings.port, database=settings.database,
        user=settings.user, password=settings.password, connection_timeout=5,
    )
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT CURRENT_USER()")
        assert cursor.fetchone()[0] == "academic_agent_ro@127.0.0.1"
        cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
        grants = [row[0] for row in cursor.fetchall()]
        assert any("GRANT SELECT ON `academic_db`.*" in grant for grant in grants)
        assert not any("GRANT UPDATE" in grant or "GRANT INSERT" in grant or "GRANT DELETE" in grant for grant in grants)
    finally:
        connection.close()
