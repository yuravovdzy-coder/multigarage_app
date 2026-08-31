"""
screens/car_card.py
Renders individual car slides for Dashboard Carousel.
"""

from kivy.uix.image import Image
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.progressbar import MDProgressBar

import theme
import database as db


def build_car_slide(car, dashboard_screen):
    """
    Створює картку автомобіля з зображенням на весь розмір слайда.
    """
    card = MDCard(
        orientation="vertical",
        padding=0,
        radius=[16, 16, 16, 16],
        md_bg_color=theme.hex_to_rgba(theme.BG_CARD),
        ripple_behavior=True,
        on_release=lambda x: dashboard_screen.open_car(car["id"])
    )

    # Макет-контейнер для накладання тексту поверх зображення
    from kivy.uix.relativelayout import RelativeLayout
    rel = RelativeLayout()

    # Зображення авто: розтягується чітко по контуру картки
    car_img = Image(
        source=car.get("image", "assets/images/volvo_xc60.jpg"),
        allow_stretch=True,
        keep_ratio=False,  # Заповнює весь квадрат/прямокутник картки
        size_hint=(1, 1),
        pos_hint={"x": 0, "y": 0}
    )
    rel.add_widget(car_img)

    # Оверлей із інформацією поверх картинки
    info_box = MDBoxLayout(
        orientation="vertical",
        padding=["16dp", "16dp", "16dp", "16dp"],
        spacing="4dp",
        pos_hint={"x": 0, "y": 0},
        size_hint=(1, 1)
    )

    # Заголовок (Марка/Модель)
    title_lbl = MDLabel(
        text=f"{car.get('make', '')} {car.get('model', '')} ({car.get('year', '')})",
        font_style="Subtitle1",
        theme_text_color="Custom",
        text_color=[1, 1, 1, 0.9],
        size_hint_y=None,
        height="24dp"
    )
    info_box.add_widget(title_lbl)

    # Пробіг
    odo_lbl = MDLabel(
        text=f"{car.get('odometer', 0):,} км".replace(",", " "),
        font_style="H4",
        bold=True,
        theme_text_color="Custom",
        text_color=[1, 1, 1, 1],
        size_hint_y=None,
        height="36dp"
    )
    info_box.add_widget(odo_lbl)

    # Заповнювач простору
    info_box.add_widget(MDBoxLayout())

    # Прогрес-бар оливи внизу картки
    reminders = db.get_reminders(car["id"])
    oil_rem = next((r for r in reminders if "олива" in r["name"].lower() or "масло" in r["name"].lower()), None)
    
    if oil_rem:
        rem_km = db.compute_remaining_km(oil_rem, car["odometer"]) or 0
        total_interval = oil_rem.get("interval_km", 10000)
        pct = max(0.0, min(1.0, rem_km / total_interval)) if total_interval else 0

        oil_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height="40dp",
            spacing="4dp"
        )
        oil_lbl = MDLabel(
            text=f"Моторна олива: залишилось {rem_km} з {total_interval} км",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=[0.4, 0.9, 0.4, 1] if rem_km > 1000 else [1, 0.3, 0.3, 1]
        )
        pb = MDProgressBar(
            value=pct * 100,
            color=[0.2, 0.8, 0.4, 1] if rem_km > 1000 else [0.9, 0.2, 0.2, 1],
            size_hint_y=None,
            height="4dp"
        )
        oil_box.add_widget(oil_lbl)
        oil_box.add_widget(pb)
        info_box.add_widget(oil_box)

    rel.add_widget(info_box)
    card.add_widget(rel)
    return card


def build_add_car_slide(dashboard_screen):
    """Слайд додавання нового авто."""
    card = MDCard(
        orientation="vertical",
        padding="16dp",
        radius=[16, 16, 16, 16],
        md_bg_color=theme.hex_to_rgba(theme.BG_CARD),
        ripple_behavior=True,
        on_release=lambda x: dashboard_screen._app().switch_screen("add_car", "left")
    )
    
    box = MDBoxLayout(
        orientation="vertical",
        halign="center",
        valign="center",
        spacing="12dp"
    )
    
    btn = MDIconButton(
        icon="plus-circle-outline",
        user_font_size="48dp",
        pos_hint={"center_x": 0.5},
        theme_text_color="Custom",
        text_color=theme.hex_to_rgba(theme.ACCENT)
    )
    lbl = MDLabel(
        text="Додати авто",
        halign="center",
        font_style="Headline6",
        theme_text_color="Custom",
        text_color=theme.hex_to_rgba(theme.TEXT_PRIMARY)
    )
    
    box.add_widget(btn)
    box.add_widget(lbl)
    card.add_widget(box)
    return card
