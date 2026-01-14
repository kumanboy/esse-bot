# bot/handlers/admin_voice.py

from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.types import Message

from bot.config import ADMIN_ID
from bot.services.db import require_pool
from bot.services.locks import unlock
from bot.services.scheduler import scheduler

router = Router()


def _is_essay_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id == ADMIN_ID)


@router.message(lambda m: m.voice is not None)
async def handle_admin_voice(message: Message):
    # 🔐 Only essay admin
    if not _is_essay_admin(message):
        return

    # ❌ Must be reply to AI result message
    if not message.reply_to_message:
        await message.answer("❌ Ovozli izoh faqat AI natija xabariga REPLY bo‘lishi kerak.")
        return

    replied = message.reply_to_message
    admin_chat_id = message.chat.id
    admin_msg_id = replied.message_id

    pool = require_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT essay_id, status
            FROM essay_reviews
            WHERE admin_chat_id = $1
              AND admin_msg_id = $2
            """,
            admin_chat_id,
            admin_msg_id,
        )

        if not row:
            await message.answer("❌ Bu xabar hech qaysi esse bilan bog‘lanmagan.")
            return

        if row["status"] in ("voice_scheduled", "voice_sent"):
            await message.answer("⚠️ Bu esse uchun ovozli izoh allaqachon qabul qilingan.")
            return

        essay_id = row["essay_id"]

        now_aware = datetime.now(timezone.utc)   # timestamptz columns
        # voiced_at in your table is timestamptz, so we use aware
        await conn.execute(
            """
            UPDATE essay_reviews
            SET
                voice_file_id = $1,
                voiced_at = $2,
                voice_sent_by = $3,
                status = 'voice_scheduled'
            WHERE essay_id = $4
            """,
            message.voice.file_id,
            now_aware,
            ADMIN_ID,
            essay_id,
        )

    # ⏳ Schedule sending after 30 minutes (you used 30 sec for testing)
    run_time = now_aware + timedelta(minutes=30)

    scheduler.add_job(
        send_voice_to_user,
        trigger="date",
        run_date=run_time,
        args=[message.bot, essay_id],
        id=f"send_voice_{essay_id}",
        replace_existing=True,
    )

    await message.answer(
        "✅ Ovozli izoh qabul qilindi.\n"
        "⏳ Foydalanuvchiga 30 daqiqadan so‘ng yuboriladi."
    )


async def send_voice_to_user(bot, essay_id: str):
    pool = require_pool()
    user_id = None

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, voice_file_id, status
                FROM essay_reviews
                WHERE essay_id = $1
                """,
                essay_id,
            )

            if not row:
                return

            user_id = int(row["user_id"])

            # ✅ Only send if scheduled
            if row["status"] != "voice_scheduled":
                return

            sent = await bot.send_voice(
                chat_id=user_id,
                voice=row["voice_file_id"],
                caption=(
                    "🎙 Ustozning ovozli izohi\n\n"
                    "Essengiz bo‘yicha batafsil fikrlar yuborildi."
                ),
            )

            now_aware = datetime.now(timezone.utc)  # timestamptz
            now_naive_utc = datetime.utcnow()       # timestamp (no tz) columns

            # ✅ atomic update: only if still scheduled
            await conn.execute(
                """
                UPDATE essay_reviews
                SET status          = 'voice_sent',
                    sent_to_user_at = $2,
                    voice_sent_at   = $3,
                    voice_msg_id    = $4
                WHERE essay_id = $1
                  AND status = 'voice_scheduled'
                """,
                essay_id,
                now_aware,
                now_naive_utc,
                sent.message_id,
            )

            # updated looks like "UPDATE 1" or "UPDATE 0"
            # If UPDATE 0: it means already changed by another action (double protection)

    except Exception as e:
        # ✅ Don’t block unlock even if DB fails
        print(f"❌ send_voice_to_user ERROR essay_id={essay_id}: {e}")

    finally:
        # 🔓 Always unlock user so they can submit again
        if user_id is not None:
            unlock(user_id)
