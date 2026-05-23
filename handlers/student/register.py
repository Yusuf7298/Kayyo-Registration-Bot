from aiogram import Router, types,F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.register_state import RegisterState
from keyboards.student import *
from utils.courses import COURSES

router = Router()
@router.message(Command("register"))
async def start_registration(message: types.Message, state: FSMContext):
    await state.set_state(RegisterState.full_name)
    await message.answer("👋 Welcome to KayyKof Summer Camp Registration\n\n""Please enter your full name.")
@router.message(RegisterState.full_name)
async def get_full_name(message: types.Message,state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(RegisterState.sex)
    await message.answer("Select your sex.",reply_markup=sex_keyboard)

@router.callback_query(RegisterState.sex,F.data.startswith("sex_"))
async def get_sex(callback: types.CallbackQuery, state: FSMContext):
    sex = callback.data.replace("sex_", "") # type: ignore
    await state.update_data(sex=sex)
    await state.set_state(RegisterState.phone)
    await callback.message.answer("Enter your phone number.") # type: ignore
    await callback.answer()

@router.message(RegisterState.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = message.text
    if not phone.isdigit(): #type: ignore
        await message.answer("❌ Phone number must contain only numbers.")
        return
    await state.update_data(phone=phone)
    await state.set_state(RegisterState.email)
    await message.answer("Enter your email address.")

@router.message(RegisterState.email)
async def get_email(message: types.Message, state: FSMContext):
    email = message.text
    if "@" not in email: # type: ignore
        await message.answer("❌ Invalid email address.")
        return
    await state.update_data(email=email)
    await state.set_state(RegisterState.education_type)
    await message.answer("Select your education type.", reply_markup=education_keyboard)
@router.callback_query(RegisterState.education_type, F.data.startswith("education_"))
async def get_education_type(callback: types.CallbackQuery, state: FSMContext):
    education_type = callback.data.replace("education_", "") # type: ignore
    await state.update_data(education_type=education_type)
    await state.set_state(RegisterState.age) # type: ignore
    if education_type == "school":
        await state.set_state(RegisterState.school_name)
        await callback.message.answer("Enter your school name.") # type: ignore
    else:
        await state.set_state(RegisterState.university_name)
        await callback.message.answer("Enter your university/collage name") # type: ignore
@router.message(RegisterState.school_name)
async def get_school_name(message: types.Message, state: FSMContext):
    await state.update_data(school_name = message.text)
    await state.set_state(RegisterState.grade) # type: ignore
    await message.answer("Enter your grade")

@router.message(RegisterState.university_name)
async def get_university_name(message: types.Message, state: FSMContext):
    await state.update_data(university_name = message.text)
    await state.set_state(RegisterState.university_year)
    await message.answer("Enter Your univeristy / Collage year")

@router.message(RegisterState.grade)
async def get_grade(message: types.Message, state: FSMContext):
    await state.update_data(grade = message.text)
    await state.set_state(RegisterState.languages)
    await message.answer("Select your languages.", reply_markup=language_keyboard)
@router.message(RegisterState.university_year)
async def get_university_year(message: types.Message, state: FSMContext):
    await state.update_data(university_year = message.text)
    await state.set_state(RegisterState.department)
    await message.answer("Enter your department.")

@router.message(RegisterState.department)
async def get_department(message: types.Message, state: FSMContext):
    await state.update_data(department = message.text)
    await state.set_state(RegisterState.languages)
    await message.answer("Select your languages.", reply_markup=language_keyboard)


def generate_course_keyboard(department):
    buttons = []
    for course in COURSES[department]:
        buttons.append([InlineKeyboardButton(text=course, callback_data=f"course_{course}")])
    buttons.append([ InlineKeyboardButton( text="✅ Done", callback_data="courses_done")])
    return InlineKeyboardMarkup(inline_keyboard=buttons )