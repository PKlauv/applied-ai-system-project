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


ANALYZE_PROMPT = """You are investigating buggy Python code. Below is the code and a list of hypotheses.

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

Respond with JSON only (no markdown fences):
{{
  "fixed_code": "<complete corrected Python source>",
  "reflection": "<one sentence on what you changed and why>"
}}"""
