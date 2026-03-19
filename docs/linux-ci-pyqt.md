# Linux/CI: diagnostyka PyQt6

Ten projekt jest targetowany na Windows, ale mozna uruchomic smoke test GUI na Linux/CI.

## Szybka diagnostyka

W katalogu projektu:

```bash
bash scripts/check_pyqt_linux.sh
```

Skrypt:
- sprawdza minimalne pakiety systemowe dla PyQt6 GUI,
- testuje `from PyQt6 import QtWidgets`,
- uruchamia krotki smoke test aplikacji:
  `LUMBAGO_SAFE_MODE=1 LUMBAGO_DISABLE_MULTIMEDIA=1 LUMBAGO_SMOKE_SECONDS=2 python -m lumbago_app.main`.

## Automatyczna instalacja brakujacych pakietow

```bash
INSTALL_DEPS=1 bash scripts/check_pyqt_linux.sh
```

Z multimediami Qt (`QMediaPlayer`, `QAudioOutput`):

```bash
INSTALL_DEPS=1 WITH_MULTIMEDIA=1 bash scripts/check_pyqt_linux.sh
```

## CI/headless (bez aktywnego X)

```bash
sudo apt-get update
sudo apt-get install -y xvfb
xvfb-run -a env LUMBAGO_SAFE_MODE=1 LUMBAGO_DISABLE_MULTIMEDIA=1 LUMBAGO_SMOKE_SECONDS=2 python -m lumbago_app.main
```
