# bot/handlers/essay.py

from datetime import datetime, timedelta

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states import EssayStates
from bot.services.word_count import count_words
from bot.services.scheduler import scheduler
from bot.services.locks import is_locked, lock, unlock

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

def chunk_text(text: str, size: int = 3800):
    """
    Telegram message limit (~4096).
    Safe margin bilan bo‘lib yuboramiz.
    """
    return [text[i:i + size] for i in range(0, len(text), size)]


# ============================================================
# Handlers
# ============================================================

@router.message(lambda m: m.text == "📝 Esse tekshirish")
async def ask_topic(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # 🔒 Tekshiruv davom etyapti
    if is_locked(user_id):
        await message.answer(
            "⏳ Sizning essengiz hozir tekshirilmoqda.\n"
            "Natija kelgach yana yuborishingiz mumkin."
        )
        return

    # 💳 Balans tekshiruvi (DB)
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
        await message.answer(
            "❌ Mavzu bo‘sh bo‘lmasligi kerak. Iltimos, mavzuni yozing."
        )
        return

    await state.update_data(topic=message.text.strip())
    await message.answer("Endi esseni yuboring.")
    await state.set_state(EssayStates.waiting_for_essay)


@router.message(EssayStates.waiting_for_essay)
async def receive_essay(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # 🔒 Lock tekshiruvi
    if is_locked(user_id):
        await message.answer(
            "⏳ Sizning essengiz hozir tekshirilmoqda.\n"
            "Natija kelgach yana yuborishingiz mumkin."
        )
        return

    # ❌ Faqat text
    if not message.text:
        await message.answer("❌ Esse faqat matn ko‘rinishida yuborilishi kerak.")
        return

    data = await state.get_data()
    topic = (data.get("topic") or "").strip()

    if not topic:
        await message.answer(
            "❌ Mavzu topilmadi. Qaytadan '📝 Esse tekshirish' ni bosing."
        )
        await state.clear()
        return

    essay_text = message.text
    words = count_words(essay_text)

    # ❌ <100 so‘z → 2 ball, STOP (pul yechilmaydi)
    if words < 100:
        await message.answer("❌ Esse 100 ta so‘zdan kam. Natija: 2 ball.")
        await state.clear()
        return

    # ❌ >350 so‘z → rad (pul yechilmaydi)
    if words > 350:
        await message.answer("❌ Esse 350 ta so‘zdan oshmasligi kerak.")
        return

    # 💳 Atomic consume (DB, FOR UPDATE)
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

    # 🔒 Lock ON
    lock(user_id)

    await message.answer(
        f"✅ Essengiz qabul qilindi.\n"
        f"So‘zlar soni: {words}\n\n"
        "Natija 15 daqiqadan so‘ng yuboriladi."
    )

    chat_id = message.chat.id
    bot = message.bot

    # ⏳ Real: 15 daqiqa
    run_time = datetime.now() + timedelta(minutes=15)

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
    OpenAI orqali tekshiradi.
    Xato bo‘lsa → balance REFUND qilinadi.
    """
    try:
        result_text = await check_essay(topic, essay_text)

        # 📤 Telegram limit → chunk
        for part in chunk_text(result_text):
            await bot.send_message(chat_id, part)

    except Exception as e:
        # 💸 Pulni qaytaramiz (DB)
        await refund_balance(user_id, amount=1)

        await bot.send_message(
            chat_id,
            "❌ Esseni tekshirish jarayonida texnik nosozlik yuz berdi.\n\n"
            "💳 Hisobingiz qayta tiklandi.\n"
            "Iltimos, birozdan so‘ng yana urinib ko‘ring."
        )

        print(f"❌ ESSAY CHECK ERROR for {user_id}: {e}")

    finally:
        # 🔓 Lock OFF (har doim)
        unlock(user_id)
