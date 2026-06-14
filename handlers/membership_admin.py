from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from database.db import *
from keyboards.menus import (
    member_admin,
    members_admins,
    membership_action_keyboard,
    refresh_back_keyboard,
    membership_export_keyboard,
    admin_panel_keyboard
)

from aiogram.types import BufferedInputFile
from database.db import export_members_excel

router = Router()
@router.message(F.text == "🪪 Manage Membership")
async def manage_membership(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:  # type: ignore
        await message.answer("❌ Access denied.")
        return
    await message.answer("🪪 Membership Administration",reply_markup=members_admins())
async def render_members(event, rows, title):
    user = event.from_user
    if user.id != SUPER_ADMIN_ID:
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Access denied",show_alert=True)
        else:
            await event.answer("❌ Access denied")
        return
    target = (event.message if isinstance(event, CallbackQuery) else event)
    if not rows:
        await target.answer("📭 No members found.") # type: ignore
        return
    await target.answer(f"{title}\n\nTotal Members: {len(rows)}") # type: ignore
    for index, row in enumerate(rows, start=1):
        await target.answer( # type: ignore
f"""
🪪 Member {index}

👤 Full Name:{row[2]}
🚻 Gender: {row[3]}
📱 Phone: {row[4]}
📧 Email: {row[5]}
💼 Occupation: {row[6]}
📍 Address: {row[7]}
🪪 Type: {row[8]}
⏳ Duration: {row[9]} Months
📌 Status: {row[11]}
""", reply_markup=membership_action_keyboard(row[1]))
    await target.answer("⬇ Actions",reply_markup=refresh_back_keyboard()) # type: ignore

@router.message(F.text == "👥 All Members")
async def all_members(message: Message):
    await render_members(message,get_all_members(),"👥 All Members")

@router.message(F.text == "✅ Approved Members")
async def approved_members(message: Message):
    await render_members(message,get_approved_members(),"✅ Approved Members")

@router.message(F.text == "❌ Rejected Members")
async def rejected_members(message: Message):
    await render_members(message,get_rejected_members(),"❌ Rejected Members")

@router.message(F.text == "⏳ Pending Members")
async def pending_members(message: Message):
    await render_members(message,get_pending_members(),"⏳ Pending Members")

@router.callback_query(F.data.startswith("approve_member:"))
async def approve_member(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[1])  # type: ignore
    approve_membership(telegram_id)
    member = get_membership(telegram_id)
    await callback.bot.send_message(telegram_id,f"🎉 Membership Approved Dear {member[2]} Your membership has been approved. Now available:\n📌 Membership Status \n🆔 Download Membership Card \n🔄 Renew Membership") # type: ignore
    await callback.message.answer("✅ Membership Approved.")  # type: ignore
    await callback.answer()

@router.callback_query(F.data.startswith("reject_member:"))
async def reject_member(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[1])  # type: ignore
    reject_membership(telegram_id)
    await callback.bot.send_message(telegram_id,"❌ Membership Rejected Unfortunately your membership request was not approved.") # type: ignore
    await callback.message.answer("❌ Membership Rejected.")  # type: ignore
    await callback.answer()

@router.callback_query(F.data.startswith("view_details_members:"))
async def view_details(callback: CallbackQuery):
    telegram_id = int(callback.data.split(":")[1])  # type: ignore
    member = get_membership(telegram_id)
    if not member:
        await callback.answer("Member not found",show_alert=True)
        return
    await callback.message.answer(  # type: ignore
f"""
🪪 Membership Details
👤 Full Name: {member[2]}
🚻 Gender: {member[3]}
📱 Phone: {member[4]}
📧 Email: {member[5]}
💼 Occupations: {member[6]}
📍 Address: {member[7]}
⭐ Type: {member[8]}
⏳ Durations {member[9]} Months
📌 Status: {member[11]}
""",reply_markup=membership_action_keyboard(telegram_id))
    await callback.answer()

@router.message(F.text =="📊 Membership Statistics")
async def statistics(message: Message):
    stats = get_membershipstatistics()
    await message.answer(
f"""
📊 Membership Statistics

👥 Total Members: {stats[0]}
━━━━━━━━━━
📌 Status 

✅ Approved: {stats[1]}
❌ Rejected: {stats[2]}
⏳ Pending: {stats[3]}

━━━━━━━━━━
🪪 Membership Types

🥉 Basic: {stats[4]}
🥈 Premium: {stats[5]}
🥇 VIP: {stats[6]}

━━━━━━━━━━
⏳ Duration

3 Months: {stats[7]}
6 Months: {stats[8]}
12 Months: {stats[9]}

━━━━━━━━━━
🚻 Gender

👦 Male: {stats[10]}
👧 Female: {stats[11]}
""")
    
@router.message(F.text =="📤 Export Members")
async def export_menu(message: Message):
    await message.answer("Export what you want", reply_markup=membership_export_keyboard())

@router.callback_query(F.data == "export_all_members")
async def export_all(callback: CallbackQuery):
    rows = get_all_members()
    if not rows:
        await callback.answer("No members.",show_alert=True)
        return
    file = export_members_excel(rows)
    await callback.message.answer_document( # type: ignore
        BufferedInputFile(file.read(),filename="all_members.xlsx"),
        caption="📤 All Members Export")
    await callback.answer()

@router.callback_query(F.data == "export_approved_members")
async def export_approved(callback: CallbackQuery):
    rows = get_approved_members()
    file = export_members_excel(rows)
    await callback.message.answer_document( # type: ignore
        BufferedInputFile(
            file.read(),
            filename="approved_members.xlsx"
        )
    )
    await callback.answer()

@router.callback_query(F.data == "export_rejected_members")
async def export_rejected(callback: CallbackQuery):
    rows = get_rejected_members()
    file = export_members_excel(rows)
    await callback.message.answer_document( # type: ignore
        BufferedInputFile(file.read(),filename="rejected_members.xlsx")
    )
    await callback.answer()

@router.callback_query(F.data == "export_pending_members")
async def export_pending(callback: CallbackQuery):
    rows = get_pending_members()
    file = export_members_excel(rows)
    await callback.message.answer_document( # type: ignore
        BufferedInputFile(file.read(),filename="pending_members.xlsx"))
    await callback.answer()