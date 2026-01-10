# bot/handlers/admin.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.config import ADMIN_ID
from bot.services.balance import add_balance
from bot.services.payments import decide_payment

router = Router()


def _is_admin(callback: CallbackQuery) -> bool:
    return callback.from_user.id == ADMIN_ID


async def _safe_edit_caption(callback: CallbackQuery, text: str):
    try:
        await callback.message.edit_caption(text)
    except TelegramBadRequest:
        pass


async def _handle_payment_decision(callback: CallbackQuery, *, approved: bool):
    if not _is_admin(callback):
        await callback.answer("❌ Siz admin emassiz.", show_alert=True)
        return

    payment_id = callback.data.split(":", 1)[1]

    payment_row = await decide_payment(
        payment_id=payment_id,
        decided_by=callback.from_user.id,
        approve=approved,
    )

    if payment_row is None:
        await callback.answer(
            "⚠️ Bu to‘lov allaqachon ko‘rib chiqilgan yoki topilmadi."
        )
        return

    user_id = int(payment_row["user_id"])
    amount = int(payment_row["amount"])

    if approved:
        # ✅ ASYNC FIX
        await add_balance(user_id, amount)

        await _safe_edit_caption(callback, "✅ To‘lov tasdiqlandi.")
        await callback.bot.send_message(
            user_id,
            f"✅ To‘lovingiz tasdiqlandi.\n\n"
            f"Balansingizga {amount} ta esse tekshirish qo‘shildi."
        )
        await callback.answer("✅ To‘lov tasdiqlandi.")
    else:
        await _safe_edit_caption(callback, "❌ To‘lov rad etildi.")
        await callback.bot.send_message(
            user_id,
            "❌ To‘lovingiz rad etildi.\n\n"
            "Iltimos, to‘lovni qayta amalga oshiring."
        )
        await callback.answer("❌ To‘lov rad etildi.")


@router.callback_query(F.data.startswith("approve_payment:"))
async def approve_payment(callback: CallbackQuery):
    await _handle_payment_decision(callback, approved=True)


@router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment(callback: CallbackQuery):
    await _handle_payment_decision(callback, approved=False)
