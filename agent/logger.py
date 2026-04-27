import json
import os
from datetime import datetime, timezone


class RunLogger:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.log_dir = os.path.join("runs", run_id)
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, "trace.jsonl")
        self._file = open(self.log_path, "w", encoding="utf-8")

    def _write(self, event_type: str, payload: dict) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **payload,
        }
        self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def log_plan(self, plan: dict) -> None:
        self._write("plan", {"plan": plan})

    def log_llm_call(self, step: str, prompt_preview: str) -> None:
        self._write("llm_call", {"step": step, "prompt_preview": prompt_preview[:200]})

    def log_tool_call(self, tool: str, args: dict) -> None:
        self._write("tool_call", {"tool": tool, "args": args})

    def log_tool_result(self, tool: str, result: dict) -> None:
        self._write("tool_result", {"tool": tool, "result": result})

    def log_iteration_end(self, iteration: int, pytest_passed: bool) -> None:
        self._write("iteration_end", {"iteration": iteration, "pytest_passed": pytest_passed})

    def log_final_report(self, report_summary: dict) -> None:
        self._write("final_report", {"summary": report_summary})

    def close(self) -> None:
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
