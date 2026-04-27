"""Fixture 01: Secret number resets on every button click (original bug #1 & #10)."""
import random
import streamlit as st

# BUG: secret is not stored in session_state — it regenerates on every rerun,
# so the player can never win because the target keeps changing.
secret = random.randint(1, 100)

guess = st.text_input("Guess a number (1-100):")
if st.button("Submit"):
    try:
        g = int(guess)
        if g == secret:
            st.success("You win!")
        elif g < secret:
            st.info("Go higher!")
        else:
            st.info("Go lower!")
    except ValueError:
        st.error("Enter a valid number.")
