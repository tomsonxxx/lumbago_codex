import ctypes.util
import os
import subprocess
import sys

import pytest


def test_ui_smoke():
    if ctypes.util.find_library("EGL") is None:
        pytest.skip("Brak biblioteki systemowej libEGL wymaganej przez PyQt6 w teście UI smoke.")
    if ctypes.util.find_library("pulse") is None:
        pytest.skip("Brak biblioteki systemowej libpulse wymaganej przez QtMultimedia w teście UI smoke.")

    env = os.environ.copy()
    env["LUMBAGO_SAFE_MODE"] = "1"
    env["LUMBAGO_SMOKE_SECONDS"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", "import main; raise SystemExit(main.main())"],
        env=env,
        check=False,
    )
    assert result.returncode == 0
