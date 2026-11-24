"""Calculations for the academic dashboard; no database or UI dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd


ATTENDANCE_THRESHOLD = 75.0
STUDENT_COLUMNS = ["student_id", "full_name", "registration_number", "semester"]
COURSE_COLUMNS = ["course_id", "course_code", "course_name", "credit_hours"]
MARK_COLUMNS = [
    "record_id", "student_id", "full_name", "registration_number", "semester",
    "course_id", "course_code", "course_name", "obtained_marks", "total_marks",
]
ATTENDANCE_COLUMNS = [
    "record_id", "student_id", "full_name", "registration_number", "semester",
    "course_id", "course_code", "course_name", "attended_classes", "total_classes",
]


@dataclass(frozen=True)
class DashboardData:
    students: pd.DataFrame
    courses: pd.DataFrame
    marks: pd.DataFrame
    attendance: pd.DataFrame


@dataclass(frozen=True)
class DashboardMetrics:
    total_students: int
    total_courses: int
    average_marks_percent: float | None
    average_attendance_percent: float | None
    students_below_75: int


def _frame(records: Iterable[dict[str, Any]], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame.from_records(list(records), columns=columns)


def prepare_dashboard_data(snapshot: dict[str, list[dict[str, Any]]]) -> DashboardData:
    students = _frame(snapshot.get("students", []), STUDENT_COLUMNS)
    courses = _frame(snapshot.get("courses", []), COURSE_COLUMNS)
    marks = _frame(snapshot.get("marks", []), MARK_COLUMNS)
    attendance = _frame(snapshot.get("attendance", []), ATTENDANCE_COLUMNS)

    for column in ("obtained_marks", "total_marks"):
        marks[column] = pd.to_numeric(marks[column], errors="coerce")
    for column in ("attended_classes", "total_classes"):
        attendance[column] = pd.to_numeric(attendance[column], errors="coerce")

    marks["marks_percent"] = (
        100 * marks["obtained_marks"] / marks["total_marks"].where(marks["total_marks"] > 0)
    ).round(2)
    attendance["attendance_percent"] = (
        100 * attendance["attended_classes"] /
        attendance["total_classes"].where(attendance["total_classes"] > 0)
    ).round(2)
    return DashboardData(students, courses, marks, attendance)


def student_attendance_summary(attendance: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "student_id", "full_name", "registration_number", "attended_classes",
        "total_classes", "attendance_percent", "below_75",
    ]
    if attendance.empty:
        return pd.DataFrame(columns=columns)
    summary = (
        attendance.groupby(["student_id", "full_name", "registration_number"], as_index=False)
        [["attended_classes", "total_classes"]]
        .sum()
    )
    summary["attendance_percent"] = (
        100 * summary["attended_classes"] /
        summary["total_classes"].where(summary["total_classes"] > 0)
    ).round(2)
    summary["below_75"] = summary["attendance_percent"] < ATTENDANCE_THRESHOLD
    return summary[columns]


def calculate_metrics(data: DashboardData) -> DashboardMetrics:
    def average(series: pd.Series) -> float | None:
        value = series.mean()
        return round(float(value), 2) if pd.notna(value) else None

    student_attendance = student_attendance_summary(data.attendance)
    return DashboardMetrics(
        total_students=int(data.students["student_id"].nunique()),
        total_courses=int(data.courses["course_id"].nunique()),
        average_marks_percent=average(data.marks["marks_percent"]),
        average_attendance_percent=average(data.attendance["attendance_percent"]),
        students_below_75=int(student_attendance["below_75"].sum()) if not student_attendance.empty else 0,
    )


def filter_records(frame: pd.DataFrame, course_ids: list[int], student_ids: list[int]) -> pd.DataFrame:
    if frame.empty or not course_ids or not student_ids:
        return frame.iloc[0:0].copy()
    return frame.loc[
        frame["course_id"].isin(course_ids) & frame["student_id"].isin(student_ids)
    ].copy()


def course_averages(frame: pd.DataFrame, percentage_column: str) -> pd.DataFrame:
    columns = ["course_id", "course_code", "course_name", "average_percent", "record_count"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    grouped = (
        frame.groupby(["course_id", "course_code", "course_name"], as_index=False)
        .agg(average_percent=(percentage_column, "mean"), record_count=(percentage_column, "count"))
        .sort_values("course_code")
    )
    grouped["average_percent"] = grouped["average_percent"].round(2)
    return grouped[columns]


def mark_extremes(marks: pd.DataFrame) -> pd.DataFrame:
    columns = ["course_code", "standing", "full_name", "registration_number", "marks_percent", "obtained_marks", "total_marks"]
    if marks.empty:
        return pd.DataFrame(columns=columns)
    valid = marks.dropna(subset=["marks_percent"])
    parts = []
    for _, group in valid.groupby("course_code", sort=True):
        high = group.loc[group["marks_percent"] == group["marks_percent"].max()].copy()
        low = group.loc[group["marks_percent"] == group["marks_percent"].min()].copy()
        high["standing"] = "Highest"
        low["standing"] = "Lowest"
        parts.extend([high, low])
    if not parts:
        return pd.DataFrame(columns=columns)
    return pd.concat(parts, ignore_index=True)[columns]


def export_filtered_records(data: DashboardData, marks: pd.DataFrame, attendance: pd.DataFrame) -> pd.DataFrame:
    keys = pd.concat(
        [marks[["student_id", "course_id"]], attendance[["student_id", "course_id"]]],
        ignore_index=True,
    ).drop_duplicates()
    columns = [
        "registration_number", "full_name", "semester", "course_code", "course_name",
        "obtained_marks", "total_marks", "marks_percent", "attended_classes",
        "total_classes", "attendance_percent",
    ]
    if keys.empty:
        return pd.DataFrame(columns=columns)
    output = (
        keys.merge(data.students, on="student_id", how="left")
        .merge(data.courses, on="course_id", how="left")
        .merge(marks[["student_id", "course_id", "obtained_marks", "total_marks", "marks_percent"]],
               on=["student_id", "course_id"], how="left")
        .merge(attendance[["student_id", "course_id", "attended_classes", "total_classes", "attendance_percent"]],
               on=["student_id", "course_id"], how="left")
        .sort_values(["course_code", "registration_number"])
    )
    return output[columns]


def to_safe_csv(frame: pd.DataFrame) -> bytes:
    """Escape spreadsheet formulas in untrusted text before CSV export."""
    safe = frame.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda value: "'" + value if isinstance(value, str)
            and value.lstrip().startswith(("=", "+", "-", "@")) else value
        )
    return safe.to_csv(index=False, na_rep="").encode("utf-8-sig")
