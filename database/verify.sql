USE academic_db;

-- Row counts expected: 30, 6, 180, 180.
SELECT (SELECT COUNT(*) FROM students) AS students,
       (SELECT COUNT(*) FROM courses) AS courses,
       (SELECT COUNT(*) FROM marks) AS marks,
       (SELECT COUNT(*) FROM attendance) AS attendance;

-- Course-wise student marks, first ten rows.
SELECT c.course_code, s.registration_number, s.full_name,
       m.obtained_marks, m.total_marks,
       ROUND(100 * m.obtained_marks / m.total_marks, 1) AS marks_percent
FROM marks AS m
JOIN students AS s ON s.student_id = m.student_id
JOIN courses AS c ON c.course_id = m.course_id
ORDER BY c.course_code, s.registration_number
LIMIT 10;

-- Compare each course's average marks and attendance.
SELECT c.course_code, c.course_name, COUNT(*) AS student_count,
       ROUND(AVG(100 * m.obtained_marks / m.total_marks), 1) AS avg_marks_percent,
       ROUND(AVG(100 * a.attended_classes / a.total_classes), 1) AS avg_attendance_percent
FROM courses AS c
JOIN marks AS m ON m.course_id = c.course_id
JOIN attendance AS a ON a.student_id = m.student_id AND a.course_id = m.course_id
GROUP BY c.course_id, c.course_code, c.course_name
ORDER BY c.course_code;
