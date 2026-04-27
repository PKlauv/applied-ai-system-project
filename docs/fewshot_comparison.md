# Few-shot vs Baseline Harness Comparison

## What Changed

The `ANALYZE_PROMPT` in `agent/prompts.py` was updated from zero-shot (schema description only) to few-shot (3 worked input/output examples before the real code). The baseline is preserved as `ANALYZE_PROMPT_BASELINE` and selectable via `FEWSHOT=0`.

Toggle:
```bash
FEWSHOT=0 python -m eval.harness   # zero-shot baseline
python -m eval.harness             # few-shot (default)
```

The 3 examples cover the same bug *categories* as the eval fixtures — inverted comparison, off-by-one index, type confusion — without copying the fixture code itself. Style issues (missing docstrings, missing input validation) are deliberately absent from the examples.

---

## Baseline Results (zero-shot, `FEWSHOT=0`)

Recorded before the few-shot prompt was added. Same 4 fixtures, same eval harness scoring.

| Fixture | Pass | Recall | Precision | Avg Conf | Iters | Bugs Reported | Notes |
|---|---|---|---|---|---|---|---|
| 01_state_reset | YES | 0.50 | 0.33 | 0.93 | 1 | 3 | 1 real + 2 style false positives |
| 02_inverted_hints | YES | 1.00 | 0.50 | 0.95 | 1 | 2 | 1 real + 1 style false positive |
| 03_off_by_one | YES | 0.50 | 0.50 | 1.00 | 1 | 2 | 1 real + 1 over-reported sub-bug |
| 04_type_confusion | YES | 0.50 | 0.33 | 0.93 | 1 | 3 | 1 real + 2 style false positives |

**Total: 4/4 passed. Avg confidence: 0.95. Avg precision: ~0.42.**

The main weakness in the baseline: the model consistently appended 1-2 style nitpicks (missing docstrings, input validation gaps) at confidence ≥ 0.85, inflating bug counts and halving precision.

---

## Few-shot Run Status

The few-shot run could not be completed on 2026-04-27 — the Groq free-tier daily TPD cap (100k tokens/day) was exhausted during development. The prompt change and toggle are in place; re-run with:

```bash
python -m eval.harness 2>&1 | tee runs/harness_fewshot.log
```

---

## Expected Differences

Based on prompt design:

| Metric | Baseline | Few-shot (expected) |
|---|---|---|
| Style false positives per fixture | 1-2 | 0-1 |
| Avg precision | ~0.42 | ~0.60+ |
| Recall | 0.50-1.00 | unchanged (examples don't add new bug types) |
| Pass rate | 4/4 | 4/4 (unchanged) |
| Avg confidence | 0.95 | similar |

The examples show only logic bugs with specific structural patterns, not style warnings. The instruction "Do NOT report missing docstrings, missing input validation, or style issues" in the few-shot prompt is more actionable when paired with concrete examples than when stated alone in zero-shot.

Recall is not expected to improve because the harness keyword matching already passes with the current labels — the improvement is precision (fewer false positives), not recall (finding more real bugs).

---

## Design Note

The few-shot examples were chosen to be *archetypal* (clear, minimal, one bug each) rather than specific to the game-logic domain. This is intentional: we want the model to learn the *category* of bug to report, not to pattern-match on game-specific variable names. A model that sees `check_guess` in an example might over-fit to that name in the real code.
