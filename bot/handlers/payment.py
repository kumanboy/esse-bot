import time

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states import PaymentStates
from bot.config import CARD_INFO, MONEY_ID
from bot.keyboards.admin import admin_approval_kb
from bot.keyboards.main import main_menu
from bot.services.payments import create_payment

router = Router()


@router.message(F.text == "⬅️ Ortga")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu())


@router.message(F.text == "💳 Hisobni to‘ldirish")
async def ask_for_payment(message: Message, state: FSMContext):
    await message.answer(CARD_INFO)
    await state.set_state(PaymentStates.waiting_for_receipt)


@router.message(PaymentStates.waiting_for_receipt)
async def receive_receipt(message: Message, state: FSMContext):
    user = message.from_user
    user_id = user.id
    username = user.username or "username yo‘q"

    # ❌ Must be photo or document
    if message.photo is None and message.document is None:
        await message.answer("❌ Iltimos, check yoki screenshot yuboring.")
        return

    payment_id = f"{user_id}_{int(time.time())}"

    # ✅ SAFE user note (caption OR text OR empty)
    user_note = message.caption or message.text or "(Izoh yo‘q)"

    admin_caption = (
        "🧾 YANGI TO‘LOV CHEKI\n\n"
        f"👤 User ID: {user_id}\n"
        f"👤 Username: @{username}\n"
        f"🆔 Payment ID: {payment_id}\n\n"
        f"📝 Izoh:\n{user_note}\n\n"
        "Quyidagi tugmalar orqali to‘lovni tasdiqlang yoki rad eting."
    )

    # =========================
    # PHOTO RECEIPT
    # =========================
    if message.photo is not None:
        photo = message.photo[-1]
        file_id = photo.file_id

        await create_payment(
            payment_id=payment_id,
            user_id=user_id,
            username=username,
            receipt_kind="photo",
            receipt_file_id=file_id,
            amount=1,
        )

        await message.bot.send_photo(
            chat_id=MONEY_ID,
            photo=file_id,
            caption=admin_caption,
            reply_markup=admin_approval_kb(payment_id),
        )

    # =========================
    # DOCUMENT / SCREENSHOT
    # =========================
    else:
        document = message.document
        file_id = document.file_id

        await create_payment(
            payment_id=payment_id,
            user_id=user_id,
            username=username,
            receipt_kind="document",
            receipt_file_id=file_id,
            amount=1,
        )

        await message.bot.send_document(
            chat_id=MONEY_ID,
            document=file_id,
            caption=admin_caption,
            reply_markup=admin_approval_kb(payment_id),
        )

    await state.clear()

    # ✅ User confirmation
    await message.answer(
        "⏳ To‘lovingiz qabul qilindi.\n"
        "Admin tomonidan tekshirilgach sizga xabar beriladi."
    )
