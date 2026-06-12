from io import BytesIO
from openpyxl import Workbook
from pathlib import Path
import sqlite3
DB_PATH = Path(__file__).resolve().parent.parent / "students.db"
def get_connection():
    return sqlite3.connect(DB_PATH)
SUPER_ADMIN_ID=8223004316
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
    cursor.execute(
        """SELECT telegram_id, role, department FROM admins""")
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
    conn =get_connection()
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

def update_student_department_course(
    telegram_id,
    department,
    course
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET department = ?,
            course = ?
        WHERE telegram_id = ?
    """, (
        department,
        course,
        telegram_id
    ))
    conn.commit()
    conn.close()

def update_registrations(
    telegram_id,
    full_name,
    phone,
    email,
    language,
    education_status,
    birthday
):
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
    """, (
        full_name,
        phone,
        email,
        language,
        education_status,
        birthday,
        telegram_id
    ))
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
    """, (
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    ))

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
    cursor.execute("""
    SELECT telegram_id
    FROM students
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_approved_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT telegram_id
    FROM students
    WHERE status='Approved'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_rejected_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT telegram_id
    FROM students
    WHERE status='Rejected'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_pending_telegram_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT telegram_id
    FROM students
    WHERE status='Pending'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_department(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO departments(name)
    VALUES(?)
    """, (name,))
    conn.commit()
    conn.close()

def get_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id,name
    FROM departments
    ORDER BY name
    """)
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
    cursor.execute("""
        DELETE FROM departments
        WHERE name = ?
    """, (name,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0

def get_department_name(department_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT name
    FROM departments
    WHERE id=?
    """, (department_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def add_course(department_id, course_name, max_students):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO courses(
        department_id,
        course_name,
        max_students
    )
    VALUES (?, ?, ?)
    """, (
        department_id,
        course_name,
        max_students
    ))
    conn.commit()
    conn.close()

def delete_course(course_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM courses
        WHERE course_name = ?
    """, (course_name,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0

def get_courses_by_department(department_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id,course_name,max_students
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
    cursor.execute("""
    SELECT course_name
    FROM courses
    WHERE id=?
    """, (course_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_course_students_count(course_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT COUNT(*)
    FROM students
    WHERE course=?
    """,(course_name,))
    total = cur.fetchone()[0]
    conn.close()
    return total

def get_course_limit(course_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT max_students
    FROM courses
    WHERE id=?
    """,(course_id,))
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
        SELECT
            department,
            course,
            COUNT(*)
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
        SELECT
            department,
            COUNT(*)
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
        "Full Name",
        "Gender",
        "Phone",
        "Email",
        "Education Status",
        "Language",
        "Birthday",
        "Department",
        "Course",
        "Status",
        "Registration Date"
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
        SELECT
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
        SELECT
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
        FROM students 
        WHERE  department = ?
        ORDER BY registration_date DESC
    """, (department,))
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "All Students")

def export_approved_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
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
        FROM students
        WHERE status='Approved'
        ORDER BY registration_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Approved Students")

def dep_export_approved_students( department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
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
        FROM students
        WHERE status='Approved' and  department = ?
        ORDER BY registration_date DESC
    """, ( department,))
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Approved Students")

def export_pending_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
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
        SELECT
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
        SELECT
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
        SELECT
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
        FROM students
        WHERE status='Rejected' and department = ?
        ORDER BY registration_date DESC
    """, (department,))
    rows = cursor.fetchall()
    conn.close()
    return _build_excel_workbook(rows, "Rejected Students")

init_db()