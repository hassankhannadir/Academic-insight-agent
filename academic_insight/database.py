"""Read-only MariaDB access with server-side query timeouts."""

from __future__ import annotations

from typing import Any

import mysql.connector

from .config import DatabaseSettings
from .sql_guard import SafeQuery, UnsafeQueryError, validate_sql


STATEMENT_TIMEOUT_SECONDS = 3
MAX_DASHBOARD_ROWS = 10000

# Dashboard SQL is fixed. User-selected filters are applied to the resulting
# Pandas frames, so no user input is ever interpolated into these queries.
DASHBOARD_QUERIES = {
    "students": """SELECT student_id, full_name, registration_number, semester
                   FROM students ORDER BY registration_number LIMIT 10001""",
    "courses": """SELECT course_id, course_code, course_name, credit_hours
                  FROM courses ORDER BY course_code LIMIT 10001""",
    "marks": """SELECT m.record_id, s.student_id, s.full_name,
                       s.registration_number, s.semester, c.course_id,
                       c.course_code, c.course_name, m.obtained_marks, m.total_marks
                FROM marks AS m
                JOIN students AS s ON s.student_id = m.student_id
                JOIN courses AS c ON c.course_id = m.course_id
                ORDER BY c.course_code, s.registration_number LIMIT 10001""",
    "attendance": """SELECT a.record_id, s.student_id, s.full_name,
                            s.registration_number, s.semester, c.course_id,
                            c.course_code, c.course_name, a.attended_classes, a.total_classes
                     FROM attendance AS a
                     JOIN students AS s ON s.student_id = a.student_id
                     JOIN courses AS c ON c.course_id = a.course_id
                     ORDER BY c.course_code, s.registration_number LIMIT 10001""",
}


class DatabaseAccessError(Exception):
    """The approved database query could not be completed."""


class AcademicDatabase:
    def __init__(self, settings: DatabaseSettings):
        if settings.user != "academic_agent_ro" or settings.database != "academic_db":
            raise DatabaseAccessError("The academic database account is not allowed.")
        self.settings = settings

    def fetch(self, query: SafeQuery) -> list[dict[str, Any]]:
        """Execute an already validated SELECT using the dedicated account."""
        try:
            checked = validate_sql(query.sql, max_rows=query.row_limit)
        except UnsafeQueryError as exc:
            raise DatabaseAccessError("The academic query failed its safety check.") from exc
        if checked.sql != query.sql:
            raise DatabaseAccessError("The academic query failed its safety check.")
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
                host=self.settings.host,
                port=self.settings.port,
                database=self.settings.database,
                user=self.settings.user,
                password=self.settings.password,
                connection_timeout=5,
                read_timeout=5,
                write_timeout=5,
                autocommit=True,
            )
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT CURRENT_USER() AS authenticated_user")
            identity = cursor.fetchone()
            if identity is None or identity["authenticated_user"] != "academic_agent_ro@127.0.0.1":
                raise DatabaseAccessError("The database authenticated an unexpected account.")
            cursor.execute(
                f"SET STATEMENT max_statement_time={STATEMENT_TIMEOUT_SECONDS} FOR {query.sql}"
            )
            rows = cursor.fetchall()
            if len(rows) > query.row_limit:
                raise DatabaseAccessError("The result exceeded the allowed row limit.")
            return rows
        except mysql.connector.Error as exc:
            raise DatabaseAccessError("The academic database query could not be completed.") from exc
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    def dashboard_snapshot(self) -> dict[str, list[dict[str, Any]]]:
        """Retrieve four bounded reports through the dedicated SELECT-only account."""
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
                host=self.settings.host,
                port=self.settings.port,
                database=self.settings.database,
                user=self.settings.user,
                password=self.settings.password,
                connection_timeout=5,
                read_timeout=5,
                write_timeout=5,
                autocommit=True,
            )
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT CURRENT_USER() AS authenticated_user")
            identity = cursor.fetchone()
            if identity is None or identity["authenticated_user"] != "academic_agent_ro@127.0.0.1":
                raise DatabaseAccessError("The database authenticated an unexpected account.")
            snapshot: dict[str, list[dict[str, Any]]] = {}
            for name, sql in DASHBOARD_QUERIES.items():
                cursor.execute(
                    f"SET STATEMENT max_statement_time={STATEMENT_TIMEOUT_SECONDS} FOR {sql}"
                )
                rows = cursor.fetchall()
                if len(rows) > MAX_DASHBOARD_ROWS:
                    raise DatabaseAccessError("The academic dataset exceeds the dashboard row limit.")
                snapshot[name] = rows
            return snapshot
        except mysql.connector.Error as exc:
            raise DatabaseAccessError("The academic database query could not be completed.") from exc
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
