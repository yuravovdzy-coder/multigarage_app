"""
main.py
Multi-Garage & Auto Care Assistant
App entry point: sets up the dark-graphite theme, registers every
screen, and runs the periodic "maintenance due" notification check.

Run inside Pydroid 3:
    pip install kivy kivymd pillow
    python main.py
(pytesseract is optional — see ocr_engine.py for details.)
"""

import os
from kivy.config import Config

Config.set("graphics", "width", "400")
Config.set("graphics", "height", "800")

from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp

import database as db
import theme
from screens.splash import SplashScreen
from screens.dashboard import DashboardScreen
from screens.car_menu import CarMenuScreen
from screens.garage import GarageScreen
from screens.maintenance import MaintenanceScreen
from screens.reminders import RemindersScreen
from screens.fuel import FuelScreen
from screens.expenses import ExpensesScreen
from screens.analytics import AnalyticsScreen
from screens.settings import SettingsScreen
from screens.add_car import AddCarScreen

Window.clearcolor = theme.hex_to_rgba(theme.BG_ROOT)


class GarageApp(MDApp):
    current_car_id = None

    def build(self):
        db.init_db()

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"

        self.theme_colors = {
            "root": theme.hex_to_rgba(theme.BG_ROOT),
            "card": theme.hex_to_rgba(theme.BG_CARD),
            "card_alt": theme.hex_to_rgba(theme.BG_CARD_ALT),
            "accent": theme.hex_to_rgba(theme.ACCENT),
            "text_primary": theme.hex_to_rgba(theme.TEXT_PRIMARY),
            "text_secondary": theme.hex_to_rgba(theme.TEXT_SECONDARY),
        }

        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(SplashScreen())
        sm.add_widget(DashboardScreen())
        sm.add_widget(CarMenuScreen())
        sm.add_widget(GarageScreen())
        sm.add_widget(MaintenanceScreen())
        sm.add_widget(RemindersScreen())
        sm.add_widget(FuelScreen())
        sm.add_widget(ExpensesScreen())
        sm.add_widget(AnalyticsScreen())
        sm.add_widget(SettingsScreen())
        sm.add_widget(AddCarScreen())
        return sm

    def switch_screen(self, name, direction="left"):
        self.root.transition.direction = direction
        self.root.current = name

    def on_start(self):
        self._check_due_reminders()

    def _check_due_reminders(self):
        """Simple in-app due-check; runs once on launch. System push
        notifications need plyer.notification wired to the OS scheduler,
        which is a per-platform build step outside Pydroid 3's scope."""
        if db.get_setting("notifications", "1") != "1":
            return
        for car in db.get_cars():
            for rem in db.get_reminders(car["id"]):
                remaining = db.compute_remaining_km(rem, car["odometer"])
                if remaining is not None and remaining <= 0:
                    try:
                        from plyer import notification
                        notification.notify(
                            title=f"{car['make']} {car['model']}",
                            message=f"Пора замінити: {rem['name']}",
                            timeout=5,
                        )
                    except Exception:
                        pass  # plyer/OS notification backend not available


if __name__ == "__main__":
    GarageApp().run()
