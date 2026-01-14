import os
from dotenv import load_dotenv

load_dotenv()

# ==============================
# Telegram bot configuration
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylda topilmadi!")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID .env faylda topilmadi!")
ADMIN_ID = int(ADMIN_ID)

CARD_INFO = (
    "💳 To‘lov uchun karta:\n"
    "9860 1606 3527 9575\n"
    "Ism: Khusan Davronov\n\n"
    "To‘lovdan so‘ng chekni file yoki screenshot qilib yuboring."
)

# ==============================
# OpenAI configuration
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY .env faylda topilmadi!")

MONEY_ID = int(os.getenv("MONEY_ID"))
if not MONEY_ID:
    raise RuntimeError("MONEY_ID .env faylda topilmadi!")

