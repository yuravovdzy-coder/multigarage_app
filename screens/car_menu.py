"""
screens/car_menu.py
Full-screen car profile with 6 module tiles:
Garage (Passport), Maintenance, Reminders, Fuel, Small Expenses, Analytics.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivymd.uix.card import MDCard

import database as db

# --- РОЗДІЛ 1: KV-РОЗМІТКА МЕНЮ АВТО ---
KV = """
<ModuleTile>:
    orientation: "vertical"
    radius: [20, 20, 20, 20]
    md_bg_color: app.theme_colors["card"]
    padding: "12dp"
    ripple_behavior: True
    
    MDIconButton:
        icon: root.icon
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        theme_text_color: "Custom"
        text_color: app.theme_colors["accent"]
        icon_size: "36dp"
        disabled: True

    MDLabel:
        text: root.title_text
        halign: "center"
        theme_text_color: "Custom"
        text_color: app.theme_colors["text_primary"]
        font_style: "Subtitle2"
        bold: True

<CarMenuScreen>:
    name: "car_menu"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        # 1.1 Верхня панель навігації
        MDTopAppBar:
            title: root.car_title
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        # 1.2 Сітка 2x3 з 6 модульних плиток
        ScrollView:
            MDGridLayout:
                cols: 2
                padding: "16dp"
                spacing: "16dp"
                size_hint_y: None
                height: self.minimum_height

                ModuleTile:
                    icon: "car-cog"
                    title_text: "Гараж (Паспорт)"
                    size_hint_y: None
                    height: "120dp"
                    on_release: app.switch_screen("garage")

                ModuleTile:
                    icon: "wrench"
                    title_text: "Журнал ТО"
                    size_hint_y: None
                    height: "120dp"
                    on_release: app.switch_screen("maintenance")

                ModuleTile:
                    icon: "bell-ring-outline"
                    title_text: "Нагадування"
                    size_hint_y: None
                    height: "120dp"
                    on_release: app.switch_screen("reminders")

                ModuleTile:
                    icon: "gas-station"
                    title_text: "Пальне"
                    size_hint_y: None
                    height: "120dp"
                    on_release: app.switch_screen("fuel")

                ModuleTile:
                    icon: "cart-outline"
                    title_text: "Дрібні витрати"
                    size_hint_y: None
                    height: "120dp"
                    on_release: app.switch_screen("expenses")

                ModuleTile:
                    icon: "chart-line"
                    title_text: "Аналітика"
                    size_hint_y: None
                    height: "120dp"
                    on_release: app.switch_screen("analytics")
"""

Builder.load_string(KV)


# --- РОЗДІЛ 2: КЛАСИ ПЛИТКИ ТА ЕКРАНА ---
class ModuleTile(MDCard):
    icon = StringProperty("help")
    title_text = StringProperty("")


class CarMenuScreen(Screen):
    car_title = StringProperty("Авто")

    def on_pre_enter(self, *args):
        app = self._app()
        if app.current_car_id:
            car = db.get_car(app.current_car_id)
            if car:
                self.car_title = f"{car['make']} {car['model']}"
            else:
                self.car_title = "Авто"

    def go_back(self):
        """Штатне повернення на головний Дашборд."""
        self._app().switch_screen("dashboard")

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
