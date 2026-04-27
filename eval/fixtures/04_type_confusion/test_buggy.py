from buggy import GuessingGame


def test_even_attempt_still_wins():
    game = GuessingGame()
    secret = game.secret
    game.attempts = 1  # next submit will be attempt #2 (even — bug triggers here)
    result = game.submit_guess(str(secret))
    assert result == "Win", (
        f"Correct guess on even attempt should win, got {result!r}"
    )
