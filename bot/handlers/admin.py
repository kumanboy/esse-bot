# bot/handlers/admin.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.config import MONEY_ID
from bot.services.balance import add_balance
from bot.services.payments import decide_payment

router = Router()


# ============================================================
# Permission check (PAYMENT ADMIN ONLY)
# ============================================================

def _is_payment_admin(callback: CallbackQuery) -> bool:
    return callback.from_user.id == MONEY_ID


# ============================================================
# Helpers
# ============================================================

async def _safe_edit_caption(callback: CallbackQuery, text: str):
    try:
        await callback.message.edit_caption(text)
    except TelegramBadRequest:
        # message might be text, deleted, or already edited
        pass


# ============================================================
# Core logic
# ============================================================

async def _handle_payment_decision(callback: CallbackQuery, *, approved: bool):
    # 🔐 STRICT permission check
    if not _is_payment_admin(callback):
        await callback.answer(
            "❌ Siz to‘lovlarni tasdiqlash huquqiga ega emassiz.",
            show_alert=True
        )
        return

    payment_id = callback.data.split(":", 1)[1]

    # 🔄 Idempotent decision (DB-level safety)
    payment_row = await decide_payment(
        payment_id=payment_id,
        decided_by=callback.from_user.id,  # MONEY_ID logged
        approve=approved,
    )

    if payment_row is None:
        await callback.answer(
            "⚠️ Bu to‘lov allaqachon ko‘rib chiqilgan yoki topilmadi.",
            show_alert=True
        )
        return

    user_id = int(payment_row["user_id"])
    amount = int(payment_row["amount"])

    if approved:
        # 💳 Balance update
        await add_balance(user_id, amount)

        await _safe_edit_caption(callback, "✅ To‘lov tasdiqlandi.")

        # 📩 Notify user
        await callback.bot.send_message(
            user_id,
            f"✅ To‘lovingiz tasdiqlandi.\n\n"
            f"Balansingizga {amount} ta esse tekshirish qo‘shildi."
        )

        # 🧾 Optional confirmation to MONEY_ID
        await callback.bot.send_message(
            MONEY_ID,
            f"🧾 TO‘LOV TASDIQLANDI\n\n"
            f"Payment ID: {payment_id}\n"
            f"User ID: {user_id}\n"
            f"Amount: {amount}"
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


# ============================================================
# Routers
# ============================================================

@router.callback_query(F.data.startswith("approve_payment:"))
async def approve_payment(callback: CallbackQuery):
    await _handle_payment_decision(callback, approved=True)


@router.callback_query(F.data.startswith("reject_payment:"))
async def reject_payment(callback: CallbackQuery):
    await _handle_payment_decision(callback, approved=False)
