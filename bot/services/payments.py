# bot/services/payments.py

from typing import Optional, Literal, Dict, Any

from bot.services.db import require_pool
from bot.services.balance import ensure_user


ReceiptKind = Literal["photo", "document"]
PaymentStatus = Literal["pending", "approved", "rejected"]


async def create_payment(
    *,
    payment_id: str,
    user_id: int,
    username: str | None,
    receipt_kind: ReceiptKind,
    receipt_file_id: str,
    amount: int = 1,
) -> None:
    """
    Create new payment request with status = pending
    """
    pool = require_pool()
    await ensure_user(user_id)

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO payments (
                payment_id,
                user_id,
                amount,
                status,
                username,
                receipt_kind,
                receipt_file_id
            )
            VALUES (
                $1,
                $2,
                $3,
                'pending',
                $4,
                $5::receipt_kind,
                $6
            )
            """,
            payment_id,
            user_id,
            amount,
            username,
            receipt_kind,
            receipt_file_id,
        )


async def decide_payment(
    *,
    payment_id: str,
    decided_by: int,
    approve: bool,
) -> Optional[Dict[str, Any]]:
    """
    Approve / Reject payment (ADMIN ONLY)

    Idempotent:
    - payment yo‘q -> None
    - allaqachon decided -> None
    """
    pool = require_pool()
    new_status: PaymentStatus = "approved" if approve else "rejected"

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT *
                FROM payments
                WHERE payment_id = $1
                FOR UPDATE
                """,
                payment_id,
            )

            if not row:
                return None

            if row["status"] != "pending":
                return None

            await conn.execute(
                """
                UPDATE payments
                SET status = $2::payment_status,
                    decided_at = now(),
                    decided_by = $3
                WHERE payment_id = $1
                """,
                payment_id,
                new_status,
                decided_by,
            )

            return dict(row)
