# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start
  (for example: "the hints were backwards").

When I first ran the game, it looked like a normal Streamlit number guessing app, but it was essentially unwinnable. The most obvious bug was that the hints were backwards — when my guess was too high, the game told me to "Go HIGHER!" instead of "Go LOWER!", which sent me in the wrong direction every time. The second major bug was that the secret number's type changed on even-numbered attempts: the code converted it to a string, which broke the integer comparison and made it impossible to match your guess to the secret even if you typed the right number. I also noticed the scoring was inconsistent — guessing too high on an even attempt actually gave you +5 points instead of deducting, while guessing too low always deducted 5. Finally, the Hard difficulty had a range of only 1-50, which was actually easier than Normal mode's 1-100 range.

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).

I used Claude Code (Anthropic's CLI tool) to help analyze the codebase and identify bugs. One correct suggestion was that the hint messages in `check_guess` needed to be swapped — when `guess > secret`, the message should say "Go LOWER!" not "Go HIGHER!". I verified this by running the fixed game and confirming the hints now pointed me toward the correct number. One initially misleading suggestion was that the `TypeError` catch block in `check_guess` was necessary for handling edge cases — but in reality, the whole block only existed because of the bug that converted the secret to a string on even attempts. Once I removed that type-conversion bug, the `TypeError` handling became unnecessary dead code. I verified this by removing both the type-conversion block and the `TypeError` catch, then running all tests and the game to confirm everything still worked correctly.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

I decided a bug was fixed by running both automated tests with pytest and manually playing the game in the browser. For automated testing, I ran `pytest tests/test_game_logic.py -v` which tested `check_guess`, `parse_guess`, `update_score`, and `get_range_for_difficulty`. The `test_update_score_symmetry` test was particularly important — it confirmed that "Too High" and "Too Low" both deduct the same number of points, catching the asymmetric scoring bug. I also manually tested by running the Streamlit app, opening the Developer Debug Info panel to see the secret number, and verifying that hints pointed in the correct direction and that I could actually win. Claude helped me think through edge cases for the tests, like testing `parse_guess` with decimal input ("3.7"), empty strings, and None values.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

Streamlit works differently from typical web apps — every time you interact with a widget (click a button, type in a box), the entire Python script runs again from top to bottom. This means any regular variable you define will reset to its initial value on every interaction. To keep data alive across these reruns, Streamlit provides `st.session_state`, which is like a persistent dictionary that survives reruns. For example, we store the secret number in `st.session_state.secret` so it doesn't get regenerated every time the user submits a guess. Without session state, the game would be truly impossible because the secret would change on every single button click.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.

One habit I want to carry forward is separating logic from UI code into utility modules and writing tests for the logic independently. This made it much easier to verify each function worked correctly without needing to run the full Streamlit app. Next time I work with AI on a coding task, I would run the code immediately and test it myself before trusting it — this project showed that AI can produce code that looks reasonable but contains subtle bugs that only surface at runtime. This project really reinforced that AI-generated code needs the same level of scrutiny as any other code: just because it runs without syntax errors doesn't mean it's correct, and automated tests are essential for catching logic bugs that are easy to miss by eye.
