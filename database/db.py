from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from pathlib import Path
from dateutil.relativedelta import relativedelta
import sqlite3
DB_PATH = Path(__file__).resolve().parent.parent / "students.db"
def get_connection():
    return sqlite3.connect(DB_PATH)
SUPER_ADMIN_ID = 8223004316
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        telegram_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        gender TEXT,
        phone TEXT UNIQUE,
        email TEXT,
        education_status TEXT,
        language TEXT,
        birthday TEXT,
        department TEXT,
        course TEXT,
        status TEXT DEFAULT 'Pending',
        registration_date TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id INTEGER,
        course_name TEXT,
        max_students INTEGER DEFAULT 50,
        FOREIGN KEY (department_id)
        REFERENCES departments(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        id INTEGER PRIMARY KEY,
        registration_open INTEGER DEFAULT 1
    )
    """)
    cursor.execute("""
    INSERT OR IGNORE INTO settings(id, registration_open)
    VALUES(1,1)
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins(
        telegram_id INTEGER PRIMARY KEY,
        role TEXT DEFAULT 'department_admin',
        department TEXT)"""
    )
    cursor.execute("""
    INSERT OR IGNORE INTO admins
        (telegram_id, role, department)
        VALUES (?, ?, ?)
        """, (SUPER_ADMIN_ID, "super_admin", None))
    
    cursor.execute("""
CREATE TABLE IF NOT EXISTS memberships(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    telegram_id INTEGER UNIQUE,

    member_code TEXT UNIQUE,

    full_name TEXT NOT NULL,

    gender TEXT NOT NULL,

    phone TEXT UNIQUE NOT NULL,

    email TEXT,

    occupation TEXT,

    address TEXT,

    membership_type TEXT,

    duration_months INTEGER,

    registration_date TEXT,

    expiry_date TEXT,

    status TEXT DEFAULT 'Pending',

    photo_file_id TEXT,
    deleted INTEGER DEFAULT 0
)
""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membership_durations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        duration_name TEXT UNIQUE,
        months INTEGER,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membership_types(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT UNIQUE,
        expiry_date TEXT DEFAULT 'Active',
        active INTEGER DEFAULT 1
    )
    """)

    types = [
        ("Basic",),
        ("Premium",),
        ("VIP",)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO membership_types(type_name)
        VALUES(?)
    """, types)

    durations = [
        ("3 Months", 3),
        ("6 Months", 6),
        ("12 Months", 12)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO membership_durations(
            duration_name,
            months
        )
        VALUES(?,?)
    """, durations)
    conn.commit()
    conn.close()

def close_registration():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE settings
    SET registration_open=0
    WHERE id=1
    """)
    conn.commit()
    conn.close()

def open_registration():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    UPDATE settings
    SET registration_open=1
    WHERE id=1
    """)
    conn.commit()
    conn.close()

def registration_status():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT registration_open
    FROM settings
    WHERE id=1
    """)
    status = cur.fetchone()[0]
    conn.close()
    return status

def add_admin(telegram_id, department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO admins
    (telegram_id, role, department)
    VALUES (?, ?, ?)
    """, (
        telegram_id,
        "department_admin",
        department
    ))
    conn.commit()
    conn.close()

def remove_admin(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM admins WHERE telegram_id=?",
        (telegram_id,)
    )
    conn.commit()
    conn.close()

def admin_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT telegram_id, role, department FROM admins""")
    addmins = cursor.fetchall()
    conn.close()
    return addmins

def get_admin(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT role, department
    FROM admins
    WHERE telegram_id=?
    """, (telegram_id,))
    admin = cursor.fetchone()
    conn.close()
    return admin

def is_super_admin(user_id):
    return user_id == SUPER_ADMIN_ID

def is_admin(telegram_id):
    return get_admin(telegram_id) is not None

def get_admin_role(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT role, department
    FROM admins
    WHERE telegram_id=?
    """, (telegram_id,))
    admin = cursor.fetchone()
    conn.close()
    return admin

def departments_approved_or_rejects(status, departments):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT telegram_id, full_name, status, registration_date 
        FROM students
        WHERE status=? and department=?
        """,
        (status, departments))
    student = cursor.fetchall()
    conn.close()
    return student

def get_department_students_by_status(status, department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT telegram_id
        FROM students
        WHERE status = ? AND department = ?
        """,
        (status, department)
    )
    students = cursor.fetchall()
    conn.close()
    return students

def get_departments_statistics(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM students WHERE department=?",
        (department,)
    )
    total_students = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM students WHERE department=? AND status='Approved'",
        (department,)
    )
    approved = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM students WHERE department=? AND status='Rejected'",
        (department,)
    )
    rejected = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM students WHERE department=? AND status='Pending'",
        (department,)
    )
    pending = cursor.fetchone()[0]
    cursor.execute("""
        SELECT course, COUNT(*)
        FROM students
        WHERE department=?
        GROUP BY course
    """, (department,))
    courses = cursor.fetchall()
    conn.close()
    return {
        "total": total_students,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "courses": courses
    }

def get_pending_students_by_department(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT telegram_id, full_name, course
        FROM students
        WHERE department=? AND status='Pending'
    """, (department,))
    data = cursor.fetchall()
    conn.close()
    return data

def get_department_students(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT telegram_id,
           full_name,
           course,
           status
    FROM students
    WHERE department=?
    ORDER BY full_name
    """, (department,))
    data = cursor.fetchall()
    conn.close()
    return data

def get_all_admins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT telegram_id, role, department
    FROM admins
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def save_student(
    telegram_id,
    full_name,
    gender,
    phone,
    email,
    education_status,
    language,
    birthday,
    department,
    course,
    status="Pending",
    registration_date=None
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO students(
        telegram_id,
        full_name,
        gender,
        phone,
        email,
        education_status,
        language,
        birthday,
        department,
        course,
        status,
        registration_date
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        telegram_id,
        full_name,
        gender,
        phone,
        email,
        education_status,
        language,
        birthday,
        department,
        course,
        status,
        registration_date
    ))
    conn.commit()
    conn.close()

def get_student(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT *
    FROM students
    WHERE telegram_id = ?
    """, (telegram_id,))
    student = cursor.fetchone()
    conn.close()
    return student

def get_student_by_departments(departments):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT telegram_id
    FROM students
    WHERE department = ?
    """, (departments,))
    student = cursor.fetchall()
    conn.close()
    return student

def get_student_by_phone(phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT *
    FROM students
    WHERE phone = ?
    """, (phone,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_student_status(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        full_name,
        status,
        registration_date
    FROM students
    WHERE telegram_id = ?
    """, (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        full_name,
        phone,
        email,
        education_status,
        department,
        course,
        status,
        registration_date
    FROM students
    ORDER BY registration_date DESC
    """)
    students = cursor.fetchall()
    conn.close()
    return students

def get_student_details(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        full_name,
        phone,
        email,
        education_status,
        language,
        birthday,
        department,
        course,
        status,
        registration_date
    FROM students
    WHERE telegram_id = ?
    """, (telegram_id,))
    student = cursor.fetchone()
    conn.close()
    return student

def update_student_department_course(telegram_id, department, course):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET department = ?,
            course = ?
        WHERE telegram_id = ?
    """, (department, course, telegram_id))
    conn.commit()
    conn.close()

def update_registrations(telegram_id, full_name, phone, email, language, education_status, birthday):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET
            full_name = ?,
            phone = ?,
            email = ?,
            language = ?,
            education_status = ?,
            birthday = ?
        WHERE telegram_id = ?
    """, (full_name, phone, email, language, education_status, birthday, telegram_id))
    conn.commit()
    conn.close()

def approve_student(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE students
    SET status='Approved'
    WHERE telegram_id=?
    """, (telegram_id,))
    conn.commit()
    conn.close()

def reject_student(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE students
    SET status='Rejected'
    WHERE telegram_id=?
    """, (telegram_id,))
    conn.commit()
    conn.close()

def delete_student(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    DELETE FROM students
    WHERE telegram_id=?
    """, (telegram_id,))
    conn.commit()
    conn.close()

def approved_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT full_name,status,telegram_id,registration_date
    FROM students
    WHERE status='Approved'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def rejected_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT full_name,status,telegram_id,registration_date
    FROM students
    WHERE status='Rejected'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def pending_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT full_name,status,telegram_id,registration_date
    FROM students
    WHERE status='Pending'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def search_student(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        telegram_id,
        full_name,
        phone,
        status,
        registration_date
    FROM students
    WHERE
        full_name LIKE ?
        OR phone LIKE ?
        OR CAST(telegram_id AS TEXT) LIKE ?
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    conn.close()
    return results

def get_statistics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        COUNT(*),
        SUM(CASE WHEN status='Approved' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END),
        SUM(CASE WHEN education_status='Student' THEN 1 ELSE 0 END),
        SUM(CASE WHEN education_status='Graduate' THEN 1 ELSE 0 END),
        SUM(CASE WHEN education_status='Dropout' THEN 1 ELSE 0 END),
        SUM(CASE WHEN language='English' THEN 1 ELSE 0 END),
        SUM(CASE WHEN language='Afaan Oromoo' THEN 1 ELSE 0 END),
        SUM(CASE WHEN language='Amharic' THEN 1 ELSE 0 END),
        SUM(CASE WHEN gender='male' THEN 1 ELSE 0 END),
        SUM(CASE WHEN gender='female' THEN 1 ELSE 0 END)
    FROM students
    """)
    stats = cursor.fetchone()
    conn.close()
    return stats

def dep_get_statistics(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        COUNT(*),
        SUM(CASE WHEN status='Approved' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END),
        SUM(CASE WHEN education_status='Student' THEN 1 ELSE 0 END),
        SUM(CASE WHEN education_status='Graduate' THEN 1 ELSE 0 END),
        SUM(CASE WHEN education_status='Dropout' THEN 1 ELSE 0 END),
        SUM(CASE WHEN language='English' THEN 1 ELSE 0 END),
        SUM(CASE WHEN language='Afaan Oromoo' THEN 1 ELSE 0 END),
        SUM(CASE WHEN language='Amharic' THEN 1 ELSE 0 END),
        SUM(CASE WHEN gender='male' THEN 1 ELSE 0 END),
        SUM(CASE WHEN gender='female' THEN 1 ELSE 0 END)
    FROM students
    WHERE department = ?
    """, (department,))
    stats = cursor.fetchone()
    conn.close()
    return stats

def get_all_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM students")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_approved_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM students WHERE status='Approved'")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_rejected_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM students WHERE status='Rejected'")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_pending_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM students WHERE status='Pending'")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_department(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO departments(name) VALUES(?)", (name,))
    conn.commit()
    conn.close()

def get_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM departments ORDER BY name")
    departments = cursor.fetchall()
    conn.close()
    return departments

def get_courses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            department_id,
            course_name,
            max_students,
            COUNT(s.telegram_id) as registered
        FROM courses c
        LEFT JOIN students s
        ON course_name = s.course
        GROUP BY c.id
    """)
    data = cursor.fetchall()
    conn.close()
    return data

def delete_department(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM departments WHERE name = ?", (name,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0

def get_department_name(department_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM departments WHERE id=?", (department_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def add_course(department_id, course_name, max_students):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO courses(department_id, course_name, max_students)
    VALUES (?, ?, ?)
    """, (department_id, course_name, max_students))
    conn.commit()
    conn.close()

def delete_course(course_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE course_name = ?", (course_name,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0

def get_courses_by_department(department_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, course_name, max_students
    FROM courses
    WHERE department_id=?
    ORDER BY course_name
    """, (department_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_course_name(course_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_name FROM courses WHERE id=?", (course_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_course_students_count(course_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students WHERE course=?", (course_name,))
    total = cur.fetchone()[0]
    conn.close()
    return total

def get_course_limit(course_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT max_students FROM courses WHERE id=?", (course_id,))
    limit = cur.fetchone()[0]
    conn.close()
    return limit

def course_is_full(course_id):
    course_name = get_course_name(course_id)
    total = get_course_students_count(course_name)
    limit = get_course_limit(course_id)
    return total >= limit

def get_department_statistics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT department, course, COUNT(*)
        FROM students
        GROUP BY department, course
        ORDER BY department, course
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_course_registered_count(course_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM students s
        JOIN courses c ON s.course = course_name
        WHERE course_name = ?
    """, (course_name,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_department_totals():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT department, COUNT(*)
        FROM students
        GROUP BY department
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def _build_excel_workbook(rows, sheet_title="Students"):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title # type: ignore
    ws.append([ # type: ignore
        "Full Name", "Gender", "Phone", "Email", "Education Status",
        "Language", "Birthday", "Department", "Course", "Status", "Registration Date"
    ])
    for row in rows:
        ws.append(row) # type: ignore
    output = BytesIO()
    wb.save(output)
    return output.getvalue()

def export_all_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students
        ORDER BY registration_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "All Students")

def dep_export_all_students(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students 
        WHERE department = ?
        ORDER BY registration_date DESC
    """, (department,))
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "All Students")

def export_approved_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students
        WHERE status='Approved'
        ORDER BY registration_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Approved Students")

def dep_export_approved_students(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students
        WHERE status='Approved' and department = ?
        ORDER BY registration_date DESC
    """, (department,))
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Approved Students")

def export_pending_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students
        WHERE status='Pending'
        ORDER BY registration_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Pending Students")

def dep_export_pending_students(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students
        WHERE status='Pending' and department = ?
        ORDER BY registration_date DESC
    """, (department,))
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Pending Students")

def export_rejected_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students
        WHERE status='Rejected'
        ORDER BY registration_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Rejected Students")

def dep_export_rejected_students(department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, gender, phone, email, education_status, language, birthday, department, course, status, registration_date
        FROM students
        WHERE status='Rejected' and department = ?
        ORDER BY registration_date DESC
    """, (department,))
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Rejected Students")

def generate_member_id(member_id):
    return f"MEMBER-{str(member_id).zfill(5)}"


def save_membership(
    telegram_id,
    full_name,
    gender,
    phone,
    email,
    occupation,
    address,
    membership_type,
    duration_months,
    registration_date,
    photo_file_id=None
):

    conn = get_connection()
    cur = conn.cursor()

    start = datetime.strptime(
        registration_date,
        "%Y-%m-%d"
    )

    expiry = (
        start +
        relativedelta(
            months=duration_months
        )
    ).strftime("%Y-%m-%d")

    try:

        cur.execute(
"""
INSERT INTO memberships(
    telegram_id,
    member_code,
    full_name,
    gender,
    phone,
    email,
    occupation,
    address,
    membership_type,
    duration_months,
    registration_date,
    expiry_date,
    photo_file_id
)
VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
""",
(
    telegram_id,
    None,
    full_name,
    gender,
    phone,
    email,
    occupation,
    address,
    membership_type,
    duration_months,
    registration_date,
    expiry,
    photo_file_id
)
)

        # Get inserted row id
        member_id = cur.lastrowid

        # Generate Member Code
        member_code = generate_member_id(
            member_id
        )

        cur.execute(
"""
UPDATE memberships
SET member_code=?
WHERE id=?
""",
(
    member_code,
    member_id
)
)

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    finally:

        conn.close()

def get_membership(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memberships WHERE telegram_id=?", (telegram_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def get_membership_status(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM memberships WHERE telegram_id=?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Pending"

def approve_membership(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE memberships SET status='Approved' WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()

def reject_membership(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE memberships SET status='Rejected' WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()

def delete_membership(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE memberships SET deleted=1 WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()

def membership_deleted(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT deleted FROM memberships WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return 0

def get_membership_types():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type_name FROM membership_types WHERE active=1")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_membership_durations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, duration_name, months FROM membership_durations WHERE active=1")
    rows = cursor.fetchall()
    conn.close()
    return rows
def get_membership_by_phone(phone):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM memberships
        WHERE phone=?
        AND deleted=0
    """, (phone,))
    data = cur.fetchone()
    conn.close()
    return data

def get_duration_months(duration_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT months FROM membership_durations WHERE id=?", (duration_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0]

def get_membership_statistics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT membership_type, duration_months, COUNT(*)
    FROM memberships
    GROUP BY membership_type, duration_months
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_members():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memberships WHERE deleted=0 ORDER BY registration_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_pending_members():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM memberships WHERE status='Pending'")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_approved_members():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM memberships WHERE status='Approved'")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_rejected_members():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM memberships WHERE status='Rejected'")
    rows = cur.fetchall()
    conn.close()
    return rows

def update_expired_memberships():
    conn = get_connection()
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("UPDATE memberships SET membership_status='Expired' WHERE expiry_date < ?", (today,))
    conn.commit()
    conn.close()

def renew_membership(telegram_id, months):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT expiry_date FROM memberships WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    if not row:
        return False
    expiry = datetime.strptime(row[0], "%Y-%m-%d")
    new_expiry = (expiry + relativedelta(months=months)).strftime("%Y-%m-%d")
    cur.execute("""
    UPDATE memberships
    SET expiry_date=?, membership_status='Active'
    WHERE telegram_id=?
    """, (new_expiry, telegram_id))
    conn.commit()
    conn.close()
    return True

def verify_membership(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT full_name, membership_type, expiry_date, membership_status
    FROM memberships
    WHERE telegram_id=? AND deleted=0
    """, (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_membershipstatistics():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN status='Approved' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='Rejected' THEN 1 ELSE 0 END),
        SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END),
        SUM(CASE WHEN membership_type='Basic' THEN 1 ELSE 0 END),
        SUM(CASE WHEN membership_type='Premium' THEN 1 ELSE 0 END),
        SUM(CASE WHEN membership_type='VIP' THEN 1 ELSE 0 END),
        SUM(CASE WHEN duration_months=3 THEN 1 ELSE 0 END),
        SUM(CASE WHEN duration_months=6 THEN 1 ELSE 0 END),
        SUM(CASE WHEN duration_months=12 THEN 1 ELSE 0 END),
        SUM(CASE WHEN gender='male' THEN 1 ELSE 0 END),
        SUM(CASE WHEN gender='female' THEN 1 ELSE 0 END)
    FROM memberships
    """)
    stats = cursor.fetchone()
    conn.close()
    return stats

from io import BytesIO
from openpyxl import Workbook


def export_members_excel(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Memberships" # type: ignore
    headers = [
        "Telegram ID",
        "Full Name",
        "Gender",
        "Phone",
        "Email",
        "Occupation",
        "Address",
        "Membership",
        "Duration",
        "Registration Date",
        "Expiry Date",
        "Status"
    ]
    ws.append(headers) # type: ignore
    for row in rows:
        ws.append([ # type: ignore
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
            row[9],
            row[10],
            row[12],
            row[11]
        ])
    file = BytesIO()
    wb.save(file)
    file.seek(0)
    return file

from io import BytesIO
from reportlab.pdfgen import canvas


def generate_membership_card(member):

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Membership Card")

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(150, 780, "MEMBERSHIP CARD")

    pdf.line(60, 760, 520, 760)

    pdf.setFont("Helvetica", 12)

    pdf.drawString(70, 700, f"Name: {member[2]}")
    pdf.drawString(70, 670, f"Gender: {member[3]}")
    pdf.drawString(70, 640, f"Phone: {member[4]}")
    pdf.drawString(70, 610, f"Email: {member[5]}")

    pdf.drawString(70, 560, f"Membership: {member[8]}")
    pdf.drawString(70, 530, f"Duration: {member[9]} Months")

    pdf.drawString(70, 500, f"Registered: {member[10]}")
    pdf.drawString(70, 470, f"Expiry: {member[12]}")

    pdf.drawString(70, 420, f"Status: {member[11]}")

    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(
        70,
        360,
        "Present this card when required."
    )

    pdf.save()

    buffer.seek(0)

    return buffer

import qrcode
from io import BytesIO


def generate_qr(member):
    data = f"""
ID:{member[2]}
NAME:{member[3]}
TYPE:{member[9]}
"""
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(
        buf,
        format="PNG"  # type: ignore
        )
    buf.seek(0)

init_db()