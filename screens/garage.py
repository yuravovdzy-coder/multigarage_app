"""
screens/garage.py
Vehicle passport: specs + fluid/part recommendations + modification log.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

import database as db
from screens.common import make_photo_button, today

KV = """
<GarageScreen>:
    name: "garage"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Гараж"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("car_menu")]]
            right_action_items: [["pencil", lambda x: root.edit_specs()]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: "16dp"
                spacing: "12dp"

                MDCard:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "8dp"
                    size_hint_y: None
                    height: "180dp"
                    radius: [20, 20, 20, 20]
                    md_bg_color: app.theme_colors["card"]
                    MDLabel:
                        text: "Технічні характеристики"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: app.theme_colors["text_primary"]
                    MDLabel:
                        id: specs_label
                        text: root.specs_text
                        theme_text_color: "Custom"
                        text_color: app.theme_colors["text_secondary"]

                MDBoxLayout:
                    size_hint_y: None
                    height: "40dp"
                    MDLabel:
                        text: "Історія модифікацій"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: app.theme_colors["text_primary"]
                    MDIconButton:
                        icon: "plus"
                        theme_text_color: "Custom"
                        text_color: app.theme_colors["accent"]
                        on_release: root.open_add_mod()

                MDBoxLayout:
                    id: mods_list
                    orientation: "vertical"
                    adaptive_height: True
                    spacing: "8dp"
"""

Builder.load_string(KV)


class GarageScreen(Screen):
    specs_text = ""

    def on_pre_enter(self, *args):
        self.reload()

    def reload(self):
        car = db.get_car(self._app().current_car_id)
        if not car:
            return
        self.specs_text = (
            f"Двигун: {car['engine_code'] or '-'} ({car['engine_size'] or '-'})\n"
            f"Олива: {car['oil_spec'] or '-'}\n"
            f"Паливо: {car['fuel_type'] or '-'}"
        )
        self.ids.specs_label.text = self.specs_text
        self._reload_mods(car["id"])

    def _reload_mods(self, car_id):
        box = self.ids.mods_list
        box.clear_widgets()
        for mod in db.get_mods(car_id):
            item = OneLineAvatarIconListItem(text=f"{mod['date']} — {mod['description']}")
            item.add_widget(IconLeftWidget(icon="palette-outline"))
            box.add_widget(item)

    def open_add_mod(self):
        content = MDBoxLayout(orientation="vertical", spacing="8dp",
                               size_hint_y=None, height="220dp")
        category = MDTextField(hint_text="Категорія (фарба/салон/обвіс/аксесуар)")
        desc = MDTextField(hint_text="Опис")
        photo_row = MDBoxLayout(size_hint_y=None, height="48dp")
        state = {"photo_path": ""}

        def on_photo(parsed, path):
            state["photo_path"] = path

        photo_row.add_widget(make_photo_button(on_photo))
        content.add_widget(category)
        content.add_widget(desc)
        content.add_widget(photo_row)

        def save(*_):
            db.add_mod(self._app().current_car_id, today(), category.text, desc.text,
                       state["photo_path"])
            dialog.dismiss()
            self._reload_mods(self._app().current_car_id)

        dialog = MDDialog(
            title="Нова модифікація",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Скасувати", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="Зберегти", on_release=save),
            ],
        )
        dialog.open()

    def edit_specs(self):
        car = db.get_car(self._app().current_car_id)
        content = MDBoxLayout(orientation="vertical", spacing="8dp",
                               size_hint_y=None, height="260dp")
        engine_code = MDTextField(hint_text="Код двигуна", text=car["engine_code"] or "")
        engine_size = MDTextField(hint_text="Об'єм двигуна", text=car["engine_size"] or "")
        oil_spec = MDTextField(hint_text="Специфікація оливи", text=car["oil_spec"] or "")
        fuel_type = MDTextField(hint_text="Тип пального", text=car["fuel_type"] or "")
        for w in (engine_code, engine_size, oil_spec, fuel_type):
            content.add_widget(w)

        def save(*_):
            db.update_car(car["id"], engine_code=engine_code.text, engine_size=engine_size.text,
                           oil_spec=oil_spec.text, fuel_type=fuel_type.text)
            dialog.dismiss()
            self.reload()

        dialog = MDDialog(
            title="Редагувати характеристики",
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
