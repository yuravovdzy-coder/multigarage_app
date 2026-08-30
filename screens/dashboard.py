"""
screens/dashboard.py
Main screen: digital clock/date top bar, swipeable car carousel,
oil-life progress widget, horizontal reminder strip.
"""

import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.filemanager import MDFileManager

import database as db
import theme

KV = """
<CarCard@MDCard>:
    orientation: "vertical"
    radius: [24, 24, 24, 24]
    md_bg_color: app.theme_colors["card"]
    padding: 0

<DashboardScreen>:
    name: "dashboard"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            padding: "12dp", "4dp"
            MDBoxLayout:
                orientation: "vertical"
                MDLabel:
                    id: clock_label
                    text: root.clock_text
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: app.theme_colors["text_primary"]
                MDLabel:
                    id: date_label
                    text: root.date_text
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: app.theme_colors["text_secondary"]
            MDIconButton:
                icon: "cog"
                theme_text_color: "Custom"
                text_color: app.theme_colors["text_primary"]
                on_release: app.switch_screen("settings")

        ScreenManager:
            id: car_carousel
            size_hint_y: 0.72

        MDBoxLayout:
            id: reminder_strip
            size_hint_y: None
            height: "48dp"
            padding: "8dp", "0dp"
            spacing: "8dp"
"""

Builder.load_string(KV)


class DashboardScreen(Screen):
    clock_text = StringProperty("")
    date_text = StringProperty("")
    active_car_id = NumericProperty(0)

    def on_pre_enter(self, *args):
        self._tick(0)
        self._clock_ev = Clock.schedule_interval(self._tick, 1)
        self.reload_cars()

    def on_leave(self, *args):
        if hasattr(self, "_clock_ev"):
            self._clock_ev.cancel()

    def _tick(self, dt):
        now = datetime.datetime.now()
        self.clock_text = now.strftime("%H:%M")
        self.date_text = now.strftime("%d %B %Y")

    # ------------------------------------------------------------ cars

    def reload_cars(self):
        from screens.car_card import build_car_slide, build_add_car_slide

        carousel = self.ids.car_carousel
        carousel.clear_widgets()
        cars = db.get_cars()
        for car in cars:
            slide = build_car_slide(car, self)
            carousel.add_widget(slide)
        carousel.add_widget(build_add_car_slide(self))

        if cars:
            self.active_car_id = cars[0]["id"]
            carousel.current = f"car_{cars[0]['id']}"
        self.refresh_reminder_strip()

    def open_car(self, car_id):
        self.active_car_id = car_id
        app = self._app()
        app.current_car_id = car_id
        app.switch_screen("car_menu")

    def next_car(self):
        self.ids.car_carousel.transition.direction = "left"
        self._shift_car(1)

    def prev_car(self):
        self.ids.car_carousel.transition.direction = "right"
        self._shift_car(-1)

    def _shift_car(self, direction):
        cars = db.get_cars()
        if not cars:
            return
        ids = [c["id"] for c in cars]
        if self.active_car_id not in ids:
            idx = 0
        else:
            idx = ids.index(self.active_car_id)
        idx = (idx + direction) % len(ids)
        self.active_car_id = ids[idx]
        self.ids.car_carousel.current = f"car_{ids[idx]}"

    def refresh_reminder_strip(self):
        strip = self.ids.reminder_strip
        strip.clear_widgets()
        if not self.active_car_id:
            return
        from kivymd.uix.label import MDLabel
        from kivymd.uix.card import MDCard

        car = db.get_car(self.active_car_id)
        if not car:
            return
        for rem in db.get_reminders(self.active_car_id):
            remaining = db.compute_remaining_km(rem, car["odometer"])
            if remaining is None:
                continue
            card = MDCard(
                size_hint=(None, None),
                size=("160dp", "40dp"),
                radius=[12, 12, 12, 12],
                md_bg_color=theme.hex_to_rgba(theme.BG_CARD_ALT),
                padding="8dp",
            )
            lbl = MDLabel(
                text=f"{rem['name']}: {remaining} км",
                theme_text_color="Custom",
                text_color=theme.hex_to_rgba(theme.status_color(remaining)),
                font_style="Caption",
            )
            card.add_widget(lbl)
            strip.add_widget(card)

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
