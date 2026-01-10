# bot/services/balance.py
from bot.services.db import require_pool


async def ensure_user(user_id: int) -> None:
    pool = require_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )


async def get_balance(user_id: int) -> int:
    pool = require_pool()
    await ensure_user(user_id)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT balance FROM balances WHERE user_id = $1",
            user_id,
        )
        return int(row["balance"]) if row else 0


async def add_balance(user_id: int, amount: int = 1) -> None:
    pool = require_pool()
    await ensure_user(user_id)

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO balances (user_id, balance)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET
                balance = balances.balance + EXCLUDED.balance,
                updated_at = now()
            """,
            user_id,
            amount,
        )


async def has_used_free(user_id: int) -> bool:
    pool = require_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM free_tries WHERE user_id = $1",
            user_id,
        )
        return row is not None


async def grant_free_balance(user_id: int) -> None:
    """
    1 MARTA (FOREVER).
    - free_tries ga yozadi
    - balansga +1 qiladi
    """
    pool = require_pool()
    await ensure_user(user_id)

    async with pool.acquire() as conn:
        async with conn.transaction():
            used = await conn.fetchrow(
                "SELECT 1 FROM free_tries WHERE user_id = $1",
                user_id,
            )
            if used:
                return

            await conn.execute(
                "INSERT INTO free_tries (user_id) VALUES ($1)",
                user_id,
            )

            await conn.execute(
                """
                INSERT INTO balances (user_id, balance)
                VALUES ($1, 1)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    balance = balances.balance + 1,
                    updated_at = now()
                """,
                user_id,
            )


async def consume_balance(user_id: int) -> bool:
    """
    Atomic: balans >=1 bo‘lsa -1 qiladi, bo‘lmasa False.
    """
    pool = require_pool()
    await ensure_user(user_id)

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT balance FROM balances WHERE user_id = $1 FOR UPDATE",
                user_id,
            )
            if not row or int(row["balance"]) < 1:
                return False

            await conn.execute(
                """
                UPDATE balances
                SET balance = balance - 1,
                    updated_at = now()
                WHERE user_id = $1
                """,
                user_id,
            )
            return True


async def refund_balance(user_id: int, amount: int = 1) -> None:
    """
    OpenAI/texnik xato bo‘lsa balansni qaytarish.
    """
    await add_balance(user_id, amount)
