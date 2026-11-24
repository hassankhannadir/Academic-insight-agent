import csv
import io
import math

import pandas as pd

from academic_insight.analytics import (
    calculate_metrics, course_averages, export_filtered_records, filter_records,
    mark_extremes, prepare_dashboard_data, student_attendance_summary, to_safe_csv,
)


def sample_snapshot():
    return {
        "students": [
            {"student_id": 1, "full_name": "Areeba", "registration_number": "CS-001", "semester": 5},
            {"student_id": 2, "full_name": "Bilal", "registration_number": "CS-002", "semester": 5},
        ],
        "courses": [
            {"course_id": 1, "course_code": "CS101", "course_name": "Programming", "credit_hours": 3},
            {"course_id": 2, "course_code": "CY501", "course_name": "Security", "credit_hours": 3},
        ],
        "marks": [
            {"record_id": 1, "student_id": 1, "full_name": "Areeba", "registration_number": "CS-001", "semester": 5,
             "course_id": 1, "course_code": "CS101", "course_name": "Programming", "obtained_marks": 35, "total_marks": 50},
            {"record_id": 2, "student_id": 2, "full_name": "Bilal", "registration_number": "CS-002", "semester": 5,
             "course_id": 1, "course_code": "CS101", "course_name": "Programming", "obtained_marks": 18, "total_marks": 20},
            {"record_id": 3, "student_id": 1, "full_name": "Areeba", "registration_number": "CS-001", "semester": 5,
             "course_id": 2, "course_code": "CY501", "course_name": "Security", "obtained_marks": 40, "total_marks": 50},
        ],
        "attendance": [
            {"record_id": 1, "student_id": 1, "full_name": "Areeba", "registration_number": "CS-001", "semester": 5,
             "course_id": 1, "course_code": "CS101", "course_name": "Programming", "attended_classes": 7, "total_classes": 10},
            {"record_id": 2, "student_id": 2, "full_name": "Bilal", "registration_number": "CS-002", "semester": 5,
             "course_id": 1, "course_code": "CS101", "course_name": "Programming", "attended_classes": 9, "total_classes": 10},
            {"record_id": 3, "student_id": 1, "full_name": "Areeba", "registration_number": "CS-001", "semester": 5,
             "course_id": 2, "course_code": "CY501", "course_name": "Security", "attended_classes": 0, "total_classes": 0},
        ],
    }


def test_percentages_normalize_different_totals_and_skip_zero_classes():
    data = prepare_dashboard_data(sample_snapshot())
    assert data.marks["marks_percent"].tolist() == [70.0, 90.0, 80.0]
    assert data.attendance["attendance_percent"].iloc[:2].tolist() == [70.0, 90.0]
    assert math.isnan(data.attendance["attendance_percent"].iloc[2])
    metrics = calculate_metrics(data)
    assert metrics.total_students == 2
    assert metrics.total_courses == 2
    assert metrics.average_marks_percent == 80.0
    assert metrics.average_attendance_percent == 80.0
    assert metrics.students_below_75 == 1
    summary = student_attendance_summary(data.attendance)
    assert summary.loc[summary["student_id"] == 1, "attendance_percent"].item() == 70.0


def test_filters_averages_and_extremes():
    data = prepare_dashboard_data(sample_snapshot())
    filtered = filter_records(data.marks, [1], [1, 2])
    assert len(filtered) == 2
    assert set(filtered["course_code"]) == {"CS101"}
    averages = course_averages(filtered, "marks_percent")
    assert averages["average_percent"].item() == 80.0
    extremes = mark_extremes(filtered)
    assert set(zip(extremes["standing"], extremes["full_name"])) == {
        ("Highest", "Bilal"), ("Lowest", "Areeba")
    }
    assert filter_records(data.marks, [], [1]).empty


def test_csv_export_uses_filtered_rows_and_escapes_formulas():
    snapshot = sample_snapshot()
    snapshot["students"][0]["full_name"] = "=HYPERLINK(\"https://example.com\")"
    snapshot["marks"][0]["full_name"] = snapshot["students"][0]["full_name"]
    snapshot["attendance"][0]["full_name"] = snapshot["students"][0]["full_name"]
    data = prepare_dashboard_data(snapshot)
    marks = filter_records(data.marks, [1], [1])
    attendance = filter_records(data.attendance, [1], [1])
    exported = export_filtered_records(data, marks, attendance)
    assert len(exported) == 1
    assert exported["marks_percent"].item() == 70.0
    row = next(csv.DictReader(io.StringIO(to_safe_csv(exported).decode("utf-8-sig"))))
    assert row["full_name"].startswith("'=HYPERLINK")
    assert row["course_code"] == "CS101"


def test_missing_data_is_safe():
    data = prepare_dashboard_data({"students": [], "courses": [], "marks": [], "attendance": []})
    metrics = calculate_metrics(data)
    assert metrics.total_students == 0
    assert metrics.average_marks_percent is None
    assert metrics.average_attendance_percent is None
    assert mark_extremes(data.marks).empty
    assert export_filtered_records(data, data.marks, data.attendance).empty
