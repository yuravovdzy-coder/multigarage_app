"""
screens/add_car.py
Form for adding a new vehicle to the multi-garage.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

import database as db

KV = """
<AddCarScreen>:
    name: "add_car"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Нове авто"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("dashboard")]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: "24dp"
                spacing: "16dp"

                MDTextField:
                    id: make
                    hint_text: "Марка (напр. Volvo)"
                MDTextField:
                    id: model
                    hint_text: "Модель (напр. XC60)"
                MDTextField:
                    id: year
                    hint_text: "Рік випуску"
                    input_filter: "int"
                MDTextField:
                    id: odometer
                    hint_text: "Поточний пробіг, км"
                    input_filter: "int"
                MDRaisedButton:
                    text: "Зберегти авто"
                    pos_hint: {"center_x": 0.5}
                    on_release: root.save_car()
"""

Builder.load_string(KV)


class AddCarScreen(Screen):
    def save_car(self):
        make = self.ids.make.text.strip()
        model = self.ids.model.text.strip()
        if not make or not model:
            return
        year = int(self.ids.year.text or 0)
        odometer = int(self.ids.odometer.text or 0)
        db.add_car(make, model, year, odometer=odometer)

        for f in ("make", "model", "year", "odometer"):
            self.ids[f].text = ""

        app = self._app()
        app.switch_screen("dashboard")
        dash = app.root.get_screen("dashboard")
        dash.reload_cars()

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
