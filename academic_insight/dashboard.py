"""Streamlit views for the academic directory and analytics dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .analytics import (
    DashboardData, calculate_metrics, course_averages, export_filtered_records,
    filter_records, mark_extremes, prepare_dashboard_data,
    student_attendance_summary, to_safe_csv,
)
from .charts import (
    attendance_heatmap, average_marks_by_course, course_attendance_comparison, marks_by_course,
    student_attendance_comparison, student_marks_comparison,
)
from .config import load_database_settings
from .database import AcademicDatabase


@st.cache_data(ttl=60, show_spinner=False)
def load_dashboard_data() -> DashboardData:
    """Cache a live read-only snapshot for one minute; refresh can clear it."""
    raw = AcademicDatabase(load_database_settings()).dashboard_snapshot()
    return prepare_dashboard_data(raw)


def render_students(data: DashboardData) -> None:
    st.subheader("Students")
    st.caption("Current student roster from academic_db.")
    if data.students.empty:
        st.info("No student records are available.")
        return
    semesters = sorted(data.students["semester"].dropna().unique().tolist())
    chosen = st.multiselect("Semester", semesters, default=semesters, key="student_semesters")
    shown = data.students.loc[data.students["semester"].isin(chosen)]
    st.dataframe(
        shown[["registration_number", "full_name", "semester"]].rename(columns={
            "registration_number": "Registration number", "full_name": "Student", "semester": "Semester",
        }),
        hide_index=True, width="stretch",
    )


def render_courses(data: DashboardData) -> None:
    st.subheader("Courses")
    st.caption("Courses available for academic analysis.")
    if data.courses.empty:
        st.info("No course records are available.")
        return
    st.dataframe(
        data.courses[["course_code", "course_name", "credit_hours"]].rename(columns={
            "course_code": "Code", "course_name": "Course", "credit_hours": "Credit hours",
        }),
        hide_index=True, width="stretch",
    )


def _percentage(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}%"


def _show_plot(figure) -> None:
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def render_analytics(data: DashboardData) -> None:
    header, action = st.columns([5, 1])
    with header:
        st.subheader("Academic Analytics")
        st.caption("Live academic records. Filters below update charts and export; summary metrics cover all records.")
    with action:
        if st.button("Refresh data", key="refresh_analytics", width="stretch"):
            load_dashboard_data.clear()
            st.rerun()

    metrics = calculate_metrics(data)
    metric_columns = st.columns(5)
    labels_and_values = [
        ("Students", str(metrics.total_students)),
        ("Courses", str(metrics.total_courses)),
        ("Average marks", _percentage(metrics.average_marks_percent)),
        ("Average attendance", _percentage(metrics.average_attendance_percent)),
        ("Below 75% overall", str(metrics.students_below_75)),
    ]
    for column, (label, value) in zip(metric_columns, labels_and_values):
        with column:
            st.metric(label, value)
    st.caption("The low-attendance KPI uses each student's total attended classes divided by total scheduled classes.")

    if data.students.empty or data.courses.empty:
        st.info("Add student and course records to see the dashboard.")
        return

    course_options = dict(zip(data.courses["course_code"], data.courses["course_id"]))
    student_options = {
        f"{row.full_name} ({row.registration_number})": int(row.student_id)
        for row in data.students.itertuples()
    }
    st.divider()
    st.markdown("#### Filter records")
    course_column, student_column = st.columns(2)
    with course_column:
        selected_course_codes = st.multiselect(
            "Courses", list(course_options), default=list(course_options), key="analytics_courses"
        )
    with student_column:
        selected_student_labels = st.multiselect(
            "Students (leave blank for all)", list(student_options), key="analytics_students"
        )
    course_ids = [int(course_options[code]) for code in selected_course_codes]
    student_ids = (
        [student_options[label] for label in selected_student_labels]
        if selected_student_labels else list(student_options.values())
    )
    marks = filter_records(data.marks, course_ids, student_ids)
    attendance = filter_records(data.attendance, course_ids, student_ids)
    if marks.empty and attendance.empty:
        st.info("No records match these filters. Select another course or student.")
        return

    st.divider()
    st.markdown("### Course-wise student marks")
    if marks.empty or marks["marks_percent"].notna().sum() == 0:
        st.info("No valid marks are available for these filters.")
    else:
        average_marks = course_averages(marks, "marks_percent")
        left, right = st.columns([1.5, 1])
        with left:
            st.markdown("**Individual student marks**")
            _show_plot(marks_by_course(marks))
            st.caption("Green marks the highest score in a course; red marks the lowest. Hover for student details.")
        with right:
            st.markdown("**Average marks by course**")
            _show_plot(average_marks_by_course(average_marks))

        st.markdown("**Highest and lowest scoring students**")
        st.dataframe(
            mark_extremes(marks).rename(columns={
                "course_code": "Course", "standing": "Standing", "full_name": "Student",
                "registration_number": "Registration number", "marks_percent": "Marks (%)",
                "obtained_marks": "Obtained", "total_marks": "Total",
            }),
            hide_index=True, width="stretch",
        )
        comparison_options = {
            label: student_id for label, student_id in student_options.items()
            if student_id in student_ids and student_id in set(marks["student_id"])
        }
        chosen_comparison = st.multiselect(
            "Compare up to five students", list(comparison_options),
            default=list(comparison_options)[:2], max_selections=5,
            key="analytics_compare_students",
        )
        if chosen_comparison:
            _show_plot(student_marks_comparison(
                marks, [comparison_options[label] for label in chosen_comparison]
            ))
        else:
            st.info("Choose students to compare their marks across courses.")

    st.divider()
    st.markdown("### Attendance comparison")
    if attendance.empty or attendance["attendance_percent"].notna().sum() == 0:
        st.info("No valid attendance percentages are available for these filters.")
    else:
        average_attendance = course_averages(attendance, "attendance_percent")
        student_summary = student_attendance_summary(attendance)
        st.markdown("**Overall attendance by student**")
        _show_plot(student_attendance_comparison(student_summary))
        st.markdown("**Average attendance by course**")
        _show_plot(course_attendance_comparison(average_attendance))
        st.caption("The dashed red line is the 75% threshold. Red bars fall below it.")
        st.markdown("**Attendance by student and course**")
        _show_plot(attendance_heatmap(attendance))
        st.caption("Red cells are below 75% for that course; teal cells meet the threshold.")
        low_records = attendance.loc[attendance["attendance_percent"] < 75]
        st.markdown("**Course attendance below 75%**")
        if low_records.empty:
            st.success("No selected course attendance records are below 75%.")
        else:
            st.dataframe(
                low_records[["registration_number", "full_name", "course_code",
                             "attended_classes", "total_classes", "attendance_percent"]]
                .rename(columns={
                    "registration_number": "Registration number", "full_name": "Student",
                    "course_code": "Course", "attended_classes": "Attended",
                    "total_classes": "Total classes", "attendance_percent": "Attendance (%)",
                }),
                hide_index=True, width="stretch",
            )

    if (attendance["total_classes"] == 0).any():
        st.caption("Records with zero total classes remain in the export and are excluded from percentage charts and averages.")

    st.divider()
    with st.expander("Filtered records and CSV export", expanded=False):
        export = export_filtered_records(data, marks, attendance)
        st.dataframe(export, hide_index=True, width="stretch")
        st.download_button(
            "Download filtered records as CSV", data=to_safe_csv(export),
            file_name="academic_records_filtered.csv", mime="text/csv",
            width="stretch",
        )
