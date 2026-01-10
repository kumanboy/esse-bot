# bot/services/db.py
import os
from typing import Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL .env da topilmadi")


_pool: Optional[asyncpg.Pool] = None


async def init_db() -> None:
    """
    App start bo‘lganda 1 marta chaqiriladi.
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )


def require_pool() -> asyncpg.Pool:
    """
    Pool init bo‘lmagan bo‘lsa — aniq xato beradi (silent fail emas).
    """
    if _pool is None:
        raise RuntimeError("DB pool init qilinmagan. main.py da await init_db() bo‘lishi shart.")
    return _pool
