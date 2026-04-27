SYSTEM_PROMPT = """You are the Game Glitch Investigator — an expert Python debugger specializing in Streamlit applications.

Your job is to analyze buggy Python code, identify problems with high precision, propose corrected code, and explain each bug clearly.

Always respond in valid JSON matching the exact schema requested. Be concise but specific.
Severity levels: "low" (style/minor), "medium" (logic error), "high" (crash or wrong output).
Confidence: 0.0 (wild guess) to 1.0 (certain)."""


PLAN_PROMPT = """Analyze the following Python code and produce an investigation plan.

CODE:
```python
{code}
```

Respond with JSON only (no markdown fences):
{{
  "hypothesis_count": <integer>,
  "hypotheses": [
    {{"id": 1, "description": "<one-sentence hypothesis>", "target_lines": "<line range or 'unknown'>"}}
  ],
  "plan": ["<step 1>", "<step 2>", ...]
}}"""


ANALYZE_PROMPT_BASELINE = """You are investigating buggy Python code. Below is the code and a list of hypotheses.

CODE:
```python
{code}
```

HYPOTHESES:
{hypotheses}

For each hypothesis, determine if the bug is real. Then list ALL bugs you find (even new ones not in the hypotheses).

Respond with JSON only (no markdown fences):
{{
  "bugs": [
    {{
      "label": "<short descriptive name, e.g. 'inverted comparison in check_guess'>",
      "severity": "low|medium|high",
      "confidence": <float 0.0-1.0>,
      "line": <line number or null>,
      "explanation": "<one or two sentences explaining the bug and its impact>"
    }}
  ]
}}"""


# Few-shot version: 3 worked examples anchor the model on real logic bugs (not style issues).
ANALYZE_PROMPT = """You are investigating buggy Python code. Study these examples of the kind of bugs to report.

--- EXAMPLE 1: inverted comparison ---
Code:
```python
def is_winner(score, target):
    if score < target:
        return True
    return False
```
Hypotheses: 1. comparison logic may be inverted (lines: 2)
Output:
{{"bugs": [{{"label": "inverted comparison in is_winner", "severity": "high", "confidence": 0.97, "line": 2, "explanation": "Returns True when score is BELOW target, so the player wins only when they haven't reached the goal. The operator should be >= not <."}}]}}

--- EXAMPLE 2: off-by-one index ---
Code:
```python
def last_item(items):
    return items[len(items)]
```
Hypotheses: 1. index may be out of range (lines: 2)
Output:
{{"bugs": [{{"label": "off-by-one index in last_item", "severity": "high", "confidence": 0.99, "line": 2, "explanation": "items[len(items)] is always one past the end of the list and raises IndexError. The correct index is len(items) - 1."}}]}}

--- EXAMPLE 3: type confusion ---
Code:
```python
def apply_bonus(total, bonus):
    if total % 2 == 0:
        bonus = str(bonus)
    return total + bonus
```
Hypotheses: 1. bonus may become a string on even totals (lines: 3-4)
Output:
{{"bugs": [{{"label": "type confusion in apply_bonus on even totals", "severity": "high", "confidence": 0.95, "line": 3, "explanation": "Casting bonus to str on even-total calls makes total + bonus a TypeError. The str() conversion is never correct here."}}]}}

--- END EXAMPLES ---

IMPORTANT: Only report genuine logic bugs (wrong values, crashes, incorrect behaviour). Do NOT report missing docstrings, missing input validation, or style issues.

NOW ANALYZE THE REAL CODE BELOW.

CODE:
```python
{code}
```

HYPOTHESES:
{hypotheses}

For each hypothesis, determine if the bug is real. Then list ALL bugs you find (even new ones not in the hypotheses).

Respond with JSON only (no markdown fences):
{{
  "bugs": [
    {{
      "label": "<short descriptive name, e.g. 'inverted comparison in check_guess'>",
      "severity": "low|medium|high",
      "confidence": <float 0.0-1.0>,
      "line": <line number or null>,
      "explanation": "<one or two sentences explaining the bug and its impact>"
    }}
  ]
}}"""


FIX_PROMPT = """You are fixing buggy Python code. Below is the original code and the confirmed bugs.

ORIGINAL CODE:
```python
{code}
```

BUGS TO FIX:
{bugs}

{pytest_feedback}

Return the COMPLETE corrected Python file with all bugs fixed. Do not truncate. Do not add new features.
IMPORTANT: The fixed_code value must be a valid JSON string. Use single-quoted strings or # comments in the Python code — never triple-quoted strings (\"\"\" or ''') inside fixed_code, as they break JSON encoding.

Respond with JSON only (no markdown fences):
{{
  "fixed_code": "<complete corrected Python source as a string>",
  "changes_summary": ["<change 1>", "<change 2>"]
}}"""


REFLECT_PROMPT = """Your previous fix attempt failed pytest. Review the failure and revise.

CURRENT CODE:
```python
{code}
```

PYTEST OUTPUT:
{pytest_output}

KNOWN BUGS:
{bugs}

Produce a corrected version of the full file. Do not truncate.
IMPORTANT: fixed_code must be a valid JSON string — use single-quoted strings or # comments, never triple-quoted strings (\"\"\" or ''').

Respond with JSON only (no markdown fences):
{{
  "fixed_code": "<complete corrected Python source>",
  "reflection": "<one sentence on what you changed and why>"
}}"""
