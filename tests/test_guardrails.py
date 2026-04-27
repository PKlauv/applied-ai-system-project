import os
import tempfile
import pytest
from agent.guardrails import validate_input, GuardrailError


def test_rejects_non_py_file():
    with pytest.raises(GuardrailError, match="Only .py files"):
        validate_input("README.md")


def test_rejects_missing_file():
    with pytest.raises(GuardrailError, match="File not found"):
        validate_input("nonexistent.py")


def test_rejects_oversized_file():
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b"x" * 100_001)
        path = f.name
    try:
        with pytest.raises(GuardrailError, match="too large"):
            validate_input(path)
    finally:
        os.unlink(path)


def test_accepts_valid_py_file():
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(b"print('hello')\n")
        path = f.name
    try:
        validate_input(path)  # should not raise
    finally:
        os.unlink(path)
