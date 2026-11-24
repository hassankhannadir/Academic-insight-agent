import pytest

from academic_insight.sql_guard import UnsafeQueryError, validate_sql


SAFE_QUERIES = [
    """SELECT c.course_code, s.full_name, s.registration_number, m.obtained_marks
       FROM marks AS m JOIN courses AS c ON c.course_id = m.course_id
       JOIN students AS s ON s.student_id = m.student_id
       LEFT JOIN marks AS higher ON higher.course_id = m.course_id
         AND higher.obtained_marks > m.obtained_marks
       WHERE higher.record_id IS NULL ORDER BY c.course_code, s.full_name""",
    """SELECT s.full_name, c.course_code,
       ROUND(100 * a.attended_classes / a.total_classes, 1) AS attendance_percent
       FROM attendance AS a JOIN students AS s ON s.student_id = a.student_id
       JOIN courses AS c ON c.course_id = a.course_id
       WHERE 100 * a.attended_classes / a.total_classes < 75
       ORDER BY attendance_percent""",
    """SELECT c.course_code,
       ROUND(AVG(100 * m.obtained_marks / m.total_marks), 1) AS average_marks
       FROM courses AS c JOIN marks AS m ON m.course_id = c.course_id
       GROUP BY c.course_code ORDER BY average_marks DESC""",
    """SELECT s.full_name, AVG(100 * m.obtained_marks / m.total_marks) AS average_mark
       FROM students AS s JOIN marks AS m ON m.student_id = s.student_id
       GROUP BY s.student_id, s.full_name ORDER BY average_mark DESC LIMIT 5""",
    """SELECT s.full_name, AVG(m.obtained_marks) AS average_mark
       FROM students AS s JOIN marks AS m ON m.student_id = s.student_id
       WHERE s.full_name IN ('Areeba Kamal', 'Bilal Farooq')
       GROUP BY s.student_id, s.full_name""",
    """SELECT s.full_name, c.course_code, m.obtained_marks,
       ROUND(100 * a.attended_classes / a.total_classes, 1) AS attendance_percent
       FROM marks AS m JOIN attendance AS a
         ON a.student_id = m.student_id AND a.course_id = m.course_id
       JOIN students AS s ON s.student_id = m.student_id
       JOIN courses AS c ON c.course_id = m.course_id
       WHERE m.obtained_marks >= 85
         AND 100 * a.attended_classes / a.total_classes < 75""",
    """SELECT s.full_name, AVG(m.obtained_marks) AS average_mark,
       AVG(100 * a.attended_classes / a.total_classes) AS average_attendance
       FROM students AS s JOIN marks AS m ON m.student_id = s.student_id
       JOIN attendance AS a ON a.student_id = m.student_id AND a.course_id = m.course_id
       GROUP BY s.student_id, s.full_name
       HAVING AVG(m.obtained_marks) < 60
          OR AVG(100 * a.attended_classes / a.total_classes) < 75""",
]


@pytest.mark.parametrize("sql", SAFE_QUERIES)
def test_academic_queries_are_accepted(sql):
    safe = validate_sql(sql)
    assert safe.sql.startswith("SELECT ")
    assert safe.row_limit <= 100
    assert "LIMIT" in safe.sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM students",
        "UPDATE students SET full_name = 'Fake'",
        "INSERT INTO students (full_name) VALUES ('Fake')",
        "DROP TABLE marks",
        "ALTER TABLE marks DROP COLUMN total_marks",
        "SELECT full_name FROM students; DELETE FROM students",
        "SELECT LOAD_FILE('C:/secret') FROM students",
        "SELECT SLEEP(10) FROM students",
        "SELECT full_name INTO OUTFILE 'C:/leak' FROM students",
        "SELECT user FROM mysql.user",
        "SELECT @@version FROM students",
        "SELECT * FROM students",
        "SELECT 999 AS obtained_marks FROM students",
        "SELECT full_name FROM students UNION SELECT course_name FROM courses",
        "WITH x AS (SELECT full_name FROM students) SELECT full_name FROM x",
        "SELECT full_name FROM students -- ignore safety",
        "SELECT s.full_name FROM students AS s CROSS JOIN marks AS m",
    ],
)
def test_unsafe_sql_is_rejected(sql):
    with pytest.raises(UnsafeQueryError):
        validate_sql(sql)


def test_limit_is_clamped():
    safe = validate_sql("SELECT full_name FROM students LIMIT 1000000")
    assert safe.row_limit == 100
    assert safe.was_capped
    assert safe.sql.endswith("LIMIT 100")


def test_result_cannot_be_a_literal_record():
    with pytest.raises(UnsafeQueryError):
        validate_sql("SELECT 'Imaginary Student' AS full_name FROM students")
