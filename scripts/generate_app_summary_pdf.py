from __future__ import annotations

from pathlib import Path

import fitz
from pypdf import PdfReader
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
OUTPUT_PDF = OUTPUT_DIR / "lumbago_app_summary_pl.pdf"
OUTPUT_PNG = TMP_DIR / "lumbago_app_summary_pl_page1.png"


TITLE = "Lumbago Music AI"
SUBTITLE = "Jednostronicowe podsumowanie aplikacji na podstawie kodu repozytorium"

WHAT_IT_IS = [
    "Desktopowa aplikacja Windows w Pythonie do zarz\u0105dzania lokaln\u0105 bibliotek\u0105 muzyczn\u0105.",
    "\u0141\u0105czy przegl\u0105d biblioteki, edycj\u0119 tag\u00f3w, analiz\u0119 audio i narz\u0119dzia dla workflow DJ.",
]

WHO_ITS_FOR = "DJ-e i kolekcjonerzy muzyki pracuj\u0105cy lokalnie na plikach audio."

FEATURES = [
    "Importuje i skanuje foldery audio oraz odczytuje metadane plik\u00f3w.",
    "Pokazuje bibliotek\u0119 w widoku tabeli i siatki z filtrowaniem oraz wyszukiwaniem.",
    "Pozwala edytowa\u0107 tagi, por\u00f3wnywa\u0107 je i zapisywa\u0107 zmiany z powrotem do plik\u00f3w.",
    "Obs\u0142uguje playlisty, smart playlisty i r\u0119czne porz\u0105dkowanie utwor\u00f3w.",
    "Wykrywa duplikaty oraz wspiera zmian\u0119 nazw plik\u00f3w z kontrol\u0105 konflikt\u00f3w.",
    "Uruchamia analiz\u0119 BPM, key, loudness, cue points oraz import i eksport XML DJ.",
    "Dodaje lokalny AI tagging oraz opcjonalne uzupe\u0142nianie metadanych z us\u0142ug online.",
]

ARCHITECTURE = [
    "Entry point: lumbago_app/main.py \u0142aduje .env, tworzy QApplication i otwiera MainWindow.",
    "UI: ui/ zawiera g\u0142\u00f3wne okno, dialogi, modele tabeli oraz workery t\u0142a dla skanu, analizy i batch jobs.",
    "Core: core/ obs\u0142uguje konfiguracj\u0119, audio I/O, backup, heurystyki analizy i cache waveform/analysis.",
    "Services: services/ realizuje AI tagging, metadata enrichment, rozpoznawanie, key/loudness i XML.",
    "Data flow: pliki audio -> ekstrakcja i analiza -> repozytorium SQLAlchemy -> SQLite -> od\u015bwie\u017canie UI.",
]

GETTING_STARTED = [
    "Utw\u00f3rz venv: python -m venv .venv",
    "Aktywuj \u015brodowisko: .venv\\Scripts\\activate",
    "Zainstaluj zale\u017cno\u015bci: pip install -r requirements.txt",
    "Uruchom aplikacj\u0119: python -m lumbago_app.main",
]


def _register_fonts() -> tuple[str, str]:
    candidates = [
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "Arial", "Arial-Bold"),
        ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf", "SegoeUI", "SegoeUI-Bold"),
    ]
    for regular_path, bold_path, regular_name, bold_name in candidates:
        regular = Path(regular_path)
        bold = Path(bold_path)
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont(regular_name, str(regular)))
            pdfmetrics.registerFont(TTFont(bold_name, str(bold)))
            return regular_name, bold_name
    return "Helvetica", "Helvetica-Bold"


def _draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font_name: str,
    font_size: int,
    color: Color,
    leading: float | None = None,
) -> float:
    lines = simpleSplit(text, font_name, font_size, width)
    text_obj = pdf.beginText(x, y)
    text_obj.setFont(font_name, font_size)
    text_obj.setFillColor(color)
    text_obj.setLeading(leading or font_size + 2)
    for line in lines:
        text_obj.textLine(line)
    pdf.drawText(text_obj)
    return y - len(lines) * (leading or font_size + 2)


def _draw_section(
    pdf: canvas.Canvas,
    title: str,
    body_lines: list[str],
    x: float,
    y: float,
    width: float,
    regular_font: str,
    bold_font: str,
) -> float:
    y = _draw_wrapped_text(pdf, title, x, y, width, bold_font, 11, HexColor("#0F172A"), leading=13)
    y -= 3
    for line in body_lines:
        if line.startswith("- "):
            wrapped = simpleSplit(line[2:], regular_font, 8.6, width - 12)
            text_obj = pdf.beginText(x, y)
            text_obj.setFont(regular_font, 8.6)
            text_obj.setLeading(10.2)
            text_obj.setFillColor(HexColor("#1F2937"))
            text_obj.textOut("\u2022 ")
            if wrapped:
                text_obj.textLine(wrapped[0])
                for cont in wrapped[1:]:
                    text_obj.moveCursor(12, 0)
                    text_obj.textLine(cont)
            pdf.drawText(text_obj)
            y -= len(wrapped) * 10.2 if wrapped else 10.2
        else:
            y = _draw_wrapped_text(pdf, line, x, y, width, regular_font, 8.6, HexColor("#1F2937"), leading=10.2)
        y -= 2
    return y - 5


def generate_pdf() -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    regular_font, bold_font = _register_fonts()
    page_width, page_height = A4
    pdf = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)
    pdf.setTitle("Lumbago Music AI - Podsumowanie")
    pdf.setAuthor("Codex")

    margin = 34
    card_x = margin
    card_y = margin
    card_w = page_width - 2 * margin
    card_h = page_height - 2 * margin

    pdf.setFillColor(HexColor("#F4F7FB"))
    pdf.rect(0, 0, page_width, page_height, stroke=0, fill=1)

    pdf.setFillColor(white)
    pdf.roundRect(card_x, card_y, card_w, card_h, 18, stroke=0, fill=1)

    pdf.setFillColor(HexColor("#0F4C81"))
    pdf.roundRect(card_x, page_height - 122, card_w, 88, 18, stroke=0, fill=1)

    pdf.setFillColor(white)
    pdf.setFont(bold_font, 22)
    pdf.drawString(card_x + 22, page_height - 70, TITLE)
    pdf.setFont(regular_font, 9.2)
    pdf.drawString(card_x + 22, page_height - 87, SUBTITLE)

    left_x = card_x + 22
    right_x = card_x + card_w * 0.56
    top_y = page_height - 145
    left_w = card_w * 0.48 - 20
    right_w = card_w * 0.40 - 12

    y_left = top_y
    y_left = _draw_section(pdf, "Czym jest", WHAT_IT_IS, left_x, y_left, left_w, regular_font, bold_font)
    y_left = _draw_section(pdf, "Dla kogo", [WHO_ITS_FOR], left_x, y_left, left_w, regular_font, bold_font)
    y_left = _draw_section(
        pdf,
        "Co robi",
        [f"- {item}" for item in FEATURES],
        left_x,
        y_left,
        left_w,
        regular_font,
        bold_font,
    )

    y_right = top_y
    y_right = _draw_section(
        pdf,
        "Jak dzia\u0142a",
        [f"- {item}" for item in ARCHITECTURE],
        right_x,
        y_right,
        right_w,
        regular_font,
        bold_font,
    )
    y_right = _draw_section(
        pdf,
        "Jak uruchomi\u0107",
        [f"- {item}" for item in GETTING_STARTED],
        right_x,
        y_right,
        right_w,
        regular_font,
        bold_font,
    )

    footer = "\u0179r\u00f3d\u0142a: README.md, lumbago_app/main.py, ui/main_window.py, core/config.py, data/*.py, services/*.py, tests/*."
    pdf.setStrokeColor(HexColor("#D8E1EC"))
    pdf.line(card_x + 22, card_y + 28, card_x + card_w - 22, card_y + 28)
    _draw_wrapped_text(
        pdf,
        footer,
        card_x + 22,
        card_y + 18,
        card_w - 44,
        regular_font,
        7.6,
        HexColor("#5B6470"),
        leading=9,
    )

    pdf.showPage()
    pdf.save()

    reader = PdfReader(str(OUTPUT_PDF))
    if len(reader.pages) != 1:
        raise RuntimeError(f"Expected exactly 1 page, got {len(reader.pages)}")

    with fitz.open(str(OUTPUT_PDF)) as doc:
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        pix.save(str(OUTPUT_PNG))

    return OUTPUT_PDF, OUTPUT_PNG


if __name__ == "__main__":
    pdf_path, png_path = generate_pdf()
    print(pdf_path)
    print(png_path)
