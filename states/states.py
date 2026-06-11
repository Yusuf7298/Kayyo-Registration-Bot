from aiogram.fsm.state import State, StatesGroup
class Registration(StatesGroup):
    department = State()
    course = State()
    full_name = State()
    gender = State()
    phone = State()
    email = State()
    education_status = State()
    language = State()
    birthday = State()
    date_of_registration = State()

class AdminSearch(StatesGroup):
    waiting_for_keyword = State()

class Announcement(StatesGroup):
    all_students = State()
    approved_students=State()
    rejected_students=State()
    pending_students=State()

class Feedback(StatesGroup):
    waiting_feedback_message=State()
class AddDepartment(StatesGroup):
    waiting_name = State()
class AddCourse(StatesGroup):
    waiting_name = State()
    waiting_max= State()
class DeleteDepartment(StatesGroup):
    waiting_name = State()
class DeleteCourse(StatesGroup):
    waiting_name = State()

class EditStudent(StatesGroup):
    waiting_departments = State()
    waiting_course = State()
class EditRegistration(StatesGroup):
    full_name = State()
    phone = State()
    email = State()
    language=State()
    education=State()
    birthday = State()
class AddAdmin(StatesGroup):
    telegram_id = State()
    department = State()
class RemoveAdmin(StatesGroup):
    waiting_telegram_id=State()


    