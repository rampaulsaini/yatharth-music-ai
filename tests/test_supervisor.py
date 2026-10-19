import subprocess, sys


def test_supervisor_compiles():
    result = subprocess.run([sys.executable, "-m", "py_compile", "supervisor.py"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
