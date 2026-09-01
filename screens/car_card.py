"""
screens/car_card.py
Factory functions that build one carousel "page" per car for the
Dashboard's inner ScreenManager.
"""

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.fitimage import FitImage
from kivy.metrics import dp

import database as db
import theme

DEFAULT_CAR_IMAGE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "default_car.png",
)

LONG_PRESS_SECONDS = 0.6


class LongPressFitImage(ButtonBehavior, FitImage):
    """FitImage з підтримкою короткого та довгого натискання."""

    def __init__(self, on_tap=None, on_long_press=None, **kwargs):
        super().__init__(**kwargs)
        self._on_tap = on_tap
        self._on_long_press = on_long_press
        self._press_ev = None
        self._long_fired = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._long_fired = False
            self._press_ev = Clock.schedule_once(self._fire_long_press, LONG_PRESS_SECONDS)
        return super().on_touch_down(touch)

    def _fire_long_press(self, dt):
        self._long_fired = True
        if self._on_long_press:
            self._on_long_press()

    def on_touch_up(self, touch):
        if self._press_ev:
            self._press_ev.cancel()
        if self.collide_point(*touch.pos) and not self._long_fired and self._on_tap:
            self._on_tap()
        return super().on_touch_up(touch)


def _oil_reminder(car):
    for rem in db.get_reminders(car["id"]):
        if "олив" in rem["name"].lower() or "oil" in rem["name"].lower():
            return rem
    return None


def build_car_slide(car, dashboard_screen):
    screen = Screen(name=f"car_{car['id']}")
    root = MDFloatLayout(md_bg_color=theme.hex_to_rgba(theme.BG_ROOT))

    card_radius = [28, 28, 28, 28]

    # MDCard як головний контейнер
    card = MDCard(
        radius=card_radius,
        md_bg_color=theme.hex_to_rgba(theme.BG_CARD),
        pos_hint={"center_x": 0.5, "center_y": 0.5},
        size_hint=(0.92, 0.96),
        padding=0,
    )

    inner = MDFloatLayout(
        size_hint=(1, 1),
        pos_hint={"center_x": 0.5, "center_y": 0.5},
    )

    image_source = car.get("image_path") or DEFAULT_CAR_IMAGE
    if not os.path.exists(image_source):
        image_source = DEFAULT_CAR_IMAGE

    # FitImage заповнює центральну частину картки без перекриття текстів
    img = LongPressFitImage(
        source=image_source,
        size_hint=(0.9, 0.6),
        pos_hint={"center_x": 0.5, "center_y": 0.5},
        radius=[16, 16, 16, 16],
        on_tap=lambda: dashboard_screen.open_car(car["id"]),
        on_long_press=lambda: _pick_new_image(car["id"], dashboard_screen),
    )
    inner.add_widget(img)

    # Верхній оверлей: Марка/Модель та Пробіг
    top_box = MDBoxLayout(
        orientation="vertical",
        size_hint=(1, None),
        height=dp(64),
        pos_hint={"top": 1},
        padding=(dp(16), dp(10)),
    )
    top_box.add_widget(MDLabel(
        text=f"{car['make']} {car['model']} ({car['year']})",
        theme_text_color="Custom",
        text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY),
        font_style="Caption",
    ))
    top_box.add_widget(MDLabel(
        text=f"{car['odometer']:,} км".replace(",", " "),
        theme_text_color="Custom",
        text_color=theme.hex_to_rgba(theme.TEXT_PRIMARY),
        font_style="H5",
        bold=True,
    ))
    inner.add_widget(top_box)

    # Нижній оверлей: стан оливи
    bottom_box = MDBoxLayout(
        orientation="vertical",
        size_hint=(1, None),
        height=dp(72),
        pos_hint={"y": 0},
        padding=(dp(16), dp(6)),
        spacing=dp(4),
    )
    oil = _oil_reminder(car)
    remaining = db.compute_remaining_km(oil, car["odometer"]) if oil else None
    interval = oil["interval_km"] if oil else 7000
    remaining_display = max(remaining, 0) if remaining is not None else interval
    ratio = 1 - (remaining_display / interval) if interval else 0
    ratio = min(max(ratio, 0), 1)

    bottom_box.add_widget(MDLabel(
        text=f"Моторна олива: залишилось {remaining_display:,} з {interval:,} км".replace(",", " "),
        theme_text_color="Custom",
        text_color=theme.hex_to_rgba(theme.status_color(remaining)),
        font_style="Caption",
    ))
    bar = MDProgressBar(value=ratio * 100, max=100, size_hint_y=None, height=dp(6))
    bar.color = theme.hex_to_rgba(theme.status_color(remaining))
    bottom_box.add_widget(bar)
    inner.add_widget(bottom_box)

    card.add_widget(inner)
    root.add_widget(card)
    screen.add_widget(root)
    return screen


def build_add_car_slide(dashboard_screen):
    screen = Screen(name="add_car_slide")
    root = MDFloatLayout(md_bg_color=theme.hex_to_rgba(theme.BG_ROOT))
    card = MDCard(
        radius=[28, 28, 28, 28],
        md_bg_color=theme.hex_to_rgba(theme.BG_CARD_ALT),
        pos_hint={"center_x": 0.5, "center_y": 0.5},
        size_hint=(0.92, 0.96),
        ripple_behavior=True,
        on_release=lambda *a: dashboard_screen._app().switch_screen("add_car"),
    )
    box = MDBoxLayout(
        orientation="vertical",
        pos_hint={"center_x": 0.5, "center_y": 0.5},
        size_hint=(None, None),
        size=(dp(120), dp(120)),
        spacing=dp(8),
    )
    from kivymd.uix.button import MDIconButton
    box.add_widget(MDIconButton(
        icon="plus-circle-outline",
        icon_size=dp(56),
        theme_text_color="Custom",
        text_color=theme.hex_to_rgba(theme.ACCENT),
        pos_hint={"center_x": 0.5},
    ))
    box.add_widget(MDLabel(
        text="Додати авто",
        halign="center",
        theme_text_color="Custom",
        text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY),
    ))
    card.add_widget(box)
    root.add_widget(card)
    screen.add_widget(root)
    return screen


def _pick_new_image(car_id, dashboard_screen):
    from kivymd.uix.filemanager import MDFileManager

    def select_path(path):
        db.update_car(car_id, image_path=path)
        manager.close()
        dashboard_screen.reload_cars()

    def exit_manager(*args):
        manager.close()

    manager = MDFileManager(
        exit_manager=exit_manager,
        select_path=select_path,
        ext=[".jpg", ".jpeg", ".png"],
    )
    manager.show(os.path.expanduser("~"))
