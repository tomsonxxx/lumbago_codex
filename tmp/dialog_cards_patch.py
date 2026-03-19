import re, pathlib
files=[r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\ai_tagger_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\bulk_edit_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\change_history_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\duplicates_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\import_wizard.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\playlist_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\playlist_order_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\renamer_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\settings_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\tag_compare_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\xml_converter_dialog.py",
       r"C:\Users\tomso\Desktop\Nowy folder\lumbago_app\ui\xml_import_dialog.py"]

def block_tpl(i: str) -> str:
    return (
        f"{i}layout = QtWidgets.QVBoxLayout(self)\n"
        f"{i}layout.setContentsMargins(16, 16, 16, 16)\n"
        f"{i}layout.setSpacing(12)\n\n"
        f"{i}card = QtWidgets.QFrame()\n"
        f"{i}card.setObjectName(\"DialogCard\")\n"
        f"{i}card_layout = QtWidgets.QVBoxLayout(card)\n"
        f"{i}card_layout.setContentsMargins(16, 14, 16, 16)\n"
        f"{i}card_layout.setSpacing(10)\n"
        f"{i}layout.addWidget(card)\n"
        f"{i}layout = card_layout\n\n"
        f"{i}title = QtWidgets.QLabel(self.windowTitle())\n"
        f"{i}title.setObjectName(\"DialogTitle\")\n"
        f"{i}layout.addWidget(title)\n"
    )

pat = re.compile(r"(?ms)^([ \t]*)layout = QtWidgets\.QVBoxLayout\(self\)\r?\n(?:.*\r?\n){0,25}?^[ \t]*layout\.addWidget\(title\)\r?\n")
first = re.compile(r"(?m)^([ \t]*)layout = QtWidgets\.QVBoxLayout\(self\)")

for p in files:
    path = pathlib.Path(p)
    text = path.read_text(encoding="utf-8")
    if pat.search(text):
        text = pat.sub(lambda m: block_tpl(m.group(1)), text, count=1)
    else:
        text = first.sub(lambda m: block_tpl(m.group(1)), text, count=1)
    path.write_text(text, encoding="utf-8")
