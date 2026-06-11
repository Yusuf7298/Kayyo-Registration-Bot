from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from database.db import get_courses_by_department, get_departments, get_course_registered_count

# --- Static Inline Keyboards ---

gender = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="👦 Male", callback_data="male"),
            InlineKeyboardButton(text="👧 Female", callback_data="female")
        ]
    ]
)

language = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="English")],
        [InlineKeyboardButton(text="🇪🇹 Afaan Oromoo", callback_data="Afaan Oromoo")],
        [InlineKeyboardButton(text="🇪🇹 Amharic", callback_data="Amharic")]
    ]
)

education_status = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎓 Student", callback_data="Student")],
        [InlineKeyboardButton(text="🎓 Graduate", callback_data="Graduate")],
        [InlineKeyboardButton(text="📚 Dropout", callback_data="Dropout")]
    ]
)

# --- Dynamic & Admin Inline Keyboards ---

def student_admin_keyboard(telegram_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👁 View", callback_data=f"view_details:{telegram_id}"),
                InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_student:{telegram_id}")
            ],
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{telegram_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{telegram_id}")
            ],
            [
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_student:{telegram_id}")
            ]
        ]
    )

def admin_actions_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍💼 Admin Management",callback_data="admin_management"),
                InlineKeyboardButton(text="👥 Students", callback_data="view_students")
            ],
            [
                InlineKeyboardButton(text="✅ Approved", callback_data="approved"),
                InlineKeyboardButton(text="❌ Rejected", callback_data="rejected")
            ],
            [
                InlineKeyboardButton(text="⏳ Pending", callback_data="pending")
            ],
            [
                InlineKeyboardButton(text="🏢 Departments", callback_data="manage_departments"),
                InlineKeyboardButton(text="📊 Dept Statistics", callback_data="show_department_stats")
            ],
            [
                InlineKeyboardButton(text="📚 Courses", callback_data="manage_courses")
            ],
            [
                InlineKeyboardButton(text="🔍 Search Student", callback_data="search_student")
            ],
            [   InlineKeyboardButton(text="🔒 Close Registration",callback_data="close_registration"), InlineKeyboardButton(text="🔓 Open Registration", callback_data="open_registration")
             ],
            [
                InlineKeyboardButton(text="📤 Export", callback_data="export_menu"),
                InlineKeyboardButton(text="📢 Announcement", callback_data="announcement")
            ],
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_stats"),
                InlineKeyboardButton(text="🔙 Back", callback_data="back")
            ]
        ]
    )

def approved_students_keyboard(telegram_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Reject", callback_data=f"reject:{telegram_id}")],
            [InlineKeyboardButton(text="👁 View Details", callback_data=f"view_details:{telegram_id}")],
            [InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_student:{telegram_id}")]
        ]
    )


def rejected_students_keyboard(telegram_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Approve", callback_data=f"approve:{telegram_id}")],
            [InlineKeyboardButton(text="👁 View Details", callback_data=f"view_details:{telegram_id}")],
            [InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_student:{telegram_id}")]
        ]
    )

def refresh_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_stats"),
                InlineKeyboardButton(text="🔙 Back", callback_data="back")
            ]
        ]
    )

def students_types_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏫 Grade School", callback_data="grade_school")],
            [InlineKeyboardButton(text="🏫 High School", callback_data="high_school")],
            [InlineKeyboardButton(text="🎓 College", callback_data="college")],
            [InlineKeyboardButton(text="🎓 University", callback_data="university")],
            [InlineKeyboardButton(text="📌 Other", callback_data="other")]
        ]
    )

def announcements_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 All Students", callback_data="all_students_announce"),
                InlineKeyboardButton(text="✅ Approved", callback_data="approved_students_announce")
            ],
            [
                InlineKeyboardButton(text="❌ Rejected", callback_data="rejected_students_announce"),
                InlineKeyboardButton(text="⏳ Pending", callback_data="pending_students_announce")
            ]
        ]
    )

def dep_announcements_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 All Students", callback_data="dep_all_students_announce"),
                InlineKeyboardButton(text="✅ Approved", callback_data="dep_approved_students_announce")
            ],
            [
                InlineKeyboardButton(text="❌ Rejected", callback_data="dep_rejected_students_announce"),
                InlineKeyboardButton(text="⏳ Pending", callback_data="dep_pending_students_announce")
            ]
        ]
    )


def departments_keyboard():
    keyboard = [
        [InlineKeyboardButton(text=dept_name, callback_data=f"department_{dept_id}")]
        for dept_id, dept_name in get_departments()
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def department_keyboard():
    keyboard = [
        [InlineKeyboardButton(text=dept_name, callback_data=f"departments_{dept_id}")]
        for dept_id, dept_name in get_departments()
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def courses_keyboard(department_id):
    keyboard = []
    for course_id, course_name, max_students in get_courses_by_department(department_id):
        registered = get_course_registered_count(course_name)
        remaining = max_students - registered
        if remaining <= 0:
            text = f"🔴 {course_name} (FULL)"
        else:
            text = f"🟢 {course_name} ({remaining} seats left)"
        keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"course_{course_id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def department_management_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Registered Departments", callback_data="registered_departments")],
            [InlineKeyboardButton(text="➕ Add Department", callback_data="add_department")],
            [InlineKeyboardButton(text="🗑 Delete Department", callback_data="delete_department")],
            [InlineKeyboardButton(text="📚 Manage Courses", callback_data="manage_courses")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
        ]
    )

def course_management_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Registered Courses", callback_data="registered_courses")],
            [InlineKeyboardButton(text="➕ Add Course", callback_data="add_course")],
            [InlineKeyboardButton(text="🗑 Delete Course", callback_data="delete_course")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]  # Added for unified UX navigation
        ]
    )
def departmenstAdmin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Register"),
                KeyboardButton(text="📌 Status")
            ],
            [
                KeyboardButton(text="✏️ Edit Registration"),
                KeyboardButton(text="💬 Feedback")
            ],
            [
                KeyboardButton(text="👥 Manage Students")
            ],
            [
                KeyboardButton(text="🌟 Follow us"),
                KeyboardButton(text="📋Avalibale Courses")
            ],
            [
                KeyboardButton(text="ℹ️ Help"),
                KeyboardButton(text="❌ Cancel")
            ]
        ],
        resize_keyboard=True
    )

def non_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Register"),
                KeyboardButton(text="📌 Status")
            ],
            [
                KeyboardButton(text="✏️ Edit Registration"),
                KeyboardButton(text="💬 Feedback")
            ],
            [
                KeyboardButton(text="🌟 Follow us"),
                KeyboardButton(text="📋Avalibale Courses")
            ],
            [
                KeyboardButton(text="ℹ️ Help"),
                KeyboardButton(text="❌ Cancel")
            ]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Admin Panel")],
            [KeyboardButton(text="🔄 Start Over")]
        ],
        resize_keyboard=True
    )

def admins_role():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add Admin", callback_data="add_admin"),
            InlineKeyboardButton(text="➖ Remove Admin", callback_data="remove_admin")],
            [InlineKeyboardButton(text="👥 View Admins", callback_data="view_admins")]
        ]
    )

def department_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Students", callback_data="department_students"),
                InlineKeyboardButton(text="📊 Statistics", callback_data="departments_statics"),
                InlineKeyboardButton(text="📢 Announcement", callback_data="departments_announcement")
            ],
            [
                InlineKeyboardButton(text="📤 Export", callback_data="dep_export_menu"),
            ],
            [
                InlineKeyboardButton(text="✅ Approved", callback_data="dep_approved"),
                InlineKeyboardButton(text="❌ Rejected", callback_data="dep_rejected"),
                InlineKeyboardButton(text="⏳Pending Students", callback_data="dep_pending")
            ],
        ]
    )

def export_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Export All",
                    callback_data="export_all"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Approved",
                    callback_data="export_approved"
                ),
                InlineKeyboardButton(
                    text="❌ Rejected",
                    callback_data="export_rejected"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Pending",
                    callback_data="export_pending"
                )
            ],
             [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="export_statistics"
                )
            ]
        ]
    )

def dep_export_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Export All",
                    callback_data="dep_export_all"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Approved",
                    callback_data="dep_export_approved"
                ),
                InlineKeyboardButton(
                    text="❌ Rejected",
                    callback_data="dep_export_rejected"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Pending",
                    callback_data="dep_export_pending"
                )
            ],
             [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="dep_export_statistics"
                )
            ]
        ]
    )