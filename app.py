import json
import os
import tempfile

import streamlit as st

from agent.core import investigate
from agent.guardrails import GuardrailError
from agent.schema import Report

st.set_page_config(page_title="Game Glitch Investigator", page_icon="🕵️", layout="wide")

# --- Sidebar ---
with st.sidebar:
    st.title("🕵️ Game Glitch Investigator")
    st.caption("An AI agent that finds and fixes bugs in Python code.")
    st.divider()
    st.markdown("**Model:** Llama 3.3 70B (via Groq)")
    max_iters = st.slider("Max fix iterations", min_value=1, max_value=5, value=3)
    st.divider()
    st.markdown(
        "**How it works:**\n"
        "1. Upload a `.py` file\n"
        "2. The agent plans, analyzes, fixes, and tests\n"
        "3. Review the bug report and corrected code"
    )

# --- Main ---
st.header("🕵️ Game Glitch Investigator")
st.caption(
    "Extended from [Module 1: Game Glitch Investigator]"
    "(https://github.com/PKlauv/ai110-module1show-gameglitchinvestigator-starter) — "
    "now an AI agent that finds the bugs automatically."
)

uploaded = st.file_uploader("Upload a buggy .py file", type=["py"])

if uploaded is None:
    st.info("Upload a `.py` file above to get started. Try one of the files in `eval/fixtures/`.")
    st.stop()

if st.button("🔍 Investigate", type="primary"):
    # Write upload to temp file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="wb") as tmp:
        tmp.write(uploaded.getvalue())
        tmp_path = tmp.name

    try:
        st.session_state.pop("report", None)

        # Live progress area
        status_area = st.status("Running agent...", expanded=True)
        steps_log = []

        try:
            gen = investigate(tmp_path, max_iters=max_iters)
            report: Report = None

            with status_area:
                try:
                    while True:
                        step = next(gen)
                        steps_log.append(step)
                        icon = {
                            "plan": "🔍",
                            "plan_result": "📋",
                            "analyze": "🧪",
                            "analyze_result": "🐛",
                            "fix": "🔧",
                            "test": "⚗️",
                            "test_result": "📊",
                            "done": "🏁",
                        }.get(step["step"], "▶")
                        st.write(f"{icon} **{step['step'].upper()}** — {step['message']}")
                except StopIteration as exc:
                    report = exc.value

            status_area.update(label="Investigation complete!", state="complete", expanded=False)
            st.session_state["report"] = report
            st.session_state["steps_log"] = steps_log

        except GuardrailError as err:
            status_area.update(label="Guardrail triggered", state="error")
            st.error(f"**Guardrail:** {err}")

    finally:
        os.unlink(tmp_path)

# --- Report display ---
if "report" in st.session_state:
    report: Report = st.session_state["report"]
    steps_log = st.session_state.get("steps_log", [])

    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bugs Found", len(report.final_bugs))
    col2.metric("Avg Confidence", f"{report.avg_confidence:.0%}")
    col3.metric("Iterations", len(report.iterations))
    col4.metric("Tests Pass", "Yes" if report.final_pytest_passed else "No")

    st.subheader("Bug Report")
    if not report.final_bugs:
        st.success("No bugs found!")
    else:
        for bug in report.final_bugs:
            severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(bug.severity, "⚪")
            with st.expander(
                f"{severity_color} [{bug.severity.upper()}] {bug.label} "
                f"— line {bug.line} — conf {bug.confidence:.0%}"
            ):
                st.write(bug.explanation)

    # Show final fixed code if available
    final_iter = report.iterations[-1] if report.iterations else None
    if final_iter and final_iter.fixed_code:
        st.subheader("Corrected Code")
        st.code(final_iter.fixed_code, language="python")

    # Pytest output
    if report.final_pytest_output:
        with st.expander("Pytest output"):
            st.code(report.final_pytest_output, language="text")

    # Decision chain
    with st.expander("Decision chain (agent trace)"):
        trace_path = os.path.join("runs", report.run_id, "trace.jsonl")
        if os.path.isfile(trace_path):
            with open(trace_path) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        st.json(entry, expanded=False)
                    except Exception:
                        pass
        else:
            st.warning("Trace file not found.")
