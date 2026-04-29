# 🕵️ Game Glitch Investigator — Applied AI System

> An AI agent that investigates, diagnoses, and fixes bugs in Python code — extended from a CodePath Module 1 debugging project.

---

## Demo Walkthrough

**Loom video:** [Watch the short walkthrough](https://www.loom.com/share/4b30f16ce598499f88ecfa258a453114) — end-to-end run, agent loop, guardrail, and eval harness.

**Screenshot tour:** [docs/walkthrough.md](docs/walkthrough.md) — covers the Streamlit UI, CLI, guardrail behavior, and the eval harness summary.

---

## Original Project

**Base project:** [Game Glitch Investigator — Module 1 Starter](https://github.com/PKlauv/ai110-module1show-gameglitchinvestigator-starter)

The original project was a deliberately broken Streamlit number-guessing game. Students were challenged to identify and fix 10 AI-generated bugs spanning Streamlit state management, inverted logic, type coercion, and off-by-one errors. It demonstrated how AI-generated code can introduce subtle, hard-to-spot defects.

This final project converts the original's *theme* into a working tool: rather than asking a human to investigate glitches manually, an AI agent does it automatically.

---

## What This System Does

Upload any `.py` file and the **Game Glitch Investigator Agent** will:

1. **Plan** — form hypotheses about what might be broken
2. **Analyze** — identify specific bugs with severity and confidence scores
3. **Fix** — generate a corrected version of the code
4. **Test** — run `pytest` in an isolated sandbox
5. **Reflect** — if tests fail, revise and retry (up to 3 iterations)

You get a structured bug report with per-bug confidence, a corrected file, and a full decision-chain trace.

---

## Architecture Overview

![System Architecture](assets/architecture.png)


The system has three layers:

- **Surfaces** (`app.py`, `cli.py`) — accept user input and display results. Both call the same agent core.
- **Agent Core** (`agent/core.py`) — orchestrates the plan → analyze → fix → test → reflect loop using Llama 3.3 70B via Groq. Emits live step events for the UI to stream.
- **Tools** (`agent/tools.py`) — file I/O and `pytest` subprocess execution inside a temp sandbox. Every call is logged to a JSONL trace file.
- **Eval Harness** (`eval/harness.py`) — runs the agent on 4 hand-crafted buggy fixtures (derived from the original Module 1 bugs) and scores precision, recall, and avg confidence.

---

## Setup

### Prerequisites

- Python 3.12+
- A free [Groq API key](https://console.groq.com/keys) (no credit card required)

### Installation

```bash
git clone https://github.com/PKlauv/applied-ai-system-project.git
cd applied-ai-system-project
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure API key

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your_key_here
```

### Run the Streamlit UI

```bash
streamlit run app.py
```

### Run via CLI

```bash
python -m cli eval/fixtures/02_inverted_hints/buggy.py
python -m cli path/to/your_file.py --max-iters 2 --json
```

### Run the eval harness

```bash
python -m eval.harness
```

### Run unit tests

```bash
pytest tests/ -q
```

---

## Sample Interactions

### Example 1 — Inverted hints (`02_inverted_hints`)

**Input:** `eval/fixtures/02_inverted_hints/buggy.py` — `check_guess` returns "Go HIGHER!" when the guess is too high.

**Agent output (real run):**
```
🔍  [PLAN] Reading code and forming investigation plan...
📋  [PLAN_RESULT] Found 1 hypothesis(es). Starting analysis.
🧪  [ANALYZE] Analyzing code against hypotheses...
🐛  [ANALYZE_RESULT] Identified 3 bug(s).
🔧  [FIX] Iteration 1: generating fix...
⚗️  [TEST] Iteration 1: running tests...
📊  [TEST_RESULT] Iteration 1: tests passed.
🏁  [DONE] Investigation complete. 3 bug(s) found, avg confidence 0.93.

  1. [MEDIUM] inverted comparison in check_guess (line 6, conf=1.00)
     The function check_guess returns incorrect hints due to swapped comparison
     operators. Returns 'Too Low' when guess > secret and 'Too High' when
     guess < secret — players are always sent in the wrong direction.
```

### Example 2 — Type confusion (`04_type_confusion`)

**Input:** `eval/fixtures/04_type_confusion/buggy.py` — secret cast to `str` on even attempts.

**Agent output (abridged):**
```
  1. [HIGH] type confusion due to str() conversion on even attempts (line 15, conf=0.95)
     self.secret = str(self.secret) converts the integer secret to a string on
     every even-numbered attempt. The subsequent integer comparison always fails,
     making the game unwinnable every other turn.
```

### Example 3 — Guardrail triggered

**Input:** `README.md` (not a `.py` file)

```bash
$ python -m cli README.md
GUARDRAIL: Only .py files are supported (got: README.md)
```

---

## Design Decisions

| Decision | Choice | Trade-off |
|---|---|---|
| LLM | Llama 3.3 70B via Groq | Free hosted inference, low latency, capable of structured JSON output. Trade-off: not as strong as frontier closed models on subtle reasoning. |
| Fix loop | Max 3 iterations | Balances quality vs. latency; most bugs resolve in 1-2 iters |
| Sandbox | `tempfile` + subprocess | Safe; no `eval`/`exec`; small overhead per run |
| Scoring | Fuzzy keyword recall | Tolerant of paraphrase; misses highly paraphrased bugs |
| UI | Streamlit | Matches original project stack; live streaming via generator |
| JSON output | Structured schema from prompt | Brittle to model drift; 2-retry parse fallback mitigates |
| Bug analysis prompt | Few-shot (3 worked examples) | ~300 extra tokens per run; anchors the model on logic bugs only, reducing style false-positives. Toggle off via `FEWSHOT=0` for baseline. See `docs/fewshot_comparison.md`. |

---

## Testing Summary

**Unit tests:** 39 tests across guardrails, logger, tools, and harness scoring — all pass.

**Eval harness** (Groq `llama-3.3-70b-versatile`, 4/4 fixtures, avg confidence 0.95):

| Fixture | Pass | Recall | Confidence | Iters |
|---|---|---|---|---|
| 01_state_reset | YES | 0.50 | 0.93 | 1 |
| 02_inverted_hints | YES | 1.00 | 0.95 | 1 |
| 03_off_by_one | YES | 0.50 | 1.00 | 1 |
| 04_type_confusion | YES | 0.50 | 0.93 | 1 |

**Reliability findings:** The agent consistently finds the primary bug in each fixture (4/4 pass) but over-reports style issues alongside real bugs, reducing precision to ~0.33-0.50. The `ANALYZE_PROMPT` uses 3 worked few-shot examples (inverted comparison, off-by-one, type confusion) to anchor the model on logic bugs only and suppress style false-positives — see `docs/fewshot_comparison.md` for the baseline vs. few-shot breakdown. Fixture 03's off-by-one boundary error is caught but confidence is 1.00, highlighting that confidence reflects self-certainty not ground-truth accuracy. The Groq model fails to produce valid JSON when fixed code contains triple-quoted docstrings — the try/except fallback prevents harness crashes but means the corrected code isn't written on those iterations.

---

## Reflection

Building this system made the gap between "AI that generates code" and "AI that reasons about code" very concrete. The agent loop — planning hypotheses, then testing them against real pytest output — forces a kind of empirical discipline that single-shot prompting lacks. The hardest part was getting consistent structured JSON output from the LLM; the retry-on-parse-error fallback turned out to be essential, not optional.

---

## Repository Structure

```
├── agent/
│   ├── core.py          # Orchestration loop
│   ├── guardrails.py    # Input validation
│   ├── llm.py           # Groq LLM wrapper
│   ├── logger.py        # JSONL run logger
│   ├── prompts.py       # Prompt templates
│   ├── schema.py        # Dataclasses
│   └── tools.py         # File I/O + pytest runner
├── eval/
│   ├── harness.py       # Evaluation script
│   └── fixtures/        # 4 buggy Python files + expected_bugs.json
├── tests/               # Unit tests (no LLM calls)
├── assets/              # Architecture diagram
├── runs/                # Agent trace files (gitignored)
├── app.py               # Streamlit UI
├── cli.py               # CLI entry point
├── logic_utils.py       # Original Module 1 helper (kept for reference)
├── reflection.md        # Original Module 1 reflection (historical)
├── model_card.md        # AI system reflection (this project)
├── .env.example         # API key template
└── requirements.txt
```
