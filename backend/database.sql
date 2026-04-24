PRAGMA foreign_keys = ON;

-- =========================================================
-- 1) USERS
-- =========================================================
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT,
    role            TEXT NOT NULL
                    CHECK (role IN ('member', 'chair'))
);

-- =========================================================
-- 2) SEMESTER SCHEDULES
-- =========================================================
CREATE TABLE semester_schedules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,              -- e.g. "Fall 2026"
    locked          INTEGER NOT NULL DEFAULT 0
                    CHECK (locked IN (0, 1)),
    status          TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'review', 'approved', 'released', 'archived')),
    created_by      INTEGER,
    approved_by     INTEGER,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at     TEXT,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- =========================================================
-- 3) COURSE CATALOG (your "Class")
-- =========================================================
CREATE TABLE catalog_courses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    course_number   TEXT NOT NULL,              -- e.g. "COP 4331"
    title           TEXT NOT NULL,
    UNIQUE(course_number, title)
);

-- =========================================================
-- 4) ROOMS
-- =========================================================
CREATE TABLE rooms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number     TEXT NOT NULL UNIQUE,
    capacity        INTEGER
);

-- =========================================================
-- 5) INSTRUCTORS
-- =========================================================
CREATE TABLE instructors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE
);

-- =========================================================
-- 6) TAs
-- =========================================================
CREATE TABLE tas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE,
    max_hours       INTEGER DEFAULT 0 CHECK (max_hours >= 0)
);

-- =========================================================
-- 7) COURSE SECTIONS (your "Course")
-- =========================================================
CREATE TABLE course_sections (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id         INTEGER NOT NULL,
    catalog_course_id   INTEGER NOT NULL,
    crn                 INTEGER NOT NULL,
    level               TEXT,                   -- e.g. UG / GR
    enrollment          INTEGER NOT NULL DEFAULT 0 CHECK (enrollment >= 0),
    start_date          TEXT,                   -- store ISO date: YYYY-MM-DD
    end_date            TEXT,                   -- store ISO date: YYYY-MM-DD
    room_id             INTEGER,
    instructor_id       INTEGER,
    FOREIGN KEY (schedule_id) REFERENCES semester_schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (catalog_course_id) REFERENCES catalog_courses(id),
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
    FOREIGN KEY (instructor_id) REFERENCES instructors(id) ON DELETE SET NULL,
    UNIQUE(schedule_id, crn)
);

-- =========================================================
-- 8) SECTION MEETINGS
-- Better than storing one "time" string on Course
-- =========================================================
CREATE TABLE section_meetings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id      INTEGER NOT NULL,
    days            TEXT NOT NULL,              -- e.g. "MWF", "TR"
    start_time      TEXT NOT NULL,              -- HH:MM
    end_time        TEXT NOT NULL,              -- HH:MM
    FOREIGN KEY (section_id) REFERENCES course_sections(id) ON DELETE CASCADE
);

-- =========================================================
-- 9) SECTION <-> TA (many-to-many)
-- =========================================================
CREATE TABLE section_tas (
    section_id      INTEGER NOT NULL,
    ta_id           INTEGER NOT NULL,
    assigned_hours  INTEGER NOT NULL DEFAULT 0 CHECK (assigned_hours >= 0),
    PRIMARY KEY (section_id, ta_id),
    FOREIGN KEY (section_id) REFERENCES course_sections(id) ON DELETE CASCADE,
    FOREIGN KEY (ta_id) REFERENCES tas(id) ON DELETE CASCADE
);

-- =========================================================
-- 10) AUDIT REPORTS
-- =========================================================
CREATE TABLE audit_reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id     INTEGER NOT NULL,
    generated_by    INTEGER,
    passed          INTEGER NOT NULL DEFAULT 0
                    CHECK (passed IN (0, 1)),
    status          TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'cleared', 'approved')),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES semester_schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (generated_by) REFERENCES users(id)
);

-- =========================================================
-- 11) ISSUES
-- =========================================================
CREATE TABLE issues (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_report_id INTEGER NOT NULL,
    section_id      INTEGER,
    type            TEXT NOT NULL,              -- e.g. conflict, duplicate_crn, missing_room
    description     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'resolved')),
    detected_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at     TEXT,
    FOREIGN KEY (audit_report_id) REFERENCES audit_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES course_sections(id) ON DELETE SET NULL
);