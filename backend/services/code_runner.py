import subprocess
import tempfile
import os
import sys
from typing import Tuple

TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARS = 4000


def run_python(code: str) -> Tuple[str, bool]:
    """Execute Python code in a subprocess with timeout. Returns (output, success)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        output = result.stdout + (f"\n[stderr]\n{result.stderr}" if result.stderr.strip() else "")
        success = result.returncode == 0
    except subprocess.TimeoutExpired:
        output = f"⏱ Time limit exceeded ({TIMEOUT_SECONDS}s)"
        success = False
    except Exception as e:
        output = f"Execution error: {e}"
        success = False
    finally:
        os.unlink(tmp_path)

    return output[:MAX_OUTPUT_CHARS], success


def run_javascript(code: str) -> Tuple[str, bool]:
    """Execute JavaScript code via Node.js with timeout. Returns (output, success)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["node", tmp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        output = result.stdout + (f"\n[stderr]\n{result.stderr}" if result.stderr.strip() else "")
        success = result.returncode == 0
    except subprocess.TimeoutExpired:
        output = f"⏱ Time limit exceeded ({TIMEOUT_SECONDS}s)"
        success = False
    except FileNotFoundError:
        output = "Node.js is not installed on the server."
        success = False
    except Exception as e:
        output = f"Execution error: {e}"
        success = False
    finally:
        os.unlink(tmp_path)

    return output[:MAX_OUTPUT_CHARS], success


def run_code(language: str, code: str) -> Tuple[str, bool]:
    """Dispatch code execution by language."""
    if language == "python":
        return run_python(code)
    elif language == "javascript":
        return run_javascript(code)
    return "Unsupported language.", False
