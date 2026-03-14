from __future__ import annotations

import sys

from dotenv import load_dotenv
from PyQt6 import QtWidgets

from lumbago_app.ui.main_window import MainWindow
from lumbago_app.ui.theme import CYBER_QSS


def main() -> int:
    load_dotenv()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(CYBER_QSS)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

