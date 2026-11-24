-- Fictional students and deterministic sample results. Re-running refreshes these seed rows.
USE academic_db;

INSERT INTO students (student_id, full_name, registration_number, semester) VALUES
  (1, 'Areeba Kamal', 'CS24-001', 5),
  (2, 'Bilal Farooq', 'CS24-002', 6),
  (3, 'Hania Siddiqui', 'CS24-003', 4),
  (4, 'Danish Raza', 'CS24-004', 7),
  (5, 'Maham Qureshi', 'CS24-005', 5),
  (6, 'Zayan Malik', 'CS24-006', 6),
  (7, 'Noor Fatima', 'CS24-007', 3),
  (8, 'Hamza Tariq', 'CS24-008', 8),
  (9, 'Iqra Nadeem', 'CS24-009', 4),
  (10, 'Saad Rehman', 'CS24-010', 7),
  (11, 'Alina Shah', 'CS24-011', 5),
  (12, 'Usman Javed', 'CS24-012', 6),
  (13, 'Mina Hassan', 'CS24-013', 3),
  (14, 'Rayyan Ahmed', 'CS24-014', 8),
  (15, 'Eman Khalid', 'CS24-015', 4),
  (16, 'Omer Saeed', 'CS24-016', 7),
  (17, 'Sara Ilyas', 'CS24-017', 5),
  (18, 'Fahad Butt', 'CS24-018', 6),
  (19, 'Nimra Yousaf', 'CS24-019', 3),
  (20, 'Ali Haider', 'CS24-020', 8),
  (21, 'Laiba Aslam', 'CS24-021', 4),
  (22, 'Kashif Mehmood', 'CS24-022', 7),
  (23, 'Zara Saleem', 'CS24-023', 5),
  (24, 'Haris Iqbal', 'CS24-024', 6),
  (25, 'Amna Naveed', 'CS24-025', 3),
  (26, 'Taha Awan', 'CS24-026', 8),
  (27, 'Sana Mirza', 'CS24-027', 4),
  (28, 'Rohan Anwar', 'CS24-028', 7),
  (29, 'Mehak Rauf', 'CS24-029', 5),
  (30, 'Ibrahim Ashraf', 'CS24-030', 6)
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name), registration_number = VALUES(registration_number), semester = VALUES(semester);

INSERT INTO courses (course_id, course_code, course_name, credit_hours) VALUES
  (1, 'CS101', 'Programming Fundamentals', 3),
  (2, 'CS203', 'Data Structures and Algorithms', 4),
  (3, 'CS305', 'Database Systems', 3),
  (4, 'CS402', 'Computer Networks', 3),
  (5, 'CY501', 'Information Security', 3),
  (6, 'CY604', 'Ethical Hacking and Penetration Testing', 4)
ON DUPLICATE KEY UPDATE course_code = VALUES(course_code), course_name = VALUES(course_name), credit_hours = VALUES(credit_hours);

-- 30 x 6 grade records. Student ability, course difficulty, and a small variation
-- produce a useful spread of scores without storing repeated student/course details.
INSERT INTO marks (student_id, course_id, obtained_marks, total_marks)
SELECT s.student_id, c.course_id,
  70 + MOD(s.student_id * 7, 19) - 9
     + MOD(s.student_id * 11 + c.course_id * 13, 23) - 11
     + CASE c.course_id WHEN 1 THEN 4 WHEN 2 THEN -5 WHEN 3 THEN 1
                        WHEN 4 THEN -2 WHEN 5 THEN -1 ELSE -4 END,
  100
FROM students AS s CROSS JOIN courses AS c
WHERE s.student_id BETWEEN 1 AND 30 AND c.course_id BETWEEN 1 AND 6
ON DUPLICATE KEY UPDATE obtained_marks = VALUES(obtained_marks), total_marks = VALUES(total_marks);

-- Each course has 28 to 32 scheduled classes. Absences range from 0 to 11.
INSERT INTO attendance (student_id, course_id, total_classes, attended_classes)
SELECT s.student_id, c.course_id,
  28 + MOD(c.course_id, 5),
  28 + MOD(c.course_id, 5) - MOD(s.student_id * 5 + c.course_id * 7, 12)
FROM students AS s CROSS JOIN courses AS c
WHERE s.student_id BETWEEN 1 AND 30 AND c.course_id BETWEEN 1 AND 6
ON DUPLICATE KEY UPDATE total_classes = VALUES(total_classes), attended_classes = VALUES(attended_classes);
