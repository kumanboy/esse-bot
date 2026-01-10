from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Esse tekshirish")],
            [KeyboardButton(text="🆘 Yordam")]
        ],
        resize_keyboard=True
    )
