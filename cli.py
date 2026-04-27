"""CLI entry point: python -m cli <path/to/buggy.py> [--max-iters N] [--json]"""
import argparse
import json
import sys

from agent.core import investigate
from agent.guardrails import GuardrailError
from agent.schema import Report


def _print_step(step: dict) -> None:
    icon = {
        "plan": "🔍",
        "plan_result": "📋",
        "analyze": "🧪",
        "analyze_result": "🐛",
        "fix": "🔧",
        "test": "⚗️",
        "test_result": "✅" if False else "📊",
        "done": "🏁",
    }.get(step["step"], "▶")
    print(f"{icon}  [{step['step'].upper()}] {step['message']}", flush=True)


def _report_to_dict(report: Report) -> dict:
    return {
        "run_id": report.run_id,
        "source_file": report.source_file,
        "iterations": len(report.iterations),
        "final_pytest_passed": report.final_pytest_passed,
        "avg_confidence": round(report.avg_confidence, 3),
        "bugs": [
            {
                "label": b.label,
                "severity": b.severity,
                "confidence": b.confidence,
                "line": b.line,
                "explanation": b.explanation,
            }
            for b in report.final_bugs
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Game Glitch Investigator CLI")
    parser.add_argument("path", help="Path to the .py file to investigate")
    parser.add_argument("--max-iters", type=int, default=3, help="Max fix iterations (default 3)")
    parser.add_argument("--json", action="store_true", help="Output final report as JSON")
    args = parser.parse_args()

    try:
        gen = investigate(args.path, max_iters=args.max_iters)
        report = None
        try:
            while True:
                step = next(gen)
                if not args.json:
                    _print_step(step)
        except StopIteration as exc:
            report = exc.value

        if args.json:
            print(json.dumps(_report_to_dict(report), indent=2))
        else:
            print("\n" + "=" * 60)
            print(f"REPORT — {report.run_id}")
            print("=" * 60)
            print(f"Bugs found   : {len(report.final_bugs)}")
            print(f"Avg confidence: {report.avg_confidence:.2f}")
            print(f"Iterations   : {len(report.iterations)}")
            print(f"Tests pass   : {report.final_pytest_passed}")
            print()
            for i, bug in enumerate(report.final_bugs, 1):
                print(
                    f"  {i}. [{bug.severity.upper()}] {bug.label} "
                    f"(line {bug.line}, conf={bug.confidence:.2f})"
                )
                print(f"     {bug.explanation}")
            print()
            print(f"Run trace: runs/{report.run_id}/trace.jsonl")

    except GuardrailError as err:
        print(f"GUARDRAIL: {err}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
