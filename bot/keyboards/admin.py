from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_approval_kb(payment_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve_payment:{payment_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject_payment:{payment_id}"
                ),
            ]
        ]
    )
