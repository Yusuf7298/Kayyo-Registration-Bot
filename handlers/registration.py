import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, FSInputFile, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from states.states import Announcement, EditRegistration, Registration, Feedback 
from database.db import (
    course_is_full,
    dep_export_all_students,
    dep_export_approved_students,
    dep_export_pending_students,
    dep_export_rejected_students,
    dep_get_statistics,
    departments_approved_or_rejects,
    export_all_students,
    export_approved_students,
    export_pending_students,
    export_rejected_students,
    get_admin_role,
    get_all_telegram_ids,
    get_approved_telegram_ids,
    get_courses_by_department,
    get_department_students_by_status,
    get_departments_statistics,
    get_pending_telegram_ids,
    get_rejected_telegram_ids,
    get_statistics,
    get_student_by_departments,
    is_admin,
    registration_status,
    save_student,
    get_student,
    get_student_status,
    get_student_by_phone,
    get_department_name,
    get_course_name,
    get_courses,
    update_registrations
)
from keyboards.menus import (
    announcements_keyboard,
    approved_students_keyboard,
    courses_keyboard,
    dep_announcements_keyboard,
    dep_export_keyboard,
    department_admin_keyboard,
    gender,
    language,
    education_status, 
    admin_keyboard,
    departments_keyboard,
    non_admin_keyboard,
    rejected_students_keyboard
)
from config.settings import ADMIN_ID
from utils.pdf_generator import create_admission_pdf

router = Router()
COURSES_PAGE_SIZE = 5

async def notify_student(bot, telegram_id: int, text: str) -> bool:
    try:
        await bot.send_message(telegram_id, text)
        return True
    except (TelegramForbiddenError, TelegramBadRequest):
        return False

def generate_courses_keyboard(current_page: int, total_items: int) -> InlineKeyboardMarkup:
    buttons = []
    total_pages = (total_items + COURSES_PAGE_SIZE - 1) // COURSES_PAGE_SIZE
    
    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"course_page:{current_page - 1}"))
    if (current_page + 1) < total_pages:
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"course_page:{current_page + 1}"))
        
    if nav_row:
        buttons.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "📝 Register")
async def register_command(message: Message, state: FSMContext):
    student = get_student(message.from_user.id) # type: ignore
    if student:
        await message.answer("✅ You have already registered.\n\nUse 📌 Status to check your registration status.")
        return
    if registration_status() == 0:
        await message.answer(
        """
🚫 Registration Closed

The registration period has ended.

Please contact the administrator.
"""
    )
        return
    await message.answer("Please enter your full name:")
    await state.set_state(Registration.full_name)

@router.message(Registration.full_name)
async def get_fullname(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip()) # type: ignore
    await state.set_state(Registration.gender)
    await message.answer("Please select your gender:", reply_markup=gender)

@router.callback_query(Registration.gender)
async def get_gender(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(gender=callback.data)
    await state.set_state(Registration.phone)
    await callback.message.answer("Please enter your phone number:") # type: ignore

@router.message(Registration.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip() # type: ignore
    existing = get_student_by_phone(phone)
    if existing:
        await message.answer("❌ This phone number is already registered.")
        return
    if not (phone.isdigit() or (phone.startswith("+") and phone[1:].isdigit())):
        await message.answer("Please enter a valid phone number.\nExample: +251912345678")
        return

    await state.update_data(phone=phone)
    await state.set_state(Registration.email)
    await message.answer("Please enter your email address:")

@router.message(Registration.email)
async def get_email(message: Message, state: FSMContext):
    email = message.text.strip() # type: ignore
    if "@" not in email or "." not in email:
        await message.answer("Please enter a valid email address.")
        return

    await state.update_data(email=email)
    await state.set_state(Registration.education_status)
    await message.answer("Please select your education status:", reply_markup=education_status)

@router.callback_query(Registration.education_status)
async def get_education(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(education_status=callback.data)
    await state.set_state(Registration.language)
    await callback.message.answer("Please select your preferred language:", reply_markup=language) # type: ignore

@router.callback_query(Registration.language)
async def get_language(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(language=callback.data)
    await state.set_state(Registration.birthday)
    await callback.message.answer("Please enter your birthday in YYYY-MM-DD format:") # type: ignore

@router.message(Registration.birthday)
async def get_birthday(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text.strip(), "%Y-%m-%d") # type: ignore
    except ValueError:
        await message.answer("Invalid date format.\nUse YYYY-MM-DD")
        return

    await state.update_data(birthday=message.text.strip()) # type: ignore
    await state.set_state(Registration.department)
    await message.answer("🏢 Please select a department:", reply_markup=departments_keyboard())

@router.callback_query(Registration.department, F.data.startswith("department_"))
async def select_department(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    department_id = int(callback.data.split("_")[1]) # type: ignore
    department_name = get_department_name(department_id)
    
    if not get_courses_by_department(department_id):
        await callback.message.edit_text("⚠️ There are no courses registered under this department. Please select another department or contact admin.") # type: ignore
        await callback.message.answer("🏢 Please select a department:", reply_markup=departments_keyboard()) # type: ignore
        return

    await state.update_data(department_id=department_id, department=department_name)
    await state.set_state(Registration.course)
    await callback.message.edit_text("📚 Available Courses:", reply_markup=courses_keyboard(department_id)) # type: ignore

@router.callback_query(Registration.course, F.data.startswith("course_"))
async def select_course(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    course_id = int(callback.data.split("_")[1]) # type: ignore
    if course_is_full(course_id):
        await callback.message.answer(f"🚫 Course Full This {get_course_name(course_id)} has reached its maximum capacity.Please choose another course.", reply_markup=departments_keyboard()) # type: ignore
        return
    course_name = get_course_name(course_id)
    await state.update_data(course_id=course_id, course=course_name)
    
    data = await state.get_data()
    registration_date = datetime.now().strftime("%Y-%m-%d")
    user_id = callback.from_user.id
    save_student(
        user_id,
        data["full_name"],
        data["gender"],
        data["phone"],
        data["email"],
        data["education_status"],
        data["language"],
        data["birthday"],
        data["department"],
        data["course"],
        registration_date=registration_date
    )
    
    await callback.message.edit_text( # type: ignore
        f"✅ Registration Completed Successfully\n\n"
        f"👤 Full Name: {data['full_name']}\n"
        f"🚻 Gender: {data['gender']}\n"
        f"📱 Phone: {data['phone']}\n"
        f"📧 Email: {data['email']}\n"
        f"🎓 Education: {data['education_status']}\n"
        f"🌍 Language: {data['language']}\n"
        f"🎂 Birthday: {data['birthday']}\n\n"
        f"🏢 Department: {data['department']}\n"
        f"📚 Course: {data['course']}\n\n"
        f"📅 Registration Date: {registration_date}\n\n"
        f"⏳ Waiting for approval."
    )
    
    await notify_student(
        callback.bot,
        ADMIN_ID,
        f"🆕 NEW REGISTRATION\n\n"
        f"👤 Name: {data['full_name']}\n"
        f"📱 Phone: {data['phone']}\n"
        f"📧 Email: {data['email']}\n\n"
        f"🏢 Department: {data['department']}\n"
        f"📚 Course: {data['course']}\n\n"
        f"🆔 Telegram ID: {user_id}\n\n"
        f"⏳ Waiting for approval."
    )
    await state.clear()

@router.message(F.text == "📌 Status")
async def status_command(message: Message):
    student = get_student(message.from_user.id) # type: ignore
    if not student:
        await message.answer("❌ You are not registered.")
        return
        
    status_info = get_student_status(message.from_user.id) # type: ignore
    current_status = status_info[1] if status_info else "Pending"
    
    if current_status == "Approved":
        extra_message = "\n✅ Your registration has been approved."
    elif current_status == "Rejected":
        extra_message = "\n❌ Your registration has been rejected."
    else:
        extra_message = "\n⏳ Your registration is still under review."
        
    await message.answer(
        f"📋 Registration Information\n\n"
        f"👤 Name: {status_info[0]}\n"
        f"🏢 Department: {student[8]}\n"
        f"📚 Course: {student[9]}\n"
        f"📌 Status: {current_status}\n"
        f"📅 Registration Date: {status_info[2]}\n"
        f"{extra_message}"
    )

@router.message(F.text == "✏️ Edit Registration")
async def edit_registration(message: Message, state: FSMContext):
    student = get_student(message.from_user.id)  # type: ignore
    if not student:
        await message.answer("❌ You are not registered.")
        return
    status = student[11]
    if status != "Pending":
        await message.answer(
            "❌ Only registrations with Pending status can be edited."
        )
        return
    await message.answer("👤 Enter your full name:")
    await state.set_state(EditRegistration.full_name)

@router.message(EditRegistration.full_name)
async def edit_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("📱 Enter your phone number:")
    await state.set_state(EditRegistration.phone)

@router.message(EditRegistration.phone)
async def edit_phone(message: Message, state: FSMContext):
    phone = message.text.strip() # type: ignore
    if not (phone.isdigit() or (phone.startswith("+") and phone[1:].isdigit())):
        await message.answer("❌ Invalid phone number.")
        return
    await state.update_data(phone=phone)
    await message.answer("📧 Enter your email:")
    await state.set_state(EditRegistration.email)

@router.message(EditRegistration.email)
async def edit_email(message: Message, state: FSMContext):
    email = message.text.strip() # type: ignore
    if "@" not in email or "." not in email:
        await message.answer("❌ Invalid email address.")
        return
    await state.update_data(email=email)
    await message.answer("🌍 Select your language:",reply_markup=language)
    await state.set_state(EditRegistration.language)

@router.callback_query(EditRegistration.language)
async def edit_language(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(language=callback.data)
    await callback.message.answer("🎓 Select your education status:", reply_markup=education_status) # type: ignore
    await state.set_state(EditRegistration.education)

@router.callback_query(EditRegistration.education)
async def edit_education(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(education=callback.data)
    await callback.message.answer("🎂 Enter your birthday (YYYY-MM-DD):") # type: ignore
    await state.set_state(EditRegistration.birthday)

@router.message(EditRegistration.birthday)
async def edit_birthday(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text.strip(), "%Y-%m-%d") # type: ignore
    except ValueError:
        await message.answer(
            "❌ Invalid date format.\nUse YYYY-MM-DD"
        )
        return
    data = await state.get_data()
    update_registrations(
        message.from_user.id,  # type: ignore
        data["full_name"],
        data["phone"],
        data["email"],
        data["language"],
        data["education"],
        message.text.strip() # type: ignore
    )
    await message.answer(
        """
✅ Registration Updated Successfully

👤 Full Name Updated
📱 Phone Updated
📧 Email Updated
🌍 Language Updated
🎓 Education Updated
🎂 Birthday Updated
"""
    )
    await state.clear()

@router.message(F.text == "ℹ️ Help")
async def help_command(message: Message):
    await message.answer(
        f"📚 Available Options\n\n"
        f"📝 Register\nRegister for the Summer Camp.\n\n"
        f"📌 Status\nCheck your registration status.\n\n"
        f"❌ Cancel\nCancel the current registration process.\n\n"
        f"If you need assistance, contact the administrator."
    )

@router.message(F.text == "❌ Cancel")
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Registration cancelled.", reply_markup=non_admin_keyboard())

@router.message(F.text == "📋Avalibale Courses")
@router.callback_query(F.data.startswith("course_page:"))
async def avaliable_course(event: Message | CallbackQuery, state: FSMContext):
    is_callback = isinstance(event, CallbackQuery)
    message = event.message if is_callback else event
    if is_callback:
        await event.answer()
        page = int(event.data.split(":")[1]) # type: ignore
    else:
        page = 0
    courses_list = get_courses()
    if not courses_list:
        if is_callback:
            await message.edit_text("No Available Courses for Registrations now wait our updates on our social media group or channels.") # type: ignore
        else:
            await message.answer("No Available Courses for Registrations.") # type: ignore
        return

    start_idx = page * COURSES_PAGE_SIZE
    end_idx = start_idx + COURSES_PAGE_SIZE
    sliced_courses = courses_list[start_idx:end_idx]
    total_pages = (len(courses_list) + COURSES_PAGE_SIZE - 1) // COURSES_PAGE_SIZE

    text = f"All Available Courses for Registrations (Page {page + 1}/{total_pages})\n\n"
    for idx, cour in enumerate(sliced_courses, start=start_idx + 1):
        remaining = cour[2] - cour[3]
        text += (
        f"{idx}. {cour[1]}\n"
        f"   👥 Registered: {cour[3]}/{cour[2]}\n"
        f"   🪑 Remaining: {remaining}\n\n"
    )
    kb = generate_courses_keyboard(page, len(courses_list))
    if is_callback:
        await message.edit_text(text, reply_markup=kb) # type: ignore
    else:
        await message.answer(text, reply_markup=kb) # type: ignore

@router.message(F.text == "💬 Feedback")
async def feedback_messages(message: Message, state: FSMContext):
    await message.answer("💬 Please send your feedback or suggestion.")
    await state.set_state(Feedback.waiting_feedback_message)

@router.message(Feedback.waiting_feedback_message)
async def send_your_feedback(message: Message, state: FSMContext):
    await notify_student(
        message.bot,
        ADMIN_ID,
        f"💬 NEW FEEDBACK\n\n"
        f"👤 User: {message.from_user.first_name}\n" # type: ignore
        f"🆔 ID: {message.from_user.id}\n" # type: ignore
        f"Message: {message.text}"
    )
    await message.answer("✅ Thank you for your feedback.", reply_markup=non_admin_keyboard())
    await state.clear()

@router.message(F.text == "🌟 Follow us")
async def social_media(message: Message):
    await message.answer(
        f"🌟 Follow Us\n\n"
        f"Telegram:\nhttps://t.me/noorvibes_light\n\n"
        f"LinkedIn:\nhttps://www.linkedin.com/in/yusuf-mohammed-5272572b6\n\n"
        f"Instagram:\nhttps://instagram.com/kebilad_7488"
    )

@router.message(F.text == "👥 Manage Students")
async def students_admin(message:Message):
    telegram_id=int(message.from_user.id) # type: ignore
    if not is_admin(telegram_id):
        await message.answer("Access is denied", show_alert=True)
        return 
    await message.answer(f"Choose what you want", reply_markup=department_admin_keyboard())

@router.callback_query(F.data =="dep_approved")
async def departments_approved(callback:CallbackQuery):
    user_id=callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("Access Denied")  # type: ignore
        return
    departments=get_admin_role(user_id)[1]
    status="Approved"
    students_list=departments_approved_or_rejects(status, departments)
    if not students_list:
        await callback.message.answer("No Approved Students") # type: ignore
    else:
        await callback.message.answer(f"List all {departments} approved students") # type: ignore
        for id, respon in enumerate(students_list):
            await callback.message.answer(f"        {departments} - {id+1}\n👤 Full Name:{respon[1]}\n 📌 Status:{respon[2]}\n 📅 Registration Date:{respon[3]}", reply_markup=approved_students_keyboard(respon[0])) # type: ignore

@router.callback_query(F.data =="dep_rejected")
async def departments_rejected(callback:CallbackQuery):
    user_id=callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("Access Denied")  # type: ignore
        return
    departments=get_admin_role(user_id)[1]
    status="Rejected"
    students_list=departments_approved_or_rejects(status, departments)
    if not students_list:
        await callback.message.answer("No Rejected Students under your departments") # type: ignore
    else:
        await callback.message.answer(f"List all {departments} rejected students") # type: ignore
        for id, respon in enumerate(students_list):
            await callback.message.answer(f"        {departments} - {id+1}\n👤 Full Name:{respon[1]}\n 📌 Status:{respon[2]}\n 📅 Registration Date:{respon[3]}", reply_markup=rejected_students_keyboard(respon[0])) # type: ignore

@router.callback_query(F.data =="dep_pending")
async def departments_pending(callback:CallbackQuery):
    user_id=callback.from_user.id
    if not is_admin(user_id):
        await callback.answer("Access Denied")  # type: ignore
        return
    departments=get_admin_role(user_id)[1]
    status="Pending"
    students_list=departments_approved_or_rejects(status, departments)
    if not students_list:
        await callback.message.answer("No Pending Students under your departments") # type: ignore
    else:
        await callback.answer(f"List all {departments} Pending students")
        for id, respon in enumerate(students_list):
            await callback.answer(f"        {departments} - {id+1}\n👤 Full Name:{respon[1]}\n 📌 Status:{respon[2]}\n 📅 Registration Date:{respon[3]}", reply_markup=rejected_students_keyboard(respon[0]))


@router.callback_query(F.data == "departments_statics")
async def department_statistics(callback: CallbackQuery):
    admin = get_admin_role(callback.from_user.id)  # type: ignore
    if not admin:
        await callback.message.answer("Access denied") # type: ignore
        return
    role, department = admin
    stats = get_departments_statistics(department)
    text = f"""
📊 {department} Statistics

👥 Total Students: {stats['total']}

✅ Approved: {stats['approved']}
❌ Rejected: {stats['rejected']}
⏳ Pending: {stats['pending']}

━━━━━━━━━━━━━━
📚 Courses
━━━━━━━━━━━━━━
"""
    for course, count in stats["courses"]:
        text += f"\n• {course}: {count} students"
    await callback.message.answer(text) # type: ignore

@router.callback_query(F.data == "departments_announcement")
async def all_announcement(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Select target audience for the announcement:", reply_markup=dep_announcements_keyboard()) # type: ignore
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

@router.callback_query(F.data == "dep_all_students_announce")
async def all_students_announcement(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for all students:") # type: ignore
    await state.set_state(Announcement.all_students)
    await callback.answer()

@router.message(Announcement.all_students)
async def send_students_announcement(message: Message, state: FSMContext):
    user_id = message.from_user.id # type: ignore
    if not is_admin(user_id):
        return
    departments=get_admin_role(user_id)[1]
    students=get_student_by_departments(departments)
    await broadcast_message(message, students, "📢 Announcement") # type: ignore
    await state.clear()

@router.callback_query(F.data == "dep_approved_students_announce")
async def approved_announcement(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for approved students:") # type: ignore
    await state.set_state(Announcement.approved_students)
    await callback.answer()

@router.message(Announcement.approved_students)
async def send_approved_announcement(message: Message, state: FSMContext):
    user_id = message.from_user.id # type: ignore
    if not is_admin(user_id):
        return
    departments=get_admin_role(user_id)[1]
    status="Approved"
    students_list=get_department_students_by_status(status, departments)
    await broadcast_message(message, students_list, "📢 ✅ Approved Students Announcement")
    await state.clear()

@router.callback_query(F.data == "dep_rejected_students_announce")
async def rejected_announcement(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for rejected students:") # type: ignore
    await state.set_state(Announcement.rejected_students)
    await callback.answer()

@router.message(Announcement.rejected_students)
async def send_rejected_announcement(message: Message, state: FSMContext):
    user_id = message.from_user.id # type: ignore
    if not is_admin(user_id):
        return
    departments=get_admin_role(user_id)[1]
    status="Rejected"
    students_list=get_department_students_by_status(status, departments)
    await broadcast_message(message, students_list, "❌ Rejected Students Announcement")
    await state.clear()

@router.callback_query(F.data == "dep_pending_students_announce")
async def pending_announcement(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    await callback.message.answer("📢 Send the announcement for pending students:") # type: ignore
    await state.set_state(Announcement.pending_students)
    await callback.answer()

@router.message(Announcement.pending_students)
async def send_pending_announcement(message: Message, state: FSMContext):
    user_id = message.from_user.id # type: ignore
    if not is_admin(user_id):
        return
    departments=get_admin_role(user_id)[1]
    status="Pending"
    students_list=get_department_students_by_status(status, departments)
    await broadcast_message(message, students_list, "⏳ Pending Students Announcement")
    await state.clear()

@router.callback_query(F.data == "dep_export_menu")
async def departments_exports(callback: CallbackQuery):
    user_id = callback.from_user.id # type: ignore
    if not is_admin(user_id):
        return
    departments=get_admin_role(user_id)[1]
    await callback.message.answer(f"📤 Select export type of your departmenst {departments}:",reply_markup=dep_export_keyboard()) # type: ignore
        
@router.callback_query(F.data == "dep_export_all")
async def export_all_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    departments=get_admin_role(user_id)[1]
    excel_file =dep_export_all_students(departments)
    file = BufferedInputFile(excel_file, filename=f"{departments}_all_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="👥 All Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "dep_export_approved")
async def export_approved_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    departments=get_admin_role(user_id)[1]
    excel_file =dep_export_approved_students(departments)
    file = BufferedInputFile(excel_file, filename=f"{departments}_approved_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="✅ Approved Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "dep_export_pending")
async def export_pending_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    departments=get_admin_role(user_id)[1]
    excel_file =dep_export_pending_students(departments)
    file = BufferedInputFile(excel_file, filename=f"{departments}_pending_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="⏳ Pending Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "dep_export_rejected")
async def export_rejected_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    departments=get_admin_role(user_id)[1]
    excel_file = dep_export_rejected_students(departments)
    file = BufferedInputFile(excel_file, filename=f"{departments}_rejected_students.xlsx") # type: ignore
    await callback.message.answer_document(document=file, caption="❌ Rejected Students Export") # type: ignore
    await callback.answer()

@router.callback_query(F.data == "dep_export_statistics")
async def export_statistics_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    departments=get_admin_role(user_id)[1]
    stats = dep_get_statistics(departments)
    text = f"""
{departments} REGISTRATION STATISTICS

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
    await callback.message.answer_document(document=file, caption=f"📊 {departments} Departments Statistics Export") # type: ignore
    await callback.answer()

@router.message(F.text == "📄 Admission Slip")
async def admission_slip(message: Message):
    student = get_student(message.from_user.id) # type: ignore
    if not student:
        await message.answer("❌ You are not registered.")
        return
    if student[10] != "Approved":
        await message.answer(
            "❌ Admission slip is available only for approved students."
        )
        return
    pdf_file = create_admission_pdf(student)
    await message.answer_document(
        document=FSInputFile(pdf_file),
        caption="🎉 Your Admission Slip"
    )