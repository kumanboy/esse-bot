import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.keyboards.main import main_menu
from bot.keyboards.subscribe import subscribe_keyboard
from bot.handlers import essay, subscription, help, payment, admin
from bot.services.scheduler import start_scheduler
from bot.services.subscription import is_user_subscribed

# ✅ TO‘G‘RI IMPORTLAR
from bot.services.db import init_db
from bot.services.balance import grant_free_balance, has_used_free


async def main():
    # ✅ DB pool init (ENG MUHIM QATOR)
    await init_db()

    # ✅ Scheduler
    start_scheduler()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(Command("start"))
    async def start_handler(message: Message):
        user_id = message.from_user.id

        # ❌ Obuna tekshiruvi
        if not await is_user_subscribed(bot, user_id):
            await message.answer(
                "❗ Botdan foydalanish uchun kanalimizga obuna bo‘lishingiz shart.",
                reply_markup=subscribe_keyboard()
            )
            return

        # 🎁 Free try (DB-based)
        if not await has_used_free(user_id):
            await grant_free_balance(user_id)
            await message.answer(
                "Assalomu alaykum! Bot ishga tushdi.\n\n"
                "🎁 Sizga 1 marta tekin esse tekshirish imkoni berildi.",
                reply_markup=main_menu()
            )
        else:
            await message.answer(
                "Assalomu alaykum! Bot ishga tushdi.\n\n"
                "ℹ️ Siz tekin imkoniyatdan avval foydalanib bo‘lgansiz.",
                reply_markup=main_menu()
            )

    # ✅ Routerlar
    dp.include_router(subscription.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    dp.include_router(help.router)
    dp.include_router(essay.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
