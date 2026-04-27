"""Fixture 04: Secret is cast to string on even attempts, breaking comparison (original bug #2)."""
import random


class GuessingGame:
    def __init__(self):
        self.secret = random.randint(1, 100)
        self.attempts = 0

    def submit_guess(self, raw_guess: str) -> str:
        self.attempts += 1
        # BUG: on even attempts the secret is converted to a string so integer
        # comparison always fails, making the game unwinnable every other turn.
        if self.attempts % 2 == 0:
            self.secret = str(self.secret)

        try:
            guess = int(raw_guess)
        except ValueError:
            return "Invalid input"

        if guess == self.secret:
            return "Win"
        elif guess < self.secret:
            return "Too Low"
        else:
            return "Too High"
