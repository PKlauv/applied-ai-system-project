import os
import shutil
import tempfile
import pytest
from agent.tools import read_file, write_to_sandbox, run_pytest, make_sandbox, cleanup_sandbox


@pytest.fixture()
def tmpdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_read_file_returns_content_and_line_count(tmpdir):
    p = os.path.join(tmpdir, "sample.py")
    with open(p, "w") as f:
        f.write("a = 1\nb = 2\n")
    result = read_file(p)
    assert result["content"] == "a = 1\nb = 2\n"
    assert result["lines"] == 2  # splitlines() on "a = 1\nb = 2\n" → 2


def test_write_to_sandbox_creates_file(tmpdir):
    result = write_to_sandbox(tmpdir, "out.py", "x = 42\n")
    assert os.path.isfile(result["written"])
    assert open(result["written"]).read() == "x = 42\n"


def test_run_pytest_passes_on_valid_code(tmpdir):
    with open(os.path.join(tmpdir, "test_ok.py"), "w") as f:
        f.write("def test_always_passes():\n    assert 1 + 1 == 2\n")
    result = run_pytest(tmpdir, "test_ok.py", timeout=10)
    assert result["passed"] is True


def test_run_pytest_fails_on_broken_code(tmpdir):
    with open(os.path.join(tmpdir, "test_bad.py"), "w") as f:
        f.write("def test_fails():\n    assert 1 == 2\n")
    result = run_pytest(tmpdir, "test_bad.py", timeout=10)
    assert result["passed"] is False
    assert "output" in result


def test_run_pytest_handles_timeout(tmpdir):
    with open(os.path.join(tmpdir, "test_slow.py"), "w") as f:
        f.write("import time\ndef test_slow():\n    time.sleep(60)\n")
    result = run_pytest(tmpdir, "test_slow.py", timeout=1)
    assert result["passed"] is False
    assert "timed out" in result["output"]


def test_make_sandbox_copies_file(tmpdir):
    src = os.path.join(tmpdir, "original.py")
    with open(src, "w") as f:
        f.write("pass\n")
    sbx, fname = make_sandbox(src)
    assert os.path.isfile(os.path.join(sbx, fname))
    cleanup_sandbox(sbx)
