"""
Evaluation harness: runs the agent on all fixtures and scores results.

Usage:
    python -m eval.harness
"""
import json
import os
import sys

# ---- Scoring helpers --------------------------------------------------------

def score_fixture(reported_labels: list[str], expected_keywords: list[str]) -> dict:
    """
    Fuzzy precision/recall:
    - A bug is "found" if any expected keyword appears in any reported label (case-insensitive).
    - Precision: fraction of reported bugs that match at least one expected keyword.
    - Recall: fraction of expected keywords matched by at least one reported label.
    """
    reported_lower = [r.lower() for r in reported_labels]
    found_keywords = [
        kw for kw in expected_keywords
        if any(kw.lower() in label for label in reported_lower)
    ]
    matched_reports = [
        label for label in reported_lower
        if any(kw.lower() in label for kw in expected_keywords)
    ]

    recall = len(found_keywords) / len(expected_keywords) if expected_keywords else 1.0
    precision = len(matched_reports) / len(reported_lower) if reported_lower else 0.0
    return {
        "recall": round(recall, 2),
        "precision": round(precision, 2),
        "found_keywords": found_keywords,
        "missed_keywords": [kw for kw in expected_keywords if kw not in found_keywords],
    }


# ---- Main -------------------------------------------------------------------

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def run_harness(max_iters: int = 3, verbose: bool = True) -> list[dict]:
    from agent.core import investigate
    from agent.guardrails import GuardrailError

    fixture_dirs = sorted(
        d for d in os.listdir(FIXTURES_DIR)
        if os.path.isdir(os.path.join(FIXTURES_DIR, d))
    )

    results = []
    for fixture_name in fixture_dirs:
        fixture_path = os.path.join(FIXTURES_DIR, fixture_name)
        buggy_file = os.path.join(fixture_path, "buggy.py")
        expected_file = os.path.join(fixture_path, "expected_bugs.json")

        if not os.path.isfile(buggy_file) or not os.path.isfile(expected_file):
            continue

        with open(expected_file) as f:
            expected_keywords = json.load(f).get("bugs", [])

        if verbose:
            print(f"\n{'='*60}")
            print(f"Fixture: {fixture_name}")
            print(f"Expected keywords: {expected_keywords}")
            print("Running agent...", flush=True)

        try:
            gen = investigate(buggy_file, max_iters=max_iters)
            report = None
            try:
                while True:
                    step = next(gen)
                    if verbose:
                        print(f"  [{step['step']}] {step['message']}", flush=True)
            except StopIteration as exc:
                report = exc.value

            reported_labels = [b.label for b in report.final_bugs]
            score = score_fixture(reported_labels, expected_keywords)
            passed = score["recall"] >= 0.5

            result = {
                "fixture": fixture_name,
                "bugs_found": len(report.final_bugs),
                "reported_labels": reported_labels,
                "precision": score["precision"],
                "recall": score["recall"],
                "avg_confidence": round(report.avg_confidence, 2),
                "iterations": len(report.iterations),
                "pytest_passed": report.final_pytest_passed,
                "passed": passed,
                "missed_keywords": score["missed_keywords"],
            }

        except GuardrailError as err:
            result = {
                "fixture": fixture_name,
                "passed": False,
                "error": str(err),
            }
        except Exception as err:
            result = {
                "fixture": fixture_name,
                "passed": False,
                "error": repr(err),
            }

        results.append(result)
        if verbose:
            status = "PASS" if result.get("passed") else "FAIL"
            print(f"  Result: {status} | recall={result.get('recall','N/A')} | "
                  f"confidence={result.get('avg_confidence','N/A')} | "
                  f"iters={result.get('iterations','N/A')}")

    return results


def print_summary(results: list[dict]) -> None:
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    header = f"{'Fixture':<30} {'Pass':>4} {'Recall':>6} {'Prec':>6} {'Conf':>6} {'Iters':>5}"
    print(header)
    print("-" * len(header))
    total_pass = 0
    for r in results:
        if "error" in r:
            print(f"{r['fixture']:<30} {'FAIL':>4}  ERROR: {r['error'][:40]}")
        else:
            status = "YES" if r["passed"] else "NO"
            if r["passed"]:
                total_pass += 1
            print(
                f"{r['fixture']:<30} {status:>4} {r['recall']:>6.2f} "
                f"{r['precision']:>6.2f} {r['avg_confidence']:>6.2f} {r['iterations']:>5}"
            )
    print(f"\nTotal: {total_pass}/{len(results)} passed")
    confidences = [r["avg_confidence"] for r in results if "avg_confidence" in r]
    if confidences:
        print(f"Overall avg confidence: {sum(confidences)/len(confidences):.2f}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Glitch Investigator Eval Harness")
    parser.add_argument("--max-iters", type=int, default=3)
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    results = run_harness(max_iters=args.max_iters, verbose=not args.json)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_summary(results)
