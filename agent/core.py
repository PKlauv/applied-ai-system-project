import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Generator

from agent.guardrails import validate_input
from agent.llm import call_structured
from agent.logger import RunLogger
from agent.prompts import (
    SYSTEM_PROMPT, PLAN_PROMPT,
    ANALYZE_PROMPT, ANALYZE_PROMPT_BASELINE,
    FIX_PROMPT, REFLECT_PROMPT,
)

# Set FEWSHOT=0 to use the zero-shot baseline for A/B comparison.
_ANALYZE_PROMPT = ANALYZE_PROMPT_BASELINE if os.environ.get("FEWSHOT") == "0" else ANALYZE_PROMPT
from agent.schema import BugFinding, IterationResult, Report
from agent.tools import cleanup_sandbox, make_sandbox, read_file, run_pytest, write_to_sandbox

MAX_ITERATIONS = 3


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _bugs_to_text(bugs: list[dict]) -> str:
    return "\n".join(
        f"- [{b.get('severity','?').upper()}] {b.get('label','?')} "
        f"(line {b.get('line','?')}): {b.get('explanation','')}"
        for b in bugs
    )


def _parse_bugs(raw_bugs: list[dict]) -> list[BugFinding]:
    findings = []
    for b in raw_bugs:
        findings.append(BugFinding(
            label=b.get("label", "unknown"),
            severity=b.get("severity", "medium"),
            confidence=float(b.get("confidence", 0.5)),
            line=b.get("line"),
            explanation=b.get("explanation", ""),
        ))
    return findings


def investigate(path: str, max_iters: int = MAX_ITERATIONS) -> Generator[dict, None, Report]:
    """
    Generator that yields step dicts for live display, then returns a Report.

    Usage:
        gen = investigate("buggy.py")
        try:
            while True:
                step = next(gen)
                display(step)
        except StopIteration as e:
            report = e.value
    """
    validate_input(path)

    run_id = _run_id()
    sandbox_dir, filename = make_sandbox(path)
    current_path = os.path.join(sandbox_dir, filename)

    try:
        with RunLogger(run_id) as logger:
            # --- PLAN ---
            yield {"step": "plan", "message": "Reading code and forming investigation plan..."}
            file_data = read_file(current_path)
            logger.log_tool_call("read_file", {"path": current_path})
            logger.log_tool_result("read_file", {"lines": file_data["lines"]})

            code = file_data["content"]
            plan_prompt = PLAN_PROMPT.format(code=code)
            logger.log_llm_call("plan", plan_prompt)
            plan_data = call_structured(SYSTEM_PROMPT, plan_prompt)
            logger.log_plan(plan_data)
            hypotheses = plan_data.get("hypotheses", [])

            yield {
                "step": "plan_result",
                "message": f"Found {len(hypotheses)} hypothesis(es). Starting analysis.",
                "data": plan_data,
            }

            # --- ANALYZE ---
            yield {"step": "analyze", "message": "Analyzing code against hypotheses..."}
            hyp_text = "\n".join(
                f"{h['id']}. {h['description']} (lines: {h.get('target_lines','?')})"
                for h in hypotheses
            )
            analyze_prompt = _ANALYZE_PROMPT.format(code=code, hypotheses=hyp_text)
            logger.log_llm_call("analyze", analyze_prompt)
            analyze_data = call_structured(SYSTEM_PROMPT, analyze_prompt)
            raw_bugs = analyze_data.get("bugs", [])

            yield {
                "step": "analyze_result",
                "message": f"Identified {len(raw_bugs)} bug(s).",
                "data": analyze_data,
            }

            # --- FIX + TEST LOOP ---
            iterations: list[IterationResult] = []
            pytest_feedback = ""
            current_code = code
            _FEEDBACK_MAX = 1500

            for iteration in range(1, max_iters + 1):
                yield {"step": "fix", "message": f"Iteration {iteration}: generating fix..."}

                feedback_trimmed = pytest_feedback[-_FEEDBACK_MAX:]
                if iteration == 1:
                    fmt_prompt = FIX_PROMPT.format(
                        code=current_code,
                        bugs=_bugs_to_text(raw_bugs),
                        pytest_feedback=feedback_trimmed,
                    )
                else:
                    fmt_prompt = REFLECT_PROMPT.format(
                        code=current_code,
                        pytest_output=feedback_trimmed,
                        bugs=_bugs_to_text(raw_bugs),
                    )

                logger.log_llm_call("fix" if iteration == 1 else "reflect", fmt_prompt)
                try:
                    fix_data = call_structured(SYSTEM_PROMPT, fmt_prompt)
                    fixed_code = fix_data.get("fixed_code", current_code)
                except Exception as llm_err:
                    yield {"step": "fix_error", "message": f"LLM error on iteration {iteration}: {llm_err!r}"}
                    logger.log_tool_result("llm_error", {"error": repr(llm_err)})
                    fixed_code = current_code

                # Write fixed code to sandbox
                logger.log_tool_call("write_to_sandbox", {"filename": filename})
                write_result = write_to_sandbox(sandbox_dir, filename, fixed_code)
                logger.log_tool_result("write_to_sandbox", write_result)
                current_code = fixed_code
                current_path = write_result["written"]

                # Run pytest
                yield {"step": "test", "message": f"Iteration {iteration}: running tests..."}
                logger.log_tool_call("run_pytest", {"file": filename})
                test_result = run_pytest(sandbox_dir, filename)
                logger.log_tool_result("run_pytest", test_result)

                bugs_this_iter = _parse_bugs(raw_bugs)
                iter_result = IterationResult(
                    iteration=iteration,
                    bugs_found=bugs_this_iter,
                    fixed_code=fixed_code,
                    pytest_passed=test_result["passed"],
                    pytest_output=test_result["output"],
                )
                iterations.append(iter_result)
                logger.log_iteration_end(iteration, test_result["passed"])

                yield {
                    "step": "test_result",
                    "message": (
                        f"Iteration {iteration}: tests {'passed' if test_result['passed'] else 'failed'}."
                    ),
                    "data": test_result,
                }

                if test_result["passed"]:
                    break

                pytest_feedback = test_result["output"]

            # --- BUILD REPORT ---
            final_iter = iterations[-1] if iterations else None
            final_bugs = _parse_bugs(raw_bugs)
            report = Report(
                run_id=run_id,
                source_file=path,
                iterations=iterations,
                final_bugs=final_bugs,
                final_pytest_passed=final_iter.pytest_passed if final_iter else False,
                final_pytest_output=final_iter.pytest_output if final_iter else "",
            )

            logger.log_final_report({
                "bugs_found": len(final_bugs),
                "avg_confidence": report.avg_confidence,
                "iterations": len(iterations),
                "pytest_passed": report.final_pytest_passed,
            })

            yield {
                "step": "done",
                "message": (
                    f"Investigation complete. {len(final_bugs)} bug(s) found, "
                    f"avg confidence {report.avg_confidence:.2f}."
                ),
            }

            return report

    finally:
        cleanup_sandbox(sandbox_dir)
