"""
screens/maintenance.py
Maintenance journal, grouped by service event, with nested part rows.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField

import database as db
import theme
from screens.common import make_photo_button, today

KV = """
<MaintenanceScreen>:
    name: "maintenance"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Журнал ТО"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("car_menu")]]
            right_action_items: [["plus", lambda x: root.open_add_event()]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        ScrollView:
            MDBoxLayout:
                id: events_box
                orientation: "vertical"
                adaptive_height: True
                padding: "16dp"
                spacing: "12dp"
"""

Builder.load_string(KV)


class MaintenanceScreen(Screen):
    def on_pre_enter(self, *args):
        self.reload()

    def reload(self):
        box = self.ids.events_box
        box.clear_widgets()
        car_id = self._app().current_car_id
        for ev in db.get_maintenance_events(car_id):
            box.add_widget(self._build_event_card(ev))

    def _build_event_card(self, ev):
        card = MDCard(orientation="vertical", padding="14dp", spacing="6dp",
                       size_hint_y=None, radius=[18, 18, 18, 18],
                       md_bg_color=theme.hex_to_rgba(theme.BG_CARD))
        card.bind(minimum_height=card.setter("height"))

        header = MDBoxLayout(size_hint_y=None, height="28dp")
        header.add_widget(MDLabel(
            text=f"{ev['title']} — {ev['odometer']:,} км".replace(",", " "),
            bold=True, theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.TEXT_PRIMARY)))
        header.add_widget(MDLabel(
            text=f"{ev['date']}", halign="right",
            theme_text_color="Custom", text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY)))
        card.add_widget(header)

        for item in ev["items"]:
            row = MDLabel(
                text=(f"• {item['part_name']} ({item['brand']}, {item['part_number']}) — "
                      f"{item['price']:.0f} + робота {item['labor_cost']:.0f}"),
                theme_text_color="Custom", text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY),
                size_hint_y=None, height="24dp", font_style="Caption")
            card.add_widget(row)

        total = MDLabel(text=f"Разом: {ev['total_cost']:.0f}", bold=True,
                         theme_text_color="Custom", text_color=theme.hex_to_rgba(theme.ACCENT),
                         size_hint_y=None, height="24dp")
        card.add_widget(total)
        return card

    def open_add_event(self):
        content = MDBoxLayout(orientation="vertical", spacing="8dp",
                               size_hint_y=None, height="440dp")
        title = MDTextField(hint_text="Назва події (напр. ТО №5)")
        odometer = MDTextField(hint_text="Пробіг, км", input_filter="int")
        part_name = MDTextField(hint_text="Деталь")
        brand = MDTextField(hint_text="Бренд")
        part_number = MDTextField(hint_text="Артикул")
        price = MDTextField(hint_text="Ціна деталі", input_filter="float")
        labor = MDTextField(hint_text="Вартість робіт", input_filter="float")
        photo_row = MDBoxLayout(size_hint_y=None, height="48dp")
        state = {"photo_path": ""}

        def on_photo(parsed, path):
            state["photo_path"] = path
            if parsed.get("amount") and not price.text:
                price.text = str(parsed["amount"])
            if parsed.get("odometer") and not odometer.text:
                odometer.text = str(parsed["odometer"])
            if parsed.get("part_number") and not part_number.text:
                part_number.text = parsed["part_number"]

        photo_row.add_widget(make_photo_button(on_photo))

        for w in (title, odometer, part_name, brand, part_number, price, labor, photo_row):
            content.add_widget(w)

        def save(*_):
            car_id = self._app().current_car_id
            event_id = db.add_maintenance_event(
                car_id, title.text or "ТО", today(),
                int(odometer.text or db.get_car(car_id)["odometer"]))
            if part_name.text:
                db.add_maintenance_item(
                    event_id, part_name.text, brand.text, part_number.text,
                    float(price.text or 0), float(labor.text or 0), state["photo_path"])
            dialog.dismiss()
            self.reload()

        dialog = MDDialog(
            title="Нова подія ТО",
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
