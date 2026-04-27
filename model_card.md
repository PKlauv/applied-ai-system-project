# Model Card — Game Glitch Investigator Agent

**Model used:** Gemini 2.5 Pro (via `google-generativeai`)
**Task:** Agentic Python bug investigation and repair
**Date:** April 2026

---

## Limitations and Biases

- **Streamlit-specific blindness:** The agent analyzes code statically. Streamlit bugs that only manifest at runtime (e.g., session state resetting on rerun) require the agent to reason about execution order without running the app. It handles these well for simple cases but can miss interactions between multiple widgets.
- **Short-context files only:** Files over 100KB are blocked by the guardrail. Very long modules with bugs spread across many functions may confuse the analysis step.
- **Training data recency:** Gemini's knowledge of Streamlit APIs may lag behind the latest version. If a bug involves a recently deprecated function, the agent may suggest a fix that uses an equally deprecated pattern.
- **Over-reporting:** In testing, the agent occasionally flags style issues (variable naming, missing docstrings) as bugs when no guardrail keyword filters these out. This inflates bug counts without adding value.
- **Language bias:** All prompts are in English. Non-English variable names or comments may reduce analysis quality.

---

## Misuse Risk and Mitigation

- **Running arbitrary code:** The agent writes and runs user-provided Python in a subprocess. The guardrail enforces `.py`-only, 100KB limit, and a 5-second timeout. It does **not** sandbox network access or filesystem writes — do not run the agent on untrusted code from unknown sources without an additional sandboxing layer (e.g., Docker).
- **False confidence:** A high confidence score (0.9+) reflects the LLM's self-reported certainty, not ground-truth accuracy. A user who treats confidence as a guarantee may skip reviewing the agent's output before applying fixes.
- **Mitigation in place:** All fixes are written to a temp sandbox copy — the original file is never modified. Users must manually apply fixes.

---

## Surprises During Reliability Testing

> **Fill this in after running `python -m eval.harness`** — describe what surprised you.

*Example (replace with real results):*
> Fixture 03 (off-by-one) was harder than expected. The agent correctly identified the `Hard` difficulty range bug (1-50 vs. 1-200) on every run, but only caught the `>` vs `>=` boundary error about 60% of the time. It seems the LLM treats boundary-condition bugs as lower-salience than obviously misnamed variables. Adding an explicit hypothesis about loop/condition boundaries in the plan prompt might improve recall here.

---

## AI Collaboration

**Helpful instance:** When designing the plan/analyze/fix/reflect loop, Claude suggested separating the "analyze" step (identify bugs) from the "fix" step (generate corrected code), rather than doing both in one prompt. This turned out to be important: a combined prompt produced less precise bug labels (which the eval harness depends on), while splitting the steps gave cleaner structured output.

**Flawed instance:** Claude initially suggested using `google-generativeai`'s streaming API for the Streamlit UI, estimating it would allow real-time token-by-token display. In practice, Streamlit's execution model re-runs the entire script on each interaction, making streaming difficult to implement without complex threading. The simpler generator-based approach (yielding step dicts from `investigate()`) worked much better for this use case.

---

## Reflection: What This Project Taught Me

<!-- Personalize this section in your own words before submitting -->

Working on this system showed me that the hardest part of building an AI agent isn't the AI — it's the scaffolding. Getting consistent structured output from an LLM, handling parse failures gracefully, isolating code execution safely, and designing an eval harness that is fair but not trivially easy all took more thought than the prompt engineering itself. I came away with a clearer picture of why reliability testing is not optional for production AI systems: the agent's behavior on my four test fixtures told me things about its failure modes that no amount of manual spot-checking would have revealed.
