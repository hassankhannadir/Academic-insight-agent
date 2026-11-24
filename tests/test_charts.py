from academic_insight.analytics import (
    course_averages, prepare_dashboard_data, student_attendance_summary,
)
from academic_insight.charts import (
    attendance_heatmap, average_marks_by_course, course_attendance_comparison,
    marks_by_course, student_attendance_comparison, student_marks_comparison,
)
from tests.test_analytics import sample_snapshot


def test_marks_and_attendance_figures_have_expected_data_and_thresholds():
    data = prepare_dashboard_data(sample_snapshot())
    assert len(marks_by_course(data.marks).data) == 2
    assert len(average_marks_by_course(course_averages(data.marks, "marks_percent")).data) == 1
    assert len(student_marks_comparison(data.marks, [1, 2]).data) == 2
    student_chart = student_attendance_comparison(student_attendance_summary(data.attendance))
    course_chart = course_attendance_comparison(course_averages(data.attendance, "attendance_percent"))
    heatmap = attendance_heatmap(data.attendance)
    assert any(shape.x0 == 75 for shape in student_chart.layout.shapes)
    assert any(shape.y0 == 75 for shape in course_chart.layout.shapes)
    assert len(heatmap.data) == 1
    assert heatmap.data[0].z.shape == (2, 1)


def test_empty_figures_do_not_crash():
    data = prepare_dashboard_data({"students": [], "courses": [], "marks": [], "attendance": []})
    assert len(marks_by_course(data.marks).data) == 0
    assert len(attendance_heatmap(data.attendance).data) == 0
