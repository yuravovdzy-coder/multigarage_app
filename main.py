"""
main.py
Multi-Garage & Auto Care Assistant
Головний блок управління (Central Gateway):
- Ініціалізація бази даних та графічної теми.
- Реєстрація всіх екранів додатка.
- Штатна обробка системної кнопки "Назад" та свайпів Android/iOS.
- Перевірка нагадувань про ТО при запуску.

Run inside Pydroid 3:
    pip install kivy kivymd pillow
    python main.py
"""

import os
from kivy.config import Config

# Налаштування розмірів вікна для тестування на ПК
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

# Встановлюємо графітовий колір фону вікна
Window.clearcolor = theme.hex_to_rgba(theme.BG_ROOT)


class GarageApp(MDApp):
    current_car_id = None

    def build(self):
        # 1. Ініціалізація бази даних (з перевіркою міграцій)
        db.init_db()

        # 2. Налаштування стилю KivyMD
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"

        # 3. Глобальна CAN-шина кольорів для всіх екранів
        self.theme_colors = {
            "root": theme.hex_to_rgba(theme.BG_ROOT),
            "card": theme.hex_to_rgba(theme.BG_CARD),
            "card_alt": theme.hex_to_rgba(theme.BG_CARD_ALT),
            "accent": theme.hex_to_rgba(theme.ACCENT),
            "accent_orange": theme.hex_to_rgba("#F58220"),
            "text_primary": theme.hex_to_rgba(theme.TEXT_PRIMARY),
            "text_secondary": theme.hex_to_rgba(theme.TEXT_SECONDARY),
            "status_green": theme.hex_to_rgba(theme.STATUS_GREEN),
            "status_yellow": theme.hex_to_rgba(theme.STATUS_YELLOW),
            "status_red": theme.hex_to_rgba(theme.STATUS_RED),
        }

        # 4. Реєстрація екранів у ScreenManager
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
        """Універсальний перемикач екранів з анімацією."""
        self.root.transition.direction = direction
        self.root.current = name

    def on_start(self):
        """Викликається одразу після запуску додатка."""
        # Прив'язуємо обробку системної кнопки "Назад" та жести смартфона
        Window.bind(on_keyboard=self.on_system_back_button)
        # Перевіряємо нагадування про регламентні роботи
        self._check_due_reminders()

    def on_system_back_button(self, window, key, *args):
        """
        Обробка системного сигналу повернення (Android keycode 27 / Esc на ПК).
        Працює аналогічно кнопці "Назад" та свайпам смартфона.
        """
        if key == 27:
            current = self.root.current
            # Якщо ми в меню або у внутрішньому розділі — повертаємося на Dashboard
            if current not in ["dashboard", "splash"]:
                self.switch_screen("dashboard", direction="right")
                return True  # Перехопили подію (не закриваємо додаток)
            elif current == "dashboard":
                # Якщо ми вже на Dashboard — дозволяємо згорнути додаток
                return False
        return False

    def _check_due_reminders(self):
        """Перевірка критичних термінів замін (олива, колодки тощо) при запуску."""
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
                            message=f"Увага! Пора замінити: {rem['name']}",
                            timeout=5,
                        )
                    except Exception:
                        pass  # Якщо Plyer недоступний на даній ОС


if __name__ == "__main__":
    GarageApp().run()
