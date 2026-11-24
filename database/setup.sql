-- Academic Insight, Phase 1. Safe to rerun: no tables are dropped.
CREATE DATABASE IF NOT EXISTS academic_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE academic_db;

CREATE TABLE IF NOT EXISTS students (
  student_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(120) NOT NULL,
  registration_number VARCHAR(24) NOT NULL,
  semester TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (student_id),
  UNIQUE KEY uq_students_registration (registration_number),
  CONSTRAINT chk_students_semester CHECK (semester BETWEEN 1 AND 8),
  CONSTRAINT chk_students_name CHECK (CHAR_LENGTH(TRIM(full_name)) > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS courses (
  course_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  course_code VARCHAR(16) NOT NULL,
  course_name VARCHAR(120) NOT NULL,
  credit_hours TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (course_id),
  UNIQUE KEY uq_courses_code (course_code),
  CONSTRAINT chk_courses_credit_hours CHECK (credit_hours BETWEEN 1 AND 6),
  CONSTRAINT chk_courses_name CHECK (CHAR_LENGTH(TRIM(course_name)) > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS marks (
  record_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id INT UNSIGNED NOT NULL,
  course_id INT UNSIGNED NOT NULL,
  obtained_marks DECIMAL(5,2) NOT NULL,
  total_marks DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (record_id),
  UNIQUE KEY uq_marks_student_course (student_id, course_id),
  KEY idx_marks_course_student (course_id, student_id),
  CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students (student_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_marks_course FOREIGN KEY (course_id) REFERENCES courses (course_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT chk_marks_range CHECK (total_marks > 0 AND obtained_marks >= 0 AND obtained_marks <= total_marks)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
  record_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id INT UNSIGNED NOT NULL,
  course_id INT UNSIGNED NOT NULL,
  total_classes SMALLINT UNSIGNED NOT NULL,
  attended_classes SMALLINT UNSIGNED NOT NULL,
  PRIMARY KEY (record_id),
  UNIQUE KEY uq_attendance_student_course (student_id, course_id),
  KEY idx_attendance_course_student (course_id, student_id),
  CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) REFERENCES students (student_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_attendance_course FOREIGN KEY (course_id) REFERENCES courses (course_id)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT chk_attendance_range CHECK (total_classes > 0 AND attended_classes <= total_classes)
) ENGINE=InnoDB;
