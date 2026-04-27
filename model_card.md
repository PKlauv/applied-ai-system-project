# Model Card — Game Glitch Investigator Agent

**Model used:** Llama 3.3 70B Versatile (via Groq's hosted inference API)
**Task:** Agentic Python bug investigation and repair
**Date:** April 2026

---

## Limitations and Biases

- **Streamlit-specific blindness:** The agent analyzes code statically. Streamlit bugs that only manifest at runtime (e.g., session state resetting on rerun) require the agent to reason about execution order without running the app. It handles these well for simple cases but can miss interactions between multiple widgets.
- **Short-context files only:** Files over 100KB are blocked by the guardrail. Very long modules with bugs spread across many functions may confuse the analysis step.
- **Training data recency:** Llama 3.3's knowledge of Streamlit APIs may lag behind the latest version. If a bug involves a recently deprecated function, the agent may suggest a fix that uses an equally deprecated pattern.
- **Over-reporting:** In testing, the agent occasionally flags style issues (variable naming, missing docstrings) as bugs when no guardrail keyword filters these out. This inflates bug counts without adding value.
- **Language bias:** All prompts are in English. Non-English variable names or comments may reduce analysis quality.

---

## Misuse Risk and Mitigation

- **Running arbitrary code:** The agent writes and runs user-provided Python in a subprocess. The guardrail enforces `.py`-only, 100KB limit, and a 5-second timeout. It does **not** sandbox network access or filesystem writes — do not run the agent on untrusted code from unknown sources without an additional sandboxing layer (e.g., Docker).
- **False confidence:** A high confidence score (0.9+) reflects the LLM's self-reported certainty, not ground-truth accuracy. A user who treats confidence as a guarantee may skip reviewing the agent's output before applying fixes.
- **Mitigation in place:** All fixes are written to a temp sandbox copy — the original file is never modified. Users must manually apply fixes.

---

## Surprises During Reliability Testing

**Harness results (Groq llama-3.3-70b-versatile, 4/4 pass, avg confidence 0.95):**

**The iteration loop never actually iterated.** Every fixture resolved in exactly 1 iteration. Without real pytest tests bundled into the sandbox, pytest exited with "no tests collected" (exit code 5), which was incorrectly treated as a test failure — burning all 3 iterations on empty reflection cycles. Adding behavioral smoke tests (`test_buggy.py`) to each fixture and treating exit-5 as "no signal" fixed this: the loop now exits after 1 iteration when tests pass.

**Groq fails to produce valid JSON when fixed code contains triple-quoted docstrings.** The `fixed_code` field is a JSON string, but the model adds `"""docstrings"""` to the Python it generates — which breaks JSON encoding at the Groq API level before we even parse it. A prompt instruction to avoid triple quotes in the output largely resolves this, though a more robust fix would be to base64-encode the fixed code.

**The agent over-reports.** On clean helper functions (e.g., `update_score` in fixture 02), the agent flagged missing input validation as "bugs" at 0.90 confidence. These are style/defensive-coding issues, not bugs, which reduces precision without adding value. The fix prompt's "do not add features" instruction partially suppresses this but doesn't eliminate it.

---

## AI Collaboration

**Helpful instance:** When designing the plan/analyze/fix/reflect loop, Claude suggested separating the "analyze" step (identify bugs) from the "fix" step (generate corrected code), rather than doing both in one prompt. This turned out to be important: a combined prompt produced less precise bug labels (which the eval harness depends on), while splitting the steps gave cleaner structured output.

**Flawed instance:** Claude initially suggested using `google-generativeai`'s streaming API for the Streamlit UI, estimating it would allow real-time token-by-token display. In practice, Streamlit's execution model re-runs the entire script on each interaction, making streaming difficult to implement without complex threading. The simpler generator-based approach (yielding step dicts from `investigate()`) worked much better for this use case.

---

## Reflection: What This Project Taught Me

<!-- Personalize this section in your own words before submitting -->

Working on this system showed me that the hardest part of building an AI agent isn't the AI — it's the scaffolding. Getting consistent structured output from an LLM, handling parse failures gracefully, isolating code execution safely, and designing an eval harness that is fair but not trivially easy all took more thought than the prompt engineering itself. I came away with a clearer picture of why reliability testing is not optional for production AI systems: the agent's behavior on my four test fixtures told me things about its failure modes that no amount of manual spot-checking would have revealed.
