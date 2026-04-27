"""Fixture 03: Off-by-one in attempt counting and range display (original bugs #3, #9)."""


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    # BUG: Hard range should be 1-200 (harder than Normal), not 1-50 (easier)
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def check_attempts(attempts: int, limit: int) -> bool:
    """Return True if the player has run out of attempts."""
    # BUG: off-by-one — should be attempts >= limit, not attempts > limit
    # This gives the player one extra free attempt beyond the limit.
    return attempts > limit
