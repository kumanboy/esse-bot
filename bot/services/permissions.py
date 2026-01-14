from aiogram.types import CallbackQuery, Message
from bot.config import ADMIN_ID, MONEY_ID


def is_payment_admin(user_id: int) -> bool:
    return user_id == MONEY_ID


def is_essay_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID
