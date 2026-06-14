import asyncio
from email import message
from io import StringIO
from aiogram.types import FSInputFile
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from config.settings import ADMIN_ID
from utils.membership_pdf import create_membership_pdf
from states.states import (
    AdminSearch,
    Announcement,
    AddDepartment,
    AddCourse,
    DeleteDepartment,
    DeleteCourse,
    EditStudent,
    AddAdmin,
    RemoveAdmin
)
from database.db import (
    admin_list,
    approve_student,
    close_registration,
    get_admin_role,
    get_course_name,
    get_department_name,
    get_department_students,
    get_student,
    is_admin,
    open_registration,
    reject_student,
    get_student_details,
    get_all_students,
    get_statistics,
    approved_students,
    rejected_students,
    get_all_telegram_ids,
    get_approved_telegram_ids,
    pending_students,
    delete_student,
    remove_admin,
    search_student,
    get_rejected_telegram_ids,
    get_pending_telegram_ids,
    get_courses,
    add_department,
    add_course,
    delete_department,
    delete_course,
    get_departments,
    get_department_statistics,
    export_all_students,
    export_approved_students,
    export_pending_students,
    export_rejected_students,
    update_student_department_course,
    add_admin,
    SUPER_ADMIN_ID
)
from keyboards.menus import (
    admin_keyboard,
    bulk_approve_rejects,
    department_keyboard,
    student_admin_keyboard,
    admin_actions_keyboard,
    approved_students_keyboard,
    rejected_students_keyboard,
    refresh_back_keyboard,
    announcements_keyboard,
    department_management_keyboard,
    departments_keyboard,
    course_management_keyboard,
    export_keyboard,
    courses_keyboard,
    admins_role,
    view_students_keyboard,
)

router = Router()
PAGE_SIZE = 5

selected_students = {}
async def notify_student(bot, telegram_id: int, text: str) -> bool:
    try:
        await bot.send_message(telegram_id, text)
        return True
    except (TelegramForbiddenError, TelegramBadRequest):
        return False

def generate_pagination_keyboard(current_page: int, total_items: int, list_type: str, action_keyboard_func=None, item_id=None) -> InlineKeyboardMarkup:
    buttons = []
    total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE

    if action_keyboard_func and item_id:
        base_kb = action_keyboard_func(item_id)
        for row in base_kb.inline_keyboard:
            buttons.append(row)

    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"page:{list_type}:{current_page - 1}"))
    if (current_page + 1) < total_pages:
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"page:{list_type}:{current_page + 1}"))
    
    if nav_row:
        buttons.append(nav_row)
        
    buttons.append([InlineKeyboardButton(text="🔙 Back to Main Panel", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "🎓 Manage Summer Camp")
async def summer_managements(message: Message):
    user_id = message.from_user.id # type: ignore
    if user_id != SUPER_ADMIN_ID:
        await message.answer("Access denied.")
    await message.answer("Super admin controls", reply_markup=admin_keyboard())


@router.message(F.text.in_(["👥 Admin Panel", "🔄 Start Over"]))
async def admin_command(message: Message):
    if message.from_user.id != ADMIN_ID: # type: ignore
        await message.answer("❌ Access denied.")
        await message.bot.send_message(ADMIN_ID, f"⚠️ Unauthorized access attempt by user {message.from_user.id}") # type: ignore
        return
    stats = get_statistics()
    await message.answer(
        f"Welcome to the Admin Panel! Please select an option:\n\n"
        f"📊 Registration Statistics\n\n"
        f"👥 Total Students: {stats[0]}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👧👦 Gender Distribution:\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f" 👦Male: {stats[10]}\n"
        f" 👧Female: {stats[11]}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🌍Language Distribution:\n\n"
        f"  🇬🇧 English: {stats[7]}\n"
        f"  🇪🇹 Afaan Oromoo: {stats[8]}\n"
        f"  🇪🇹 Amharic: {stats[9]}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎓Education Status:\n\n"
        f" 📚Students: {stats[4]}\n"
        f" 🎓Graduates: {stats[5]}\n"
        f" 📕Dropouts: {stats[6]}\n \n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 Registration Status:\n\n"
        f" ✅Approved Students: {stats[1]}\n"
        f" ❌Rejected Students: {stats[2]}\n"
        f" ⏳Pending Students: {stats[3]}\n",
        reply_markup=admin_actions_keyboard()
    )

@router.callback_query(F.data == "view_students")
@router.callback_query(F.data.startswith("page:all:"))
async def list_students(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied.", show_alert=True)
        return
    
    page = int(callback.data.split(":")[2]) if callback.data.startswith("page:all:") else 0 # type: ignore
    students = get_all_students()
    
    if not students:
        await callback.message.edit_text("📭 No students found.", reply_markup=generate_pagination_keyboard(0, 0, "all")) # type: ignore
        await callback.answer()
        return

    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    sliced_students = students[start_idx:end_idx]
    total_pages = (len(students) + PAGE_SIZE - 1) // PAGE_SIZE

    text = f"👥 Registered Students (Page {page + 1}/{total_pages}):\n\n"
    for student in sliced_students:
        text += (
            f"👤 Full Name: {student[0]}\n"
            f"📱 Phone: {student[1]}\n"
            f"🏢 Dept: {student[4]} | 📚 Course: {student[5]}\n"
            f"📌 Status: {student[6]}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )

    await callback.message.edit_text(text, reply_markup=generate_pagination_keyboard(page, len(students), "all")) # type: ignore
    await callback.answer()

@router.callback_query(F.data == "approved")
@router.callback_query(F.data.startswith("page:approved:"))
async def list_approved_students(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied.", show_alert=True)
        return
        
    page = int(callback.data.split(":")[2]) if callback.data.startswith("page:approved:") else 0 # type: ignore
    students = approved_students()
    
    if not students:
        await callback.message.edit_text("📭 No approved students.", reply_markup=generate_pagination_keyboard(0, 0, "approved")) # type: ignore
        await callback.answer()
        return

    if page >= (len(students) + PAGE_SIZE - 1) // PAGE_SIZE:
        page = max(0, page - 1)

    student = students[page]
    text = (
        f"✅ Approved Students ({page + 1}/{len(students)})\n\n"
        f"👤 Full Name: {student[0]}\n"
        f"📌 Status: {student[1]}\n"
        f"📅 Date: {student[3]}"
    )
    
    await callback.message.edit_text( # type: ignore
        text, 
        reply_markup=generate_pagination_keyboard(page, len(students), "approved", approved_students_keyboard, student[2])
    )
    await callback.answer()

@router.callback_query(F.data == "rejected")
@router.callback_query(F.data.startswith("page:rejected:"))
async def list_rejected_students(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied.", show_alert=True)
        return
        
    page = int(callback.data.split(":")[2]) if callback.data.startswith("page:rejected:") else 0 # type: ignore
    students = rejected_students()
    
    if not students:
        await callback.message.edit_text("📭 No rejected students.", reply_markup=generate_pagination_keyboard(0, 0, "rejected")) # type: ignore
        await callback.answer()
        return

    if page >= (len(students) + PAGE_SIZE - 1) // PAGE_SIZE:
        page = max(0, page - 1)

    student = students[page]
    text = (
        f"❌ Rejected Students ({page + 1}/{len(students)})\n\n"
        f"👤 Full Name: {student[0]}\n"
        f"📌 Status: {student[1]}"
    )
    
    await callback.message.edit_text( # type: ignore
        text, 
        reply_markup=generate_pagination_keyboard(page, len(students), "rejected", rejected_students_keyboard, student[2])
    )
    await callback.answer()

@router.callback_query(F.data == "pending")
@router.callback_query(F.data.startswith("page:pending:"))
async def list_pending_students(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied.", show_alert=True)
        return
        
    page = int(callback.data.split(":")[2]) if callback.data.startswith("page:pending:") else 0 # type: ignore
    students = pending_students()
    
    if not students:
        await callback.message.edit_text("📭 No pending students.", reply_markup=generate_pagination_keyboard(0, 0, "pending")) # type: ignore
        await callback.answer()
        return

    if page >= (len(students) + PAGE_SIZE - 1) // PAGE_SIZE:
        page = max(0, page - 1)

    student = students[page]
    text = (
        f"⏳ Pending Students ({page + 1}/{len(students)})\n\n"
        f"👤 Full Name: {student[0]}\n"
        f"📌 Status: {student[1]}"
    )
    
    await callback.message.edit_text( # type: ignore
        text, 
        reply_markup=generate_pagination_keyboard(page, len(students), "pending", student_admin_keyboard, student[2])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("approve:"))
async def approve_callback(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN_ID and not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    try:
        telegram_id = int(callback.data.split(":")[1]) # type: ignore
    except (ValueError, IndexError):
        await callback.answer("Invalid student ID.")
        return
    approve_student(telegram_id)
    student = get_student_details(telegram_id)
    notified = await notify_student(
        callback.bot,
        telegram_id,
        f"🎉Registration Approved! Dear {student[0]}, Your registration has been approved. Welcome to summer camp!"
    )
    await callback.message.edit_text( # type: ignore
        f"✅ Student Approved: {student[0]}\n" + ("(Notified)" if notified else "(Notification failed)"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Return to Pending", callback_data="pending")]])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("reject:"))
async def reject_callback(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN_ID and not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    try:
        telegram_id = int(callback.data.split(":")[1]) # type: ignore
    except (ValueError, IndexError):
        await callback.answer("Invalid student ID.")
        return
    reject_student(telegram_id)
    student = get_student_details(telegram_id)
    notified = await notify_student(
        callback.bot,
        telegram_id,
        f"❌Registration Rejected! Dear {student[0]}, unfortunately, your registration was not approved. Contact support for details."
    )
    await callback.message.edit_text( # type: ignore
        f"❌ Student Rejected: {student[0]}\n" + ("(Notified)" if notified else "(Notification failed)"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Return to Pending", callback_data="pending")]])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_details:"))
async def view_details_callback(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN_ID and not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return
    try:
        telegram_id = int(callback.data.split(":")[1]) # type: ignore
    except (ValueError, IndexError):
        await callback.answer("Invalid student ID.")
        return
    student = get_student_details(telegram_id)
    if not student:
        await callback.message.answer("Student not found.") # type: ignore
        await callback.answer()
        return
    
    await callback.message.answer( # type: ignore
        f"👤 Full Name: {student[0]}\n"
        f"📱 Phone: {student[1]}\n"
        f"📧 Email: {student[2]}\n"
        f"🎓 Education: {student[3]}\n"
        f"🌍 Language: {student[4]}\n"
        f"🎂 Birthday: {student[5]}\n"
        f"🏢 Department: {student[6]}\n"
        f"📚 Course: {student[7]}\n"
        f"📌 Status: {student[8]}\n"
        f"📅 Registration Date: {student[9]}\n"
    )
    await callback.answer("Details Loaded")

@router.callback_query(F.data == "refresh_stats")
async def refresh_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    stats = get_statistics()
    await callback.message.edit_text( # type: ignore
        f"📊 Registration Statistics\n\n"
        f"👥 Total Students: {stats[0]}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👧👦 Gender Distribution:\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f" 👦Male: {stats[10]}\n"
        f" 👧Female: {stats[11]}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🌍Language Distribution:\n\n"
        f"  🇬🇧 English: {stats[7]}\n"
        f"  🇪🇹 Afaan Oromoo: {stats[8]}\n"
        f"  🇪🇹 Amharic: {stats[9]}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎓Education Status:\n\n"
        f" 📚Students: {stats[4]}\n"
        f" 🎓Graduates: {stats[5]}\n"
        f" 📕Dropouts: {stats[6]}\n \n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 Registration Status:\n\n"
        f" ✅Approved Students: {stats[1]}\n"
        f" ❌Rejected Students: {stats[2]}\n"
        f" ⏳Pending Students: {stats[3]}\n",
        reply_markup=admin_actions_keyboard()
    )
    await callback.answer("Statistics updated")

@router.callback_query(F.data == "back")
async def back_to_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    await callback.message.edit_text("Admin Menu:", reply_markup=admin_actions_keyboard()) # type: ignore
    await callback.answer()

@router.callback_query(F.data == "search_student")
async def search_student_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    await callback.message.answer("Please enter the keyword to search for a student (Full Name, Phone, or Telegram ID):") # type: ignore
    await state.set_state(AdminSearch.waiting_for_keyword)
    await callback.answer()

@router.message(AdminSearch.waiting_for_keyword)
async def handle_search_query(message: Message, state: FSMContext):
    keyword = message.text.strip() # type: ignore
    students = search_student(keyword)
    if not students:
        await message.answer("No students found.")
        await state.clear()
        return
    for student in students:
        await message.answer(
            f"👤Full Name: {student[1]}\n"
            f"📱Phone Number: {student[2]}\n"
            f"📌Registration Status: {student[3]}\n"
            f"📅Registration Date: {student[4]}\n",
            reply_markup=student_admin_keyboard(student[0])
        )
    await state.clear()
@router.callback_query(F.data.startswith("delete_student:"))
async def delete_student_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    try:
        telegram_id = int(callback.data.split(":")[1]) # type: ignore
    except (ValueError, IndexError):
        await callback.answer("Invalid Telegram ID.")
        return
    delete_student(telegram_id)
    await callback.message.edit_text(f"Student with Telegram ID {telegram_id} has been deleted.", reply_markup=refresh_back_keyboard()) # type: ignore
    await callback.answer("Student deleted")

@router.callback_query(F.data.startswith("edit_student:"))
async def edit_student(callback: CallbackQuery, state: FSMContext):
    telegram_id = int(callback.data.split(":")[1])  # type: ignore
    await state.update_data(telegram_id=telegram_id)
    await callback.message.answer("🏢 Select new department:",reply_markup=departments_keyboard())  # type: ignore
    await state.set_state(EditStudent.waiting_departments)
    await callback.answer()

@router.callback_query(EditStudent.waiting_departments,F.data.startswith("department_"))
async def edit_department(callback: CallbackQuery, state: FSMContext):
    department_id = int(callback.data.split("_")[1])  # type: ignore
    department_name = get_department_name(department_id)
    await state.update_data(department_name=department_name)
    await callback.message.answer("📚 Select new course:",reply_markup=courses_keyboard(department_id))  # type: ignore
    await state.set_state(EditStudent.waiting_course)
    await callback.answer()

@router.callback_query(EditStudent.waiting_course,F.data.startswith("course_"))
async def edit_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[1])  # type: ignore
    course_name = get_course_name(course_id)
    data = await state.get_data()
    update_student_department_course(
        data["telegram_id"],
        data["department_name"],
        course_name
    )
    await notify_student(
        callback.bot,
        data["telegram_id"],
        f"""
📢 Registration Updated

Dear Student,

Your registration information has been updated by the administrator.

🏢 Department: {data['department_name']}
📚 Course: {course_name}

Please check your registration status for the latest information.

Thank you.
"""
    )
    await callback.message.answer(  # type: ignore
        f"""
✅ Student Updated Successfully

🏢 Department: {data['department_name']}
📚 Course: {course_name}

📨 Student has been notified.
"""
    )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "announcement")
async def all_announcement(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Select target audience for the announcement:", reply_markup=announcements_keyboard()) # type: ignore
    await callback.answer()

async def broadcast_message(message: Message, telegram_ids: list, prefix: str):
    success, failed = 0, 0
    for row in telegram_ids:
        try:
            await message.bot.send_message(row[0], f"{prefix}\n\n{message.text}") # type: ignore
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await message.answer(f"📢 Announcement Processed\n\n✅ Delivered: {success}\n❌ Failed: {failed}")

@router.callback_query(F.data == "all_students_announce")
async def all_students_announcement(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for all students:") # type: ignore
    await state.set_state(Announcement.all_students)
    await callback.answer()

@router.message(Announcement.all_students)
async def send_students_announcement(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: # type: ignore
        return
    await broadcast_message(message, get_all_telegram_ids(), "📢 Announcement")
    await state.clear()

@router.callback_query(F.data == "approved_students_announce")
async def approved_announcement(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for approved students:") # type: ignore
    await state.set_state(Announcement.approved_students)
    await callback.answer()

@router.message(Announcement.approved_students)
async def send_approved_announcement(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: # type: ignore
        return
    await broadcast_message(message, get_approved_telegram_ids(), "📢 ✅ Approved Students Announcement")
    await state.clear()

@router.callback_query(F.data == "rejected_students_announce")
async def rejected_announcement(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for rejected students:") # type: ignore
    await state.set_state(Announcement.rejected_students)
    await callback.answer()

@router.message(Announcement.rejected_students)
async def send_rejected_announcement(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: # type: ignore
        return
    await broadcast_message(message, get_rejected_telegram_ids(), "❌ Rejected Students Announcement")
    await state.clear()

@router.callback_query(F.data == "pending_students_announce")
async def pending_announcement(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for pending students:") # type: ignore
    await state.set_state(Announcement.pending_students)
    await callback.answer()

@router.message(Announcement.pending_students)
async def send_pending_announcement(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: # type: ignore
        return
    await broadcast_message(message, get_pending_telegram_ids(), "⏳ Pending Students Announcement")
    await state.clear()

@router.callback_query(F.data == "manage_departments")
async def manage_departments(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("🏢 Department & Course Management", reply_markup=department_management_keyboard()) # type: ignore
    await callback.answer()

@router.callback_query(F.data == "manage_courses")
async def manage_courses(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("🏢 Course Management", reply_markup=course_management_keyboard()) # type: ignore
    await callback.answer()

@router.callback_query(F.data == "add_department")
async def add_department_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏢 Send department name:") # type: ignore
    await state.set_state(AddDepartment.waiting_name)
    await callback.answer()

@router.message(AddDepartment.waiting_name)
async def save_department_handler(message: Message, state: FSMContext):
    name = message.text.strip() # type: ignore
    add_department(name)
    await message.answer(f"✅ Department '{name.title()}' added successfully.")
    await state.clear()

@router.callback_query(F.data == "delete_department")
async def delete_department_menu(callback: CallbackQuery, state: FSMContext):
    departments_list = get_departments()
    if not departments_list:
        await callback.message.answer("❌ No departments found.") # type: ignore
        await callback.answer()
        return
    text = "🏢 Departments:\n\n"
    for dep in departments_list:
        text += f"• {dep[1]}\n"
    await callback.message.answer(text + "\n\nSend department name to delete:") # type: ignore
    await state.set_state(DeleteDepartment.waiting_name)
    await callback.answer()

@router.message(DeleteDepartment.waiting_name)
async def delete_department_handler(message: Message, state: FSMContext):
    name = message.text.strip() # type: ignore
    delete_department(name)
    await message.answer(f"🗑 Department '{name}' deleted.")
    await state.clear()

@router.callback_query(F.data == "add_course")
async def add_course_start(callback: CallbackQuery):
    departments_list = get_departments()
    if not departments_list:
        await callback.message.answer("❌ No departments available.") # type: ignore
        await callback.answer()
        return
    await callback.message.answer("Select Department", reply_markup=departments_keyboard()) # type: ignore
    await callback.answer()

@router.callback_query(F.data.regexp(r"^department_\d+$"))
async def select_department(callback: CallbackQuery, state: FSMContext):
    department_id = int(callback.data.split("_")[1]) # type: ignore
    await state.update_data(department_id=department_id)
    await callback.message.answer("📚 Send course name:") # type: ignore
    await state.set_state(AddCourse.waiting_name)
    await callback.answer()

@router.message(AddCourse.waiting_name)
async def save_course_name(message: Message, state: FSMContext):
    await state.update_data(course_name=message.text)
    await message.answer("Enter max amount of students")
    await state.set_state(AddCourse.waiting_max)


@router.message(AddCourse.waiting_max)
async def save_course_max(message: Message, state: FSMContext):
    data = await state.get_data()
    max = message.text
    add_course(data["department_id"],data['course_name'], max) # type: ignore
    await message.answer(f"✅ Course '{data['course_name']}' added with maximum numbers of students {max}.")
    await state.clear()

@router.callback_query(F.data == "delete_course")
async def delete_course_start(callback: CallbackQuery, state: FSMContext):
    courses_list = get_courses()
    if not courses_list:
        await callback.message.answer("❌ No Courses available.") # type: ignore
        await callback.answer()
        return
    text = "🏢 Available Courses:\n\n"
    for dep in courses_list:
        text += f"{dep[0]} - {dep[1]}\n"
    await callback.message.answer(text + "\n\nSend Course Name to Delete:") # type: ignore
    await state.set_state(DeleteCourse.waiting_name)
    await callback.answer()

@router.message(DeleteCourse.waiting_name)
async def delete_course_handler(message: Message, state: FSMContext):
    name = message.text.strip() # type: ignore
    success = delete_course(name)
    if success:
        await message.answer(f"🗑 Course '{name}' deleted.")
    else:
        await message.answer("❌ Course not found.")
    await state.clear()

@router.callback_query(F.data=="close_registration")
async def close_reg(callback: CallbackQuery):
    close_registration()
    await callback.message.answer("🔒 Registration Closed") # type: ignore

@router.callback_query(F.data=="open_registration")
async def open_reg(callback: CallbackQuery):
    open_registration()
    await callback.message.answer("🔓 Registration Opened") # type: ignore

@router.callback_query(F.data == "show_department_stats")
async def departments_statistics(callback: CallbackQuery):
    data = get_department_statistics()
    if not data:
        await callback.message.answer("No registrations found.") # type: ignore
        await callback.answer()
        return
    text = "📊 Department Statistics\n\n"
    current_department = None
    for department, course, total in data:
        if current_department != department:
            text += f"\n🏢 {department}\n\n"
            current_department = department
        text += f"   📚 {course} — {total} students\n"
    await callback.message.answer(text) # type: ignore
    await callback.answer()

@router.callback_query(F.data == "registered_departments")
async def registered_departments(callback: CallbackQuery):
    departments_list = get_departments()
    if departments_list:
        text = "All Registered Departments \n\n"
        for idx, dep in enumerate(departments_list):
            text += f"{idx+1}. {dep[1]}\n"
        await callback.message.answer(text) # type: ignore
    else:
        await callback.message.answer("No registered Departments. Add Departments first.") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "registered_courses")
async def registered_courses(callback: CallbackQuery):
    courses_list = get_courses()
    if courses_list:
        text = "All Registered Courses \n\n"
        for idx, cour in enumerate(courses_list):
            text += f"{idx+1}. {cour[1]}\n"
        await callback.message.answer(text) # type: ignore
    else:
        await callback.message.answer("No Registered Courses. Add Courses first.") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "export_menu")
async def export_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📤 Select export type:",reply_markup=export_keyboard()) # type: ignore

@router.callback_query(F.data == "export_all")
async def export_all_handler(callback: CallbackQuery):
    excel_file = export_all_students()
    file = BufferedInputFile(excel_file, filename="all_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="👥 All Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "export_approved")
async def export_approved_handler(callback: CallbackQuery):
    excel_file = export_approved_students()
    file = BufferedInputFile(excel_file, filename="approved_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="✅ Approved Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "export_pending")
async def export_pending_handler(callback: CallbackQuery):
    excel_file = export_pending_students()
    file = BufferedInputFile(excel_file, filename="pending_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="⏳ Pending Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "export_rejected")
async def export_rejected_handler(callback: CallbackQuery):
    excel_file = export_rejected_students()
    file = BufferedInputFile(excel_file, filename="rejected_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="❌ Rejected Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "export_statistics")
async def export_statistics_handler(callback: CallbackQuery):
    stats = get_statistics()
    text = f"""
REGISTRATION STATISTICS

Total Students: {stats[0]}
Approved: {stats[1]}
Rejected: {stats[2]}
Pending: {stats[3]}

Students: {stats[4]}
Graduates: {stats[5]}
Dropouts: {stats[6]}

English: {stats[7]}
Afaan Oromoo: {stats[8]}
Amharic: {stats[9]}

Male: {stats[10]}
Female: {stats[11]}
"""
    file = BufferedInputFile(text.encode("utf-8"), filename="statistics.txt")
    await callback.message.answer_document(document=file, caption="📊 Statistics Export") # type: ignore
    await callback.answer()


@router.callback_query(F.data == "admin_management")
async def admins_managemnts(callback:CallbackQuery):
    await callback.answer()
    if not callback.message:
        return
    await callback.message.edit_text( # type: ignore
        text="👥 Admin Management Menu:\nChoose an option below:",
        reply_markup=admins_role()
    )

@router.callback_query(F.data=="add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    await callback.message.answer("📩 Send Telegram ID of the new admin:") # type: ignore
    await state.set_state(AddAdmin.telegram_id)
    await callback.answer()


@router.message(AddAdmin.telegram_id)
async def get_admin_id(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text) # type: ignore
    except ValueError:
        await message.answer("❌ Invalid Telegram ID.")
        return
    await state.update_data(telegram_id=telegram_id)
    await message.answer("🏢 Please select a department:",reply_markup=department_keyboard())
    await state.set_state(AddAdmin.department)


@router.callback_query(AddAdmin.department,F.data.startswith("departments_"))
async def save_admin_handler(callback: CallbackQuery,state: FSMContext):
    data = await state.get_data()
    department_id = int(callback.data.split("_")[1]) # type: ignore
    department_name = get_department_name(department_id)
    add_admin(data["telegram_id"],department_name)
    await callback.message.answer( # type: ignore
        f"""
✅ Department Admin Added

🆔 Telegram ID: {data['telegram_id']}
🏢 Department: {department_name}
"""
    )

    try:
        await callback.bot.send_message(data["telegram_id"], # type: ignore
            f"""
🎉 You have been added as a Department Admin

🏢 Department: {department_name}

Use /start to access your admin panel.
"""
        )
    except Exception:
        pass

    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "remove_admin")
async def remove_admin_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    await callback.message.answer("📩 Send Telegram ID to remove:")  # type: ignore
    await state.set_state(RemoveAdmin.waiting_telegram_id)
    await callback.answer()

@router.message(RemoveAdmin.waiting_telegram_id)
async def remove_admin_handler(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Please send a valid Telegram ID.")
        return

    telegram_id = int(message.text)
    remove_admin(telegram_id)
    await message.answer(
        f"✅ Admin with Telegram ID {telegram_id} removed successfully."
    )
    await state.clear()

@router.callback_query(F.data == "view_admins")
async def admins_list_handler(callback: CallbackQuery):
    await callback.answer() # Stops the loading spinner
    if callback.from_user.id != SUPER_ADMIN_ID:
        return 
    text ="All Admins with thiers Departments \n"
    admins = admin_list()
    if not admins:
        if callback.message:
            await callback.message.answer("❌ No admins added yet. ➕ Add Admin")
        return
    
    text = "👥 All Admins & Their Departments:\n\n"
    for admin in admins:
        text += f"User ID: `{admin[0]}`\n🎭 Role: {admin[1]}\n🏢 Departments: {admin[2]}\n"
        text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n" # Separator line
    if callback.message:
        await callback.message.answer(text)


@router.callback_query(F.data == "department_students")
async def departments_students(callback: CallbackQuery):
    admin = get_admin_role(callback.from_user.id)  # type: ignore
    if not admin:
        return
    role, department = admin
    students = get_department_students(department)
    if not students:
        await callback.message.answer("No students found.")  # type: ignore
        return
    await callback.message.answer(f"📋 Students under {department}\n\nTotal Students: {len(students)}")  # type: ignore
    for roll, student in enumerate(students, start=1):
        telegram_id = student[0]
        text = f"""
{department}-{roll}

👤 Full Name: {student[1]}
📚 Course: {student[2]}
📌 Status: {student[3]}
"""
        await callback.message.answer(text,  reply_markup=view_students_keyboard(telegram_id)) # type: ignore
    await callback.message.answer("📋 Bulk Actions", reply_markup= bulk_approve_rejects()) # type: ignore

@router.callback_query(F.data.startswith("select_student:"))
async def select_student(callback: CallbackQuery):
    admin_id = callback.from_user.id
    student_id = int(callback.data.split(":")[1]) # type: ignore
    if admin_id not in selected_students:
        selected_students[admin_id] = set()
    if student_id in selected_students[admin_id]:
        selected_students[admin_id].remove(student_id)
    else:
        selected_students[admin_id].add(student_id)
    total = len(selected_students[admin_id])
    await callback.answer(
        f"Selected Students: {total}"
    )

@router.callback_query(F.data == "bulk_approve")
async def bulk_approve(callback: CallbackQuery):
    admin_id = callback.from_user.id
    students = selected_students.get(admin_id, set())
    if not students:
        await callback.answer("No students selected",show_alert=True)
        return
    count = 0
    for student_id in students:
        student = get_student(student_id)
        if student[10] == "Approved":
            continue
        approve_student(student_id)
        await notify_student(
            callback.bot,
            student_id,
            """
🎉 Registration Approved

Congratulations!

Your registration has been approved.
"""
        )

        count += 1

    selected_students[admin_id] = set()
    await callback.message.answer(f"✅ {count} students approved.") # type: ignore

@router.callback_query(F.data == "bulk_reject")
async def bulk_reject(callback: CallbackQuery):
    admin_id = callback.from_user.id
    students = selected_students.get(admin_id, set())
    if not students:
        await callback.answer("No students selected",show_alert=True)
        return
    count = 0
    for student_id in students:
        student = get_student(student_id)
        if student[10] == "Rejected":
            continue
        reject_student(student_id)
        await notify_student(
            callback.bot,
            student_id,
            """
❌ Registration Rejected
Unfortunately your registration was not approved.
"""
        )
        count += 1
    selected_students[admin_id] = set()
    await callback.message.answer( # type: ignore
        f"❌ {count} students rejected."
    )

@router.callback_query(F.data == "bulk_delete")
async def bulk_delete(callback: CallbackQuery):
    admin_id = callback.from_user.id
    students = selected_students.get(admin_id, set())
    if not students:
        await callback.answer("No students selected",show_alert=True)
        return
    count = 0
    for student_id in students:
        student = get_student(student_id)
        if student[11] == "Rejected":
            continue
        delete_student(student_id)
        await notify_student(
            callback.bot,
            student_id,
            """
❌ You are no longer to use @KaayyooKoof_bot
Unfortunately your registration was not approved.
"""
        )
        count += 1
    selected_students[admin_id] = set()
    await callback.message.answer( # type: ignore
        f"❌ {count} students rejected.")
    
@router.callback_query(F.data == "clear_selection")
async def clear_selection(callback: CallbackQuery):
    admin_id = callback.from_user.id
    selected_students[admin_id] = set()
    await callback.answer("Selection cleared")


