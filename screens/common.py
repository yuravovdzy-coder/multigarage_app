"""
screens/common.py
Reusable "Camera / Photo" button + OCR pre-fill flow shared by every
input form in the app (fuel, maintenance, expenses, mods, etc.).
"""

import os
import shutil
import datetime
from kivymd.uix.button import MDIconButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.snackbar import Snackbar

import ocr_engine

RECEIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "receipts",
)
os.makedirs(RECEIPTS_DIR, exist_ok=True)


def make_photo_button(on_result):
    """
    Returns an MDIconButton. When tapped, opens the file manager (photo
    picker), copies the chosen image into assets/receipts/, runs OCR,
    and calls on_result(parsed_dict, saved_path).
    """

    def open_picker(*_):
        def select_path(path):
            manager.close()
            saved_path = _store_receipt(path)
            parsed = ocr_engine.parse_receipt(saved_path)
            if not parsed.get("ocr_available"):
                Snackbar(text="OCR недоступний на цьому пристрої — заповніть поля вручну.").open()
            on_result(parsed, saved_path)

        def exit_manager(*args):
            manager.close()

        manager = MDFileManager(
            exit_manager=exit_manager,
            select_path=select_path,
            ext=[".jpg", ".jpeg", ".png"],
        )
        manager.show(os.path.expanduser("~"))

    btn = MDIconButton(icon="camera")
    btn.bind(on_release=open_picker)
    return btn


def _store_receipt(src_path):
    ext = os.path.splitext(src_path)[1] or ".jpg"
    dest = os.path.join(
        RECEIPTS_DIR, f"receipt_{datetime.datetime.now():%Y%m%d_%H%M%S}{ext}"
    )
    try:
        shutil.copy(src_path, dest)
        return dest
    except Exception:
        return src_path


def today():
    return datetime.date.today().isoformat()
