"""
theme.py
Soft matte graphite palette shared across every screen.
Functions and logic remain 100% compatible with existing code.
"""

# Оновлені кольори: світліший графітовий фон та контрастні картки
BG_ROOT = "#1C1E22"        # М'який графітовий фон (замість вугільно-чорного)
BG_CARD = "#282B30"        # Світліша поверхня карток
BG_CARD_ALT = "#32353B"    # Графітовий відтінок для рядків та полів вводу
ACCENT = "#3D7EFF"         # Основний синій акцент (кнопки, активні елементи)
ACCENT_SOFT = "#26314D"

TEXT_PRIMARY = "#F2F2F3"   # Основний яскравий текст
TEXT_SECONDARY = "#9A9DA3" # Допоміжний текст
DIVIDER = "#3A3D44"        # Лінії розмежування

# Індикатори статусів (Контрольні лампи щитка приладів)
STATUS_GREEN = "#3DDC84"   # Норма
STATUS_YELLOW = "#F5C242"  # Увага (скоро заміна)
STATUS_RED = "#F0503C"     # Помилка / Критичний знос


def status_color(remaining_km):
    """
    Визначає колір індикатора на основі залишку пробігу (аналог датчика зносу).
    """
    if remaining_km is None:
        return TEXT_SECONDARY
    if remaining_km <= 0:
        return STATUS_RED
    if remaining_km <= 1000:
        return STATUS_YELLOW
    return STATUS_GREEN


def hex_to_rgba(hex_color, alpha=1.0):
    """
    Перетворює HEX-код кольору у формат RGBA (0.0 - 1.0) для Kivy.
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return [r, g, b, alpha]
