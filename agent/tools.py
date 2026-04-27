import os
import shutil
import subprocess
import sys
import tempfile


def read_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"path": path, "content": content, "lines": len(content.splitlines())}


def write_to_sandbox(sandbox_dir: str, filename: str, content: str) -> dict:
    dest = os.path.join(sandbox_dir, filename)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    return {"written": dest}


def run_pytest(sandbox_dir: str, target_file: str, timeout: int = 5) -> dict:
    """Run pytest on target_file inside sandbox_dir. Returns structured result."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", target_file, "-v", "--tb=short", "--no-header", "-q"],
            cwd=sandbox_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        passed = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        passed = False
        output = f"pytest timed out after {timeout}s"
    except FileNotFoundError:
        passed = False
        output = "pytest not found in PATH"

    return {"passed": passed, "output": output[:3000]}


def make_sandbox(source_path: str) -> tuple[str, str]:
    """Copy source file into a fresh temp dir. Returns (sandbox_dir, filename)."""
    sandbox_dir = tempfile.mkdtemp(prefix="glitch_sbx_")
    filename = os.path.basename(source_path)
    shutil.copy2(source_path, os.path.join(sandbox_dir, filename))
    return sandbox_dir, filename


def cleanup_sandbox(sandbox_dir: str) -> None:
    shutil.rmtree(sandbox_dir, ignore_errors=True)
