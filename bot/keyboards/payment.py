from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def payment_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Hisobni to‘ldirish")],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True
    )
