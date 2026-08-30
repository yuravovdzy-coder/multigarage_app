"""
screens/fuel.py
Fuel log with instant L/100km calculation and monthly summaries.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel

import database as db
from screens.common import make_photo_button, today

KV = """
<FuelScreen>:
    name: "fuel"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Пальне"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("car_menu")]]
            right_action_items: [["plus", lambda x: root.open_add_fuel()]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        MDBoxLayout:
            id: monthly_box
            size_hint_y: None
            height: "56dp"
            padding: "12dp", "8dp"

        ScrollView:
            MDList:
                id: fuel_list
"""

Builder.load_string(KV)


class FuelScreen(Screen):
    def on_pre_enter(self, *args):
        self.reload()

    def reload(self):
        car_id = self._app().current_car_id
        logs = db.get_fuel_logs(car_id)

        box = self.ids.fuel_list
        box.clear_widgets()
        for log in logs:
            avg = f"{log['avg_consumption']} л/100км" if log["avg_consumption"] else "н/д"
            item = TwoLineIconListItem(
                text=f"{log['date']} — {log['liters']} л — {log['amount']} грн",
                secondary_text=f"{log['odometer']:,} км · {avg}".replace(",", " "),
            )
            item.add_widget(IconLeftWidget(icon="gas-station-outline"))
            box.add_widget(item)

        self.ids.monthly_box.clear_widgets()
        if logs:
            this_month = logs[0]["date"][:7]
            month_logs = [l for l in logs if l["date"][:7] == this_month]
            avgs = [l["avg_consumption"] for l in month_logs if l["avg_consumption"]]
            total_cost = sum(l["amount"] or 0 for l in month_logs)
            avg_txt = f"{sum(avgs)/len(avgs):.1f} л/100км" if avgs else "—"
            self.ids.monthly_box.add_widget(MDLabel(
                text=f"Цей місяць: {total_cost:.0f} грн, середнє {avg_txt}",
                theme_text_color="Custom", text_color=self._app().theme_colors["text_secondary"]))

    def open_add_fuel(self):
        content = MDBoxLayout(orientation="vertical", spacing="8dp",
                               size_hint_y=None, height="280dp")
        odometer = MDTextField(hint_text="Пробіг, км", input_filter="int")
        amount = MDTextField(hint_text="Сума, грн", input_filter="float")
        liters = MDTextField(hint_text="Літри", input_filter="float")
        full_row = MDBoxLayout(size_hint_y=None, height="40dp")
        full_check = MDCheckbox(active=True, size_hint=(None, None), size=("40dp", "40dp"))
        full_row.add_widget(full_check)
        full_row.add_widget(MDLabel(text="Повний бак"))
        photo_row = MDBoxLayout(size_hint_y=None, height="48dp")
        state = {"photo_path": ""}

        def on_photo(parsed, path):
            state["photo_path"] = path
            if parsed.get("amount") and not amount.text:
                amount.text = str(parsed["amount"])
            if parsed.get("odometer") and not odometer.text:
                odometer.text = str(parsed["odometer"])

        photo_row.add_widget(make_photo_button(on_photo))

        for w in (odometer, amount, liters, full_row, photo_row):
            content.add_widget(w)

        def save(*_):
            car_id = self._app().current_car_id
            db.add_fuel_log(
                car_id, today(), int(odometer.text or 0), float(amount.text or 0),
                float(liters.text or 0), 1 if full_check.active else 0, state["photo_path"])
            dialog.dismiss()
            self.reload()

        dialog = MDDialog(
            title="Заправка",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Скасувати", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="Зберегти", on_release=save),
            ],
        )
        dialog.open()

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
