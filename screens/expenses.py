"""
screens/expenses.py
Micro-expense log: washer fluid, wipers, car wash, parking, etc.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

import database as db
from screens.common import make_photo_button, today

CATEGORY_ICONS = {
    "мийка": "car-wash", "паркування": "parking", "склоомивач": "spray-bottle",
    "щітки": "wiper-wash", "лампи": "lightbulb-outline",
}

KV = """
<ExpensesScreen>:
    name: "expenses"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Дрібні витрати"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("car_menu")]]
            right_action_items: [["plus", lambda x: root.open_add_expense()]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        ScrollView:
            MDList:
                id: expenses_list
"""

Builder.load_string(KV)


class ExpensesScreen(Screen):
    def on_pre_enter(self, *args):
        self.reload()

    def reload(self):
        box = self.ids.expenses_list
        box.clear_widgets()
        for exp in db.get_expenses(self._app().current_car_id):
            icon = CATEGORY_ICONS.get(exp["category"].lower(), "cart-outline")
            item = TwoLineIconListItem(
                text=f"{exp['category']} — {exp['amount']:.0f}",
                secondary_text=f"{exp['date']} · {exp['note'] or ''}",
            )
            item.add_widget(IconLeftWidget(icon=icon))
            box.add_widget(item)

    def open_add_expense(self):
        content = MDBoxLayout(orientation="vertical", spacing="8dp",
                               size_hint_y=None, height="240dp")
        category = MDTextField(hint_text="Категорія (мийка/склоомивач/щітки...)")
        amount = MDTextField(hint_text="Сума, грн", input_filter="float")
        note = MDTextField(hint_text="Примітка")
        photo_row = MDBoxLayout(size_hint_y=None, height="48dp")
        state = {"photo_path": ""}

        def on_photo(parsed, path):
            state["photo_path"] = path
            if parsed.get("amount") and not amount.text:
                amount.text = str(parsed["amount"])

        photo_row.add_widget(make_photo_button(on_photo))
        for w in (category, amount, note, photo_row):
            content.add_widget(w)

        def save(*_):
            db.add_expense(self._app().current_car_id, today(), category.text or "Інше",
                            float(amount.text or 0), note.text, state["photo_path"])
            dialog.dismiss()
            self.reload()

        dialog = MDDialog(
            title="Нова витрата",
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
