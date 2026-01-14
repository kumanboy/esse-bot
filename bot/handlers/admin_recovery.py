from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import Message

from bot.config import ADMIN_ID
from bot.services.db import require_pool
from bot.services.locks import unlock

router = Router()


# =========================
# Permissions
# =========================

def _is_essay_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id == ADMIN_ID)


# =========================
# DB helpers
# =========================

async def _fetch_one(query: str, *args):
    pool = require_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def _execute(query: str, *args):
    pool = require_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


# =========================
# /fix <essay_id>
# =========================

@router.message(lambda m: (m.text or "").startswith("/fix "))
async def fix_essay(message: Message):
    if not _is_essay_admin(message):
        return

    essay_id = message.text.split(maxsplit=1)[1]

    row = await _fetch_one(
        """
        UPDATE essay_reviews
        SET
            status = 'waiting_voice',
            voice_file_id = NULL,
            voice_sent_at = NULL,
            voice_sent_by = NULL,
            voice_msg_id = NULL
        WHERE essay_id = $1
        RETURNING user_id
        """,
        essay_id,
    )

    if not row:
        await message.answer("❌ Essay topilmadi.")
        return

    await message.answer(f"🔁 Essay qayta ochildi: {essay_id}")


# =========================
# /resend <essay_id>
# =========================

@router.message(lambda m: m.text and m.text.startswith("/resend "))
async def resend_voice(message: Message):
    if not _is_essay_admin(message):
        return

    essay_id = message.text.split(maxsplit=1)[1]

    row = await _fetch_one(
        """
        SELECT user_id, voice_file_id
        FROM essay_reviews
        WHERE essay_id = $1
        """,
        essay_id,
    )

    if not row or not row["voice_file_id"]:
        await message.answer("❌ Ovoz topilmadi.")
        return

    sent = await message.bot.send_voice(
        chat_id=row["user_id"],
        voice=row["voice_file_id"],
    )

    await _execute(
        """
        UPDATE essay_reviews
        SET
            status = 'resent',
            sent_to_user_at = $1,
            voice_msg_id = $2
        WHERE essay_id = $3
        """,
        datetime.now(timezone.utc),
        sent.message_id,
        essay_id,
    )

    await message.answer(f"📤 Ovoz qayta yuborildi: {essay_id}")


# =========================
# /cancel <essay_id>
# =========================

@router.message(lambda m: m.text and m.text.startswith("/cancel "))
async def cancel_voice(message: Message):
    if not _is_essay_admin(message):
        return

    essay_id = message.text.split(maxsplit=1)[1]

    row = await _fetch_one(
        """
        UPDATE essay_reviews
        SET
            status = 'waiting_voice',
            voice_file_id = NULL,
            voice_sent_at = NULL,
            voice_sent_by = NULL,
            voice_msg_id = NULL
        WHERE essay_id = $1
        RETURNING user_id
        """,
        essay_id,
    )

    if not row:
        await message.answer("❌ Essay topilmadi.")
        return

    unlock(row["user_id"])
    await message.answer(f"❌ Ovoz bekor qilindi: {essay_id}")
