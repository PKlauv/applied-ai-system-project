"""Fixture 02: check_guess returns inverted hints (original bug #1)."""


def check_guess(guess: int, secret: int) -> tuple[str, str]:
    if guess == secret:
        return "Win", "Correct!"
    # BUG: hints are backwards — higher/lower labels are swapped
    if guess > secret:
        return "Too Low", "Go HIGHER!"
    else:
        return "Too High", "Go LOWER!"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    if outcome == "Win":
        points = max(10, 100 - 10 * attempt_number)
        return current_score + points
    return current_score - 5
