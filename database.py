import sqlite3

DATABASE = "timetable.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Basic timetable setup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable_setup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT,
            semester TEXT,
            start_time TEXT,
            end_time TEXT,
            working_days TEXT
        )
    """)

    # Subjects and teachers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            teacher_name TEXT NOT NULL,
            lectures INTEGER NOT NULL,
            subject_type TEXT NOT NULL
        )
    """)

    # Rooms
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT NOT NULL,
            room_type TEXT NOT NULL
        )
    """)

    # Generated timetable
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            time_slot TEXT,
            subject TEXT,
            teacher TEXT,
            room TEXT,
            subject_type TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_setup(class_name, semester, start_time, end_time, working_days):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO timetable_setup
        (class_name, semester, start_time, end_time, working_days)
        VALUES (?, ?, ?, ?, ?)
    """, (
        class_name,
        semester,
        start_time,
        end_time,
        ",".join(working_days)
    ))

    conn.commit()
    conn.close()


def save_subject(subject_name, teacher_name, lectures, subject_type):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO subjects
        (subject_name, teacher_name, lectures, subject_type)
        VALUES (?, ?, ?, ?)
    """, (
        subject_name,
        teacher_name,
        lectures,
        subject_type
    ))

    conn.commit()
    conn.close()


def save_room(room_name, room_type):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO rooms
        (room_name, room_type)
        VALUES (?, ?)
    """, (
        room_name,
        room_type
    ))

    conn.commit()
    conn.close()


def clear_old_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM timetable_setup")
    cursor.execute("DELETE FROM subjects")
    cursor.execute("DELETE FROM rooms")
    cursor.execute("DELETE FROM generated_timetable")

    conn.commit()
    conn.close()


def save_generated_timetable(timetable):
    conn = get_connection()
    cursor = conn.cursor()

    for lecture in timetable:
        cursor.execute("""
            INSERT INTO generated_timetable
            (day, time_slot, subject, teacher, room, subject_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            lecture["day"],
            lecture["time"],
            lecture["subject"],
            lecture["teacher"],
            lecture["room"],
            lecture["type"]
        ))

    conn.commit()
    conn.close()


def get_generated_timetable():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM generated_timetable
        ORDER BY
            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                ELSE 7
            END,
            time_slot
    """)

    data = cursor.fetchall()
    conn.close()

    return data


# Create database tables automatically
create_tables()