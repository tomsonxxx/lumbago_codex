from __future__ import annotations

import sys

from PyQt6 import QtWidgets

from .ui import MainWindow


def run() -> int:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())

