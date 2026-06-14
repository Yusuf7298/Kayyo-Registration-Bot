from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.db import (
    verify_membership
)

router=Router()


@router.message(
Command(
"verify"
)
)
async def verify(
message:Message
):

    parts=(
        message.text
        .split() # type: ignore
    )

    if len(parts)<2:

        await message.answer(
            "Usage:\n/verify telegram_id"
        )

        return

    member=verify_membership(
        int(
            parts[1]
        )
    )

    if not member:

        await message.answer(
            "Member not found."
        )

        return

    await message.answer(
f"""
✅ VERIFIED

👤 {member[0]}

🪪 {member[1]}

📅 Expiry:
{member[2]}

📌 Status:
{member[3]}
"""
    )