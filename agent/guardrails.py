import os

MAX_FILE_BYTES = 100_000  # 100 KB


class GuardrailError(Exception):
    pass


def validate_input(path: str) -> None:
    if not path.endswith(".py"):
        raise GuardrailError(f"Only .py files are supported (got: {path})")
    if not os.path.isfile(path):
        raise GuardrailError(f"File not found: {path}")
    size = os.path.getsize(path)
    if size > MAX_FILE_BYTES:
        raise GuardrailError(
            f"File too large: {size} bytes (max {MAX_FILE_BYTES}). "
            "Split the file before investigating."
        )
