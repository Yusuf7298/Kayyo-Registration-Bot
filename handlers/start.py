from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database.db import SUPER_ADMIN_ID,is_admin
from keyboards.menus import departmenstAdmin_keyboard, admin_keyboard, non_admin_keyboard

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    first_name = message.from_user.first_name or "Student"  # type: ignore
    user_id = message.from_user.id  # type: ignore
    if user_id == SUPER_ADMIN_ID:
        await message.answer(f"👋 Welcome Super Admin {first_name}",reply_markup=admin_keyboard())
        return
    if not is_admin(user_id):
        await message.answer(
        f"""
Welcome {first_name} 👋

Welcome to the Summer Camp Registration Bot.

Use the menu below to register or check your status.
""",
        reply_markup=non_admin_keyboard()  # Student Menu
    )
        
        return
    await message.answer(f"👋 Welcome Department Admin {first_name}",reply_markup=departmenstAdmin_keyboard())  # Department Admin Menu

@router.message(F.text == "ℹ️ Help")
async def help_command(message: Message):
    await message.answer(
        f"📚 Available Options\n\n"
        f"📝 Register\nRegister for the Summer Camp.\n\n"
        f"📌 Status\nCheck your registration status.\n\n"
        f"❌ Cancel\nCancel the current registration process.\n\n"
        f"If you need assistance, contact the administrator."
    )

@router.message(Command("about"))
async def about_command(message: Message):
    await message.answer(
        f"ℹ️ About This Bot\n\n"
        f"This bot handles registration pipelines for the Summer Camp. "
        f"Built using the robust aiogram framework with asynchronous event handlers, "
        f"FSM state engines, and modular router controls."
    )