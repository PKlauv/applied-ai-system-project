# Model Card — Game Glitch Investigator Agent

**Model used:** Llama 3.3 70B Versatile (via Groq's hosted inference API)
**Task:** Agentic Python bug investigation and repair — given a `.py` file, plan hypotheses, identify bugs with confidence scores, generate a corrected file, and validate it with `pytest` in a sandbox.
**Surfaces:** Streamlit UI (`app.py`) and CLI (`cli.py`), both built on the same `investigate()` generator in `agent/core.py`.
**Date:** April 2026
**Author:** Per Lauvstad — CodePath AI 110, Module 1 → Final extension.

---

## Intended Use

The agent is intended as a **debugging assistant for small, single-file Python programs** — specifically the kind of beginner-friendly Streamlit and game-logic code that the original Module 1 project featured. Typical inputs are 50-300 line files with logic bugs, off-by-one errors, type confusion, or incorrect Streamlit state handling. The output is a structured report with per-bug severity, confidence, line numbers, and a one-or-two-sentence explanation, plus a sandboxed corrected version of the file.

It is **not** intended as a replacement for human code review on production code, a security auditor, or a general-purpose code repair tool for large multi-file projects.

---

## Limitations and Biases

- **Streamlit-specific blindness:** The agent reasons about code statically. Streamlit bugs that only manifest at runtime (e.g., `session_state` resetting on rerun) require it to simulate execution order without running the app. It handles simple cases well but misses interactions between multiple widgets.
- **Short-context files only:** Files over 100 KB are blocked by the guardrail. Very long modules with bugs spread across many functions can dilute the analysis step's attention.
- **Training data recency:** Llama 3.3's knowledge of Streamlit APIs may lag the latest version. If a bug involves a recently deprecated function, the agent may suggest an equally deprecated fix.
- **Over-reporting:** The agent occasionally flags style issues (missing docstrings, missing input validation) as bugs at 0.85+ confidence. This inflates bug counts without adding value and reduces precision on otherwise clean helper functions.
- **Language bias:** All prompts are in English. Non-English variable names or comments may reduce analysis quality.
- **Free-tier token cap:** The Groq free tier allows 100k tokens/day. Expect rate-limit errors after ~10-15 fixture runs in a single day. The UI and CLI both catch this and display a "come back in X minutes" message rather than crashing.
- **Confidence is self-reported:** The 0.0-1.0 confidence on each bug is the LLM's own claim, not a calibrated probability. Treat it as a relative ranking inside one report, not as a probability of correctness.

---

## Misuse Risk and Mitigation

- **Running arbitrary code:** The agent writes user-provided Python to a temp directory and runs `pytest` against it. The guardrail enforces `.py`-only and 100 KB max; `subprocess.run` enforces a 5-second timeout. It does **not** sandbox network access, filesystem writes outside the temp dir, or imports of system packages. Do not run the agent on untrusted code from unknown sources without an additional sandboxing layer (Docker, Firejail, etc.).
- **False confidence:** A high confidence score (0.9+) reflects the LLM's self-reported certainty, not ground-truth accuracy. A user who treats confidence as a guarantee may apply a wrong fix without reviewing the diff. The UI deliberately shows the corrected code as a read-only block — users must copy/paste it themselves, never an automatic write.
- **Original file is never modified:** All fix attempts go to a `tempfile.mkdtemp()` sandbox, which is `shutil.rmtree`'d at the end of the run regardless of outcome. The user's source file stays untouched.

---

## Surprises During Reliability Testing

The eval harness (`python -m eval.harness`) runs the agent against four hand-crafted fixtures derived from the original Module 1 bugs and scores precision/recall against expected keywords. Final results: **4/4 pass, average confidence 0.95, every fixture solved in 1 iteration.** Three things genuinely surprised me on the way to that number:

**1. The iteration loop never actually iterated.** My first end-to-end run resolved every fixture in exactly 3 iterations — the maximum. I assumed the agent was doing real reflective work. It wasn't. The fixture files have no `test_*` functions, so `pytest` was exiting with code 5 ("no tests collected"), which my `run_pytest` wrapper was treating as a failure. The agent was burning all three iterations on empty reflection cycles, then reporting whatever it found in the analyze step. Adding a behavioral `test_buggy.py` to each fixture and treating exit-5 as "no signal, stop" fixed this: every fixture now resolves in 1 iteration when the smoke tests pass. **Lesson:** an agent loop without a real test signal is just the same prompt three times in a row. Verify your verification.

**2. Groq returns 400 errors on triple-quoted docstrings inside the JSON `fixed_code` field.** The model would generate a perfectly correct Python fix, but inside its own JSON envelope it would emit `"""docstrings"""` — which breaks JSON encoding at the Groq API level *before* my parsing code ever sees it. Fixture 03 (off-by-one) crashed every run for this reason. The fix was a one-line addition to the FIX_PROMPT instructing the model to use `#` comments instead of `"""` strings inside `fixed_code`. A more robust solution would be to base64-encode the code field, but the prompt instruction has held in every run since.

**3. Scoring fragility, not model fragility, was the real problem.** My initial expected-bug keyword lists had 4 synonyms each (e.g., `["inverted", "swapped", "higher", "lower"]`). The agent correctly identified the inverted-comparison bug with the label `"inverted comparison in check_guess"` — matching only 1 of 4 keywords, scoring 25% recall, and failing the fixture. The bug wasn't in the agent. Trimming each fixture's keyword list to 2 representative terms gave a much fairer signal of whether the agent had identified the *concept*, not whether it had used my exact synonyms.

---

## AI Collaboration

**Helpful instance.** When designing the plan/analyze/fix/reflect loop, Claude suggested splitting the "analyze" step (identify bugs) from the "fix" step (generate corrected code) into two separate prompts rather than asking the model to do both at once. I initially thought this was over-engineering — one round-trip is faster and cheaper than two. But the combined version produced muddy bug labels because the model was reasoning about the fix and the diagnosis simultaneously, and the eval harness depends on clean labels for keyword matching. Splitting them gave cleaner structured output and made the iteration loop possible (you can re-`fix` after a test failure without re-doing the analysis).

**Flawed instance.** Claude initially recommended using a streaming token-by-token display in the Streamlit UI for the agent's live progress. The reasoning was that `google-generativeai` had a streaming API and Streamlit could render partial output. In practice, Streamlit's execution model re-runs the entire script on every interaction, and combining that with an asynchronous token stream requires either threading or `st.empty()` placeholders that fight the rerun cycle — way more complexity than the project warranted. The simpler approach that actually shipped: `investigate()` is a generator that yields step dicts (`{"step": "plan", "message": "..."}`), and the UI displays each one inside an `st.status` panel as `next(gen)` returns. Same visible-decision-chain effect, none of the threading.

---

## Reflection: What This Project Taught Me

The biggest lesson from this project is that **the AI is the easy part**. Picking a model, writing prompts, parsing JSON — that work was largely done in an afternoon. What ate the actual time was everything around the model: getting consistent JSON when the model decides to wrap output in markdown fences, handling 400 errors when the model emits triple quotes inside a JSON string, building a sandbox that pytest can run inside without leaking state, designing an eval harness fair enough that a paraphrased correct answer doesn't fail, and showing the user what the agent is doing without making them stare at a frozen screen.

The eval harness in particular shifted how I think about LLM systems. Before this project I would have called the agent "working" after a few successful manual runs in the UI. Running it against four deterministic fixtures and watching three of them fail on the first try — for three completely different reasons — was a different kind of feedback. The harness told me my iteration loop was broken (lesson 1 above), my JSON encoding was fragile (lesson 2), and my scoring was unfair to the agent (lesson 3). None of those would have shown up in a demo. I'd ship a "working" agent that quietly burned 3× the API budget per run and failed on any code with docstrings.

The other thing this project crystallized: **confidence scores are not accuracy scores.** The agent rates its own work at 0.90+ on bugs that are genuine, and at 0.90+ on style nitpicks that aren't bugs. Same number, different ground truth. I now read confidence as "how strongly the model wants to commit to this answer," not "how likely the answer is correct." That's a useful signal — but it's not the signal I assumed it was when I started.

If I extended this further, the next thing I'd add isn't a bigger model or fancier prompts. It's a precision-focused evaluation: a fixture set of *correct* code where the right answer is "no bugs found." Right now the harness only measures whether the agent finds real bugs; it doesn't measure how often it invents fake ones. That's the next reliability gap, and it's the one most likely to bite a real user.
