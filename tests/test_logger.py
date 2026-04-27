import json
import os
import shutil
from agent.logger import RunLogger

RUN_ID = "test_run_logger"


def setup_function():
    shutil.rmtree(os.path.join("runs", RUN_ID), ignore_errors=True)


def teardown_function():
    shutil.rmtree(os.path.join("runs", RUN_ID), ignore_errors=True)


def _read_events(run_id: str):
    path = os.path.join("runs", run_id, "trace.jsonl")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_logger_writes_valid_jsonl():
    with RunLogger(RUN_ID) as logger:
        logger.log_plan({"steps": ["analyze", "fix"]})
        logger.log_llm_call("analyze", "Analyze this code...")
        logger.log_tool_call("run_pytest", {"file": "buggy.py"})
        logger.log_tool_result("run_pytest", {"passed": False})
        logger.log_iteration_end(1, pytest_passed=False)
        logger.log_final_report({"bugs_found": 2})

    events = _read_events(RUN_ID)
    assert len(events) == 6


def test_logger_includes_required_event_types():
    with RunLogger(RUN_ID) as logger:
        logger.log_plan({})
        logger.log_tool_call("read_file", {})
        logger.log_tool_result("read_file", {})
        logger.log_iteration_end(1, pytest_passed=True)
        logger.log_final_report({})

    event_types = {e["event"] for e in _read_events(RUN_ID)}
    for required in ("plan", "tool_call", "tool_result", "iteration_end", "final_report"):
        assert required in event_types


def test_logger_entries_have_timestamps():
    with RunLogger(RUN_ID) as logger:
        logger.log_plan({})

    events = _read_events(RUN_ID)
    assert "ts" in events[0]
