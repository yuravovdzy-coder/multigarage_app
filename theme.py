"""
theme.py
Matte dark-graphite / near-black palette shared across every screen.
"""

BG_ROOT = "#0E0F11"        # matte black background
BG_CARD = "#1A1C1F"        # graphite card surface
BG_CARD_ALT = "#212327"    # slightly lighter surface (rows, inputs)
ACCENT = "#3D7EFF"         # primary accent (buttons, active states)
ACCENT_SOFT = "#26314D"

TEXT_PRIMARY = "#F2F2F3"
TEXT_SECONDARY = "#9A9DA3"
DIVIDER = "#2A2C30"

STATUS_GREEN = "#3DDC84"
STATUS_YELLOW = "#F5C242"
STATUS_RED = "#F0503C"


def status_color(remaining_km):
    if remaining_km is None:
        return TEXT_SECONDARY
    if remaining_km <= 0:
        return STATUS_RED
    if remaining_km <= 1000:
        return STATUS_YELLOW
    return STATUS_GREEN


def hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return [r, g, b, alpha]
