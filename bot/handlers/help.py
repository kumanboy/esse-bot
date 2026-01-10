from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message(lambda m: m.text == "🆘 Yordam")
async def help_handler(message: Message):
    await message.answer(
        "🆘 Yordam\n\n"
        "Muammoingizni batafsil yozib, quyidagi adminga murojaat qiling:\n"
        "@sardor_toshmuhammadov_admin"
    )
