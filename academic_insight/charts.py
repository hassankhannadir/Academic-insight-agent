"""Responsive Plotly figures for marks and attendance."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .analytics import ATTENDANCE_THRESHOLD


NAVY = "#243B53"
TEAL = "#147D86"
GREEN = "#278064"
RED = "#C34D4D"
AMBER = "#D89A3E"
GRID = "#E5EAF0"


def _style(figure: go.Figure, *, height: int = 420) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=24, r=24, t=42, b=32),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", color=NAVY, size=13),
        hoverlabel=dict(bgcolor="white", font_color=NAVY),
        legend=dict(orientation="h", y=-0.24),
    )
    figure.update_xaxes(gridcolor=GRID, zeroline=False)
    figure.update_yaxes(gridcolor=GRID, zeroline=False)
    return figure


def marks_by_course(marks: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    valid = marks.dropna(subset=["marks_percent"])
    if valid.empty:
        return _style(figure)
    course_codes = sorted(valid["course_code"].unique())
    for position, code in enumerate(course_codes):
        group = valid.loc[valid["course_code"] == code]
        highest = group["marks_percent"].max()
        lowest = group["marks_percent"].min()
        colors = [
            GREEN if value == highest else RED if value == lowest else TEAL
            for value in group["marks_percent"]
        ]
        jitter = [position + ((int(student_id) * 17 % 19) - 9) / 55
                  for student_id in group["student_id"]]
        custom = group[["full_name", "registration_number", "obtained_marks", "total_marks", "semester"]].astype(str).to_numpy()
        figure.add_trace(go.Scatter(
            x=jitter, y=group["marks_percent"], mode="markers",
            marker=dict(color=colors, size=10, line=dict(color="white", width=1)),
            customdata=custom,
            hovertemplate=(
                "<b>%{customdata[0]}</b> (%{customdata[1]})<br>"
                "Course: " + str(code) + "<br>Marks: %{customdata[2]}/%{customdata[3]}<br>"
                "Semester: %{customdata[4]}<br>Score: %{y:.1f}%<extra></extra>"
            ),
            showlegend=False,
        ))
    figure.update_xaxes(
        tickmode="array", tickvals=list(range(len(course_codes))), ticktext=course_codes,
        title="Course", range=[-0.5, len(course_codes) - 0.5],
    )
    figure.update_yaxes(title="Marks (%)", range=[0, 105])
    return _style(figure)


def average_marks_by_course(summary: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    valid = summary.dropna(subset=["average_percent"])
    if not valid.empty:
        figure.add_trace(go.Bar(
            x=valid["course_code"], y=valid["average_percent"],
            marker_color=TEAL,
            customdata=valid[["course_name", "record_count"]].to_numpy(),
            hovertemplate=(
                "<b>%{x}</b> — %{customdata[0]}<br>Average: %{y:.1f}%<br>"
                "Students: %{customdata[1]}<extra></extra>"
            ),
            showlegend=False,
        ))
    figure.update_xaxes(title="Course")
    figure.update_yaxes(title="Average marks (%)", range=[0, 105])
    return _style(figure)


def student_marks_comparison(marks: pd.DataFrame, student_ids: list[int]) -> go.Figure:
    figure = go.Figure()
    valid = marks.loc[marks["student_id"].isin(student_ids)].dropna(subset=["marks_percent"])
    if valid.empty:
        return _style(figure)
    course_order = (
        valid[["course_id", "course_code"]].drop_duplicates()
        .sort_values("course_id")["course_code"].tolist()
    )
    for index, (_, group) in enumerate(valid.groupby("student_id", sort=True)):
        group = group.sort_values("course_id")
        label = f"{group.iloc[0]['full_name']} ({group.iloc[0]['registration_number']})"
        custom = group[["obtained_marks", "total_marks"]].astype(str).to_numpy()
        figure.add_trace(go.Scatter(
            x=group["course_code"], y=group["marks_percent"], mode="lines+markers",
            name=label, line=dict(width=2.5, color=[NAVY, TEAL, AMBER, GREEN, RED][index % 5]),
            marker=dict(size=9), customdata=custom,
            hovertemplate=(
                f"<b>{label}</b><br>Course: %{{x}}<br>Marks: "
                "%{customdata[0]}/%{customdata[1]}<br>Score: %{y:.1f}%<extra></extra>"
            ),
        ))
    figure.update_xaxes(title="Course", categoryorder="array", categoryarray=course_order)
    figure.update_yaxes(title="Marks (%)", range=[0, 105])
    return _style(figure, height=440)


def student_attendance_comparison(summary: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    valid = summary.dropna(subset=["attendance_percent"]).sort_values("attendance_percent")
    if not valid.empty:
        labels = valid["full_name"] + " (" + valid["registration_number"] + ")"
        colors = [RED if low else TEAL for low in valid["below_75"]]
        figure.add_trace(go.Bar(
            x=valid["attendance_percent"], y=labels, orientation="h",
            marker_color=colors,
            customdata=valid[["attended_classes", "total_classes"]].to_numpy(),
            hovertemplate=(
                "<b>%{y}</b><br>Attendance: %{customdata[0]}/%{customdata[1]} classes"
                "<br>Rate: %{x:.1f}%<extra></extra>"
            ),
            showlegend=False,
        ))
    figure.add_vline(x=ATTENDANCE_THRESHOLD, line_dash="dash", line_color=RED,
                     annotation_text="75% minimum", annotation_position="top right")
    figure.update_xaxes(title="Overall attendance (%)", range=[0, 105])
    figure.update_yaxes(title="Student", autorange="reversed")
    return _style(figure, height=max(420, 28 * len(valid) + 170))


def attendance_heatmap(attendance: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    valid = attendance.dropna(subset=["attendance_percent"])
    if valid.empty:
        return _style(figure)
    valid = valid.copy()
    valid["student_label"] = valid["full_name"] + " (" + valid["registration_number"] + ")"
    valid["class_count"] = (
        valid["attended_classes"].astype(int).astype(str) + "/" +
        valid["total_classes"].astype(int).astype(str)
    )
    student_order = (
        valid[["student_id", "student_label"]].drop_duplicates()
        .sort_values("student_id")["student_label"].tolist()
    )
    course_order = (
        valid[["course_id", "course_code"]].drop_duplicates()
        .sort_values("course_id")["course_code"].tolist()
    )
    values = valid.pivot(index="student_label", columns="course_code", values="attendance_percent")
    classes = valid.pivot(index="student_label", columns="course_code", values="class_count")
    values = values.reindex(index=student_order, columns=course_order)
    classes = classes.reindex(index=student_order, columns=course_order)
    figure.add_trace(go.Heatmap(
        z=values.to_numpy(), x=course_order, y=student_order,
        text=classes.fillna("No record").to_numpy(),
        zmin=0, zmax=100,
        colorscale=[[0, RED], [0.749, RED], [0.75, TEAL], [1, TEAL]],
        colorbar=dict(title="Attendance %"),
        hovertemplate=(
            "<b>%{y}</b><br>Course: %{x}<br>Attendance: %{z:.1f}%"
            "<br>Classes: %{text}<extra></extra>"
        ),
    ))
    figure.update_xaxes(title="Course", side="top")
    figure.update_yaxes(title="Student", autorange="reversed")
    return _style(figure, height=max(450, 26 * len(student_order) + 170))


def course_attendance_comparison(summary: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    valid = summary.dropna(subset=["average_percent"])
    if not valid.empty:
        figure.add_trace(go.Bar(
            x=valid["course_code"], y=valid["average_percent"],
            marker_color=[RED if value < ATTENDANCE_THRESHOLD else TEAL
                          for value in valid["average_percent"]],
            customdata=valid[["course_name", "record_count"]].to_numpy(),
            hovertemplate=(
                "<b>%{x}</b> — %{customdata[0]}<br>Average: %{y:.1f}%<br>"
                "Records: %{customdata[1]}<extra></extra>"
            ),
            showlegend=False,
        ))
    figure.add_hline(y=ATTENDANCE_THRESHOLD, line_dash="dash", line_color=RED,
                     annotation_text="75% minimum", annotation_position="top left")
    figure.update_xaxes(title="Course")
    figure.update_yaxes(title="Average attendance (%)", range=[0, 105])
    return _style(figure)
