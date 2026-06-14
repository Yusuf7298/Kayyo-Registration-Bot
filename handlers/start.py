from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from database.db import (SUPER_ADMIN_ID,is_admin,get_admin_role)
from keyboards.menus import (admin_panel_keyboard,admin_keyboard, departmenstAdmin_keyboard,membership_menu_keyboard,non_admin_keyboard,registration_choice_keyboard)
router = Router()
@router.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id  # type: ignore
    name = message.from_user.first_name or "User"  # type: ignore
    if user_id == SUPER_ADMIN_ID:
        await message.answer(f"👑 Welcome Super Admin {name}",reply_markup=admin_panel_keyboard())
        return
    admin = get_admin_role(user_id)
    if admin:
        role, department = admin
        await message.answer(
            f"""
👋 Welcome Admin
Department:
🏢 {department}
""",
            reply_markup=departmenstAdmin_keyboard()
        )
        return
    await message.answer(
f"""
Welcome {name} 👋

Choose registration system:
""",
        reply_markup=registration_choice_keyboard()
    )

@router.message(F.text == "ℹ️ Help")
async def help_command(message: Message):

    await message.answer(
"""
📚 Available Options

🎓 Summer Camp
Register and track summer camp.

🪪 Membership
Register and manage memberships.

❌ Cancel
Cancel current process.
"""
    )
@router.message(Command("about"))
async def about_command(message: Message):
    await message.answer(
"""
ℹ️ About

This bot manages:

🎓 Summer Camp Registration
🪪 Membership Registration

Built using Aiogram + FSM + SQLite.
"""
    )

@router.callback_query(F.data=="back_registration")
async def back_registration(callback: CallbackQuery):
    await callback.message.edit_text("Choose registration system:") # type: ignore
    await callback.message.answer( # type: ignore
reply_markup=registration_choice_keyboard()
    )
    await callback.answer()


@router.message(F.text=="🔙 Back To Admin Menu")
async def back_home(message: Message):
    await message.answer(
        "Choose registration type:",
        reply_markup=admin_panel_keyboard()
    )