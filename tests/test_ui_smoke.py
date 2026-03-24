import ctypes.util
import os
import subprocess
import sys

import pytest


def test_ui_smoke():
    if ctypes.util.find_library("EGL") is None:
        pytest.skip("Brak biblioteki systemowej libEGL wymaganej przez PyQt6 w teście UI smoke.")

    env = os.environ.copy()
    env["LUMBAGO_SAFE_MODE"] = "1"
    env["LUMBAGO_SMOKE_SECONDS"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", "from lumbago_app import main; raise SystemExit(main.main())"],
        env=env,
        check=False,
    )
    assert result.returncode == 0
