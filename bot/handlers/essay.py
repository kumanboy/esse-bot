# bot/handlers/essay.py

from datetime import datetime, timedelta
import uuid
from bot.keyboards.main import main_menu

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states import EssayStates
from bot.services.word_count import count_words
from bot.services.scheduler import scheduler
from bot.services.locks import is_locked, lock, unlock

from bot.config import ADMIN_ID
from bot.services.db import require_pool

# ✅ DB-based balance
from bot.services.balance import (
    get_balance,
    consume_balance,
    refund_balance,
)

from bot.keyboards.payment import payment_keyboard
from bot.services.essay_checker import check_essay

router = Router()

# ============================================================
# Helpers
# ============================================================

def chunk_text(text: str, size: int = 3200) -> list[str]:
    """
    Telegram limit ~4096.
    Adminga yuborishda caption/headers ham bo‘ladi, shuning uchun 3200 xavfsiz.
    """
    if not text:
        return [""]
    return [text[i:i + size] for i in range(0, len(text), size)]


async def _send_admin_ai_result(
    bot,
    *,
    essay_id: str,
    user_id: int,
    topic: str,
    result_text: str,
) -> int:
    """
    1) Adminga "anchor" xabar yuboradi (admin reply qilishi uchun)
    2) AI natijani alohida chunk message qilib yuboradi (message too long muammosiz)
    3) anchor message_id ni qaytaradi
    """
    anchor_text = (
        "📝 YANGI ESSE TEKSHIRILDI\n\n"
        f"🆔 Essay ID: {essay_id}\n"
        f"👤 User ID: {user_id}\n"
        f"📝 Mavzu: {topic}\n\n"
        "🎙 Iltimos, SHU XABARGA REPLY qilib ovozli izoh yuboring.\n"
        "⏳ Ovozli izoh foydalanuvchiga 30 daqiqadan keyin yuboriladi.\n\n"
        "👇 AI natija quyidagi xabarlarda:"
    )

    anchor_msg = await bot.send_message(chat_id=ADMIN_ID, text=anchor_text)

    # AI natijani chunk qilib yuboramiz
    parts = chunk_text(result_text, size=3200)

    # Ko‘p esse bo‘lsa aralashib ketmasligi uchun har bir qismga Essay ID qo‘shamiz
    for idx, part in enumerate(parts, start=1):
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📊 AI NATIJA (Essay ID: {essay_id}) — {idx}/{len(parts)}\n\n"
                f"{part}"
            )
        )

    return anchor_msg.message_id


# ============================================================
# Handlers
# ============================================================

@router.message(lambda m: m.text == "📝 Esse tekshirish")
async def ask_topic(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if is_locked(user_id):
        await message.answer(
            "⏳ Sizning essengiz hozir tekshirilmoqda.\n"
            "Natija kelgach yana yuborishingiz mumkin."
        )
        return

    balance = await get_balance(user_id)
    if balance < 1:
        await message.answer(
            "❌ Hisobingizda tekshiruvlar qolmagan.\n\n"
            "1 ta esse tekshirish narxi: 10 000 so‘m.\n"
            "Hisobni to‘ldirish uchun quyidagi tugmani bosing.",
            reply_markup=payment_keyboard()
        )
        return

    await message.answer("Iltimos, mavzuni yozing.")
    await state.set_state(EssayStates.waiting_for_topic)


@router.message(EssayStates.waiting_for_topic)
async def receive_topic(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("❌ Mavzu bo‘sh bo‘lmasligi kerak. Iltimos, mavzuni yozing.")
        return

    await state.update_data(topic=message.text.strip())
    await message.answer("Endi esseni yuboring.")
    await state.set_state(EssayStates.waiting_for_essay)


@router.message(EssayStates.waiting_for_essay)
async def receive_essay(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if is_locked(user_id):
        await message.answer(
            "⏳ Sizning essengiz hozir tekshirilmoqda.\n"
            "Natija kelgach yana yuborishingiz mumkin.\n\n"
            "🏠 Asosiy menyu:",
            reply_markup=main_menu()
        )
        return

    if not message.text:
        await message.answer("❌ Esse faqat matn ko‘rinishida yuborilishi kerak.")
        return

    data = await state.get_data()
    topic = (data.get("topic") or "").strip()

    if not topic:
        await message.answer("❌ Mavzu topilmadi. Qaytadan '📝 Esse tekshirish' ni bosing.")
        await state.clear()
        return

    essay_text = message.text
    words = count_words(essay_text)

    # STOP CASES (pul yechilmaydi)
    if words < 100:
        await message.answer("❌ Esse 100 ta so‘zdan kam. Natija: 2 ball.")
        await state.clear()
        return

    if words > 350:
        await message.answer("❌ Esse 350 ta so‘zdan oshmasligi kerak.")
        return

    # Balance consume
    consumed = await consume_balance(user_id)
    if not consumed:
        await message.answer(
            "❌ Hisobingizda tekshiruvlar qolmagan.\n\n"
            "1 ta esse tekshirish narxi: 10 000 so‘m.\n"
            "Hisobni to‘ldirish uchun quyidagi tugmani bosing.",
            reply_markup=payment_keyboard()
        )
        await state.clear()
        return

    # Lock ON
    lock(user_id)

    await message.answer(
        f"✅ Essengiz qabul qilindi.\n"
        f"So‘zlar soni: {words}\n\n"
        "Natija ustoz tomonidan ovozli izoh shaklida yuboriladi."
    )

    chat_id = message.chat.id
    bot = message.bot

    # TEST: 30 sec (keyin 15 min qilasiz)
    run_time = datetime.now() + timedelta(seconds=30)

    scheduler.add_job(
        send_result_with_openai,
        trigger="date",
        run_date=run_time,
        args=[bot, chat_id, user_id, topic, essay_text],
        id=f"essay_result_{user_id}",
        replace_existing=True,
    )

    await state.clear()


# ============================================================
# Background job
# ============================================================

async def send_result_with_openai(
    bot,
    chat_id: int,
    user_id: int,
    topic: str,
    essay_text: str,
):
    """
    ✅ AI natija USERga emas — ADMIN'ga yuboriladi va DBga yoziladi.
    ❌ Xato bo‘lsa → refund + userga xabar + unlock.
    """
    essay_id = f"essay_{uuid.uuid4().hex}"

    try:
        result_text = await check_essay(topic, essay_text)

        # ✅ Send to ADMIN safely (chunked) + get anchor msg_id
        anchor_msg_id = await _send_admin_ai_result(
            bot,
            essay_id=essay_id,
            user_id=user_id,
            topic=topic,
            result_text=result_text,
        )

        # ✅ Save to DB (anchor only)
        pool = require_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO essay_reviews (
                    essay_id,
                    user_id,
                    topic,
                    essay_text,
                    ai_result,
                    admin_chat_id,
                    admin_msg_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                essay_id,
                user_id,
                topic,
                essay_text,
                result_text,
                ADMIN_ID,
                anchor_msg_id,
            )

        # ❗ USERga natija yuborilmaydi.
        # unlock ham qilinmaydi: admin voice workflow tugaganda ochiladi.

    except Exception as e:
        await refund_balance(user_id, amount=1)

        await bot.send_message(
            chat_id,
            "❌ Esseni tekshirish jarayonida texnik nosozlik yuz berdi.\n\n"
            "💳 Hisobingiz qayta tiklandi.\n"
            "Iltimos, birozdan so‘ng yana urinib ko‘ring."
        )

        unlock(user_id)
        print(f"❌ ESSAY CHECK ERROR for {user_id}: {e}")
