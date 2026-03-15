import os
import subprocess
import sys


def test_ui_smoke():
    env = os.environ.copy()
    env["LUMBAGO_SAFE_MODE"] = "1"
    env["LUMBAGO_SMOKE_SECONDS"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", "from lumbago_app import main; raise SystemExit(main.main())"],
        env=env,
        check=False,
    )
    assert result.returncode == 0
