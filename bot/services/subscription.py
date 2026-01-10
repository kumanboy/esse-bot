from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

CHANNEL_USERNAME = "@sardortoshmuhammad_onatili"


async def is_user_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)

        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )

    except (TelegramBadRequest, TelegramForbiddenError):
        # - user kanalga obuna emas
        # - kanal topilmadi
        # - botda huquq yo‘q
        return False
