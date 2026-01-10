# bot/handlers/subscription.py

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.services.subscription import is_user_subscribed
from bot.services.balance import grant_free_balance, has_used_free
from bot.keyboards.main import main_menu

router = Router()


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot = callback.bot

    # ❌ Obuna yo‘q
    if not await is_user_subscribed(bot, user_id):
        await callback.answer(
            "❌ Siz hali kanalga obuna bo‘lmagansiz.",
            show_alert=True
        )
        return

    # ✅ Obuna bor
    already_used = await has_used_free(user_id)

    if not already_used:
        # 🎁 DB-based ONE TIME ONLY
        await grant_free_balance(user_id)

        await callback.message.edit_text(
            "✅ Obuna tasdiqlandi.\n\n"
            "🎁 Sizga 1 marta tekin esse tekshirish imkoni berildi.",
            reply_markup=None
        )
    else:
        await callback.message.edit_text(
            "✅ Obuna tasdiqlandi.\n\n"
            "ℹ️ Siz tekin imkoniyatdan avval foydalanib bo‘lgansiz.",
            reply_markup=None
        )

    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=main_menu()
    )
