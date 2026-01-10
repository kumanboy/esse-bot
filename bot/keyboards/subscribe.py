from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def subscribe_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga obuna bo‘lish",
                    url="https://t.me/sardortoshmuhammad_onatili"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish",
                    callback_data="check_subscription"
                )
            ]
        ]
    )
