from datetime import datetime

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from states.states import MembershipRegistration
from keyboards.menus import (
    membership_types_keyboard,
    membership_duration_keyboard,
    gender,
    membership_menu_keyboard
)

from database.db import (
    get_membership,
    get_membership_by_phone,
    get_membership_status,
    renew_membership,
    save_membership,
    get_membership_types,
    get_duration_months,
    SUPER_ADMIN_ID
)

from handlers.registration import notify_student
from utils.membership_pdf import (
    create_membership_pdf
)
router = Router()
@router.message(
    F.text.in_([
        "🪪 Membership Registration",
        "🪪 Membership"
    ])
)
async def membership_start(message: Message,state: FSMContext):
    member = get_membership(message.from_user.id) # type: ignore
    if member:
        await message.answer(f"🪪 Membership\nWelcome back {member[3]} You already submitted registration.", reply_markup=membership_menu_keyboard())
        return
    await message.answer("👤 Enter Full Name:")
    await state.set_state(MembershipRegistration.full_name)
@router.message(MembershipRegistration.full_name)
async def member_name(message: Message,state: FSMContext):
    await state.update_data(full_name=message.text.strip()) # type: ignore
    await message.answer("🚻 Select Gender:",reply_markup=gender)
    await state.set_state(MembershipRegistration.genders)
@router.callback_query(MembershipRegistration.genders)
async def member_gender(callback: CallbackQuery,state: FSMContext):
    await callback.answer()
    await state.update_data(gender=callback.data)
    await callback.message.answer("📱 Enter Phone:") # type: ignore
    await state.set_state(MembershipRegistration.phone)
@router.message(MembershipRegistration.phone)
async def member_phone(message: Message,state: FSMContext):
    phone = message.text.strip() # type: ignore
    if get_membership_by_phone(phone):
        await message.answer("❌ Phone already exists. Use:\n📌 Membership Status\n🔄 Renew Membership")
        return
    await state.update_data(phone=phone)
    await message.answer("📧 Enter Email:")
    await state.set_state(MembershipRegistration.email)
@router.message(MembershipRegistration.email)
async def member_email(message: Message,state: FSMContext):
    email = message.text.strip() # type: ignore
    if "@" not in email:
        await message.answer("❌ Invalid Email")
        return
    await state.update_data(email=email)
    await message.answer("💼 Enter Occupation:")
    await state.set_state(MembershipRegistration.occupation)
@router.message(MembershipRegistration.occupation)
async def occupation(message: Message,state: FSMContext):
    await state.update_data(occupation=message.text.strip()) # type: ignore
    await message.answer("📍 Enter Address:")
    await state.set_state(MembershipRegistration.address)

@router.message(MembershipRegistration.address)
async def address(message: Message,state: FSMContext):
    await state.update_data(address=message.text.strip()) # type: ignore
    await message.answer("🪪 Select Membership Type",reply_markup=membership_types_keyboard())
    await state.set_state(MembershipRegistration.membership_type)

@router.callback_query(MembershipRegistration.membership_type, F.data.startswith("member_type_"))
async def member_type(callback: CallbackQuery,state: FSMContext):
    selected = ""
    type_id = int(callback.data.split("_")[2]) # type: ignore
    for item in get_membership_types():
        if item[0] == type_id:
            selected = item[1]

    await state.update_data(membership_type=selected)
    await callback.message.answer("⏳ Choose Duration",reply_markup=membership_duration_keyboard()) # type: ignore
    await state.set_state(MembershipRegistration.duration)

@router.callback_query(MembershipRegistration.duration,F.data.startswith("member_duration_"))
async def duration(callback: CallbackQuery,state: FSMContext):
    duration_id = int(callback.data.split("_")[2]) # type: ignore
    months = get_duration_months(duration_id)
    await state.update_data(duration=months)
    await callback.message.answer( # type: ignore
"""
📷 Upload Membership Photo

Requirements:
• Clear face
• Portrait
"""
    )

    await state.set_state(
        MembershipRegistration.photo
    )

@router.message(MembershipRegistration.photo, F.photo)
async def photo(message: Message,state: FSMContext):
    data = await state.get_data()
    photo_id = (message.photo[-1].file_id) # type: ignore
    reg_date = (datetime.now().strftime("%Y-%m-%d"))
    saved = save_membership(
        message.from_user.id, # type: ignore
        data["full_name"],
        data["gender"],
        data["phone"],
        data["email"],
        data["occupation"],
        data["address"],
        data["membership_type"],
        data["duration"],
        reg_date,
        data.get("photo_file_id")# type: ignore
    )

    if not saved:
        await message.answer("❌ Registration Failed")
        return
    await message.answer(
"""
✅ Membership Submitted
Status:
⏳ Pending Approval
"""
    )
    await notify_student(
        message.bot,
        SUPER_ADMIN_ID,
        f"""
🆕 New Membership
{data["full_name"]}
{data["membership_type"]}
"""
    )
    await state.clear()

@router.message(F.text=="📌 Membership Status")
async def status(message: Message):
    member = get_membership(message.from_user.id) # type: ignore
    if not member:
        await message.answer("❌ No Membership")
        return
    await message.answer(
f"""
🪪 Membership

👤 Full Name: {member[3]}

📱 Phone: {member[5]}

📧 Email: {member[6]}

⭐ Type: {member[9]}

⏳ Duration: {member[10]} Months

📌 Status: {member[13]}
"""
    )

@router.message(F.text=="🔄 Renew Membership")
async def renew(message: Message):
    status = get_membership_status(message.from_user.id) # type: ignore
    if status != "Approved":
        await message.answer("❌ Not Approved")
        return
    renew_membership(message.from_user.id,3) # type: ignore
    await message.answer(
"""
✅ Renewed

+3 Months
"""
    )

@router.message(F.text=="🆔 Download Membership Card")
async def download(message: Message):
    status = get_membership_status(message.from_user.id) # type: ignore
    if status != "Approved":
        await message.answer(
"""
❌ Membership not approved.
Download available after approval.
"""
        )
        return
    pdf = create_membership_pdf(message.from_user.id) # type: ignore
    if not pdf:
        await message.answer("❌ Card generation failed")
        return
    await message.answer_document(
        BufferedInputFile(
            pdf.read(),
            filename=pdf.name
        ),
        caption="🪪 Membership Card"
    )