-- Drop tables if they exist, in proper dependency order
DROP TABLE IF EXISTS assessment;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS admin;

-- Admin table
CREATE TABLE admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Course table
CREATE TABLE course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL
);

-- Student table
CREATE TABLE student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- Assessment table
CREATE TABLE assessment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    weight REAL,               -- FLOAT is accepted, but REAL is preferred in SQLite
    score REAL,                -- DECIMAL(5,2) is treated as REAL in SQLite
    FOREIGN KEY (student_id) REFERENCES student(id)
    FOREIGN KEY (course_id) REFERENCES course(id)
);
