# oddiy in-memory lock
active_checks: set[int] = set()


def is_locked(user_id: int) -> bool:
    return user_id in active_checks


def lock(user_id: int):
    active_checks.add(user_id)


def unlock(user_id: int):
    active_checks.discard(user_id)
