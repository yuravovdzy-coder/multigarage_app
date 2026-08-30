"""
screens/reminders.py
Replacement-interval tracking with default + custom items.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

import database as db
import theme
from screens.common import today

KV = """
<RemindersScreen>:
    name: "reminders"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Нагадування"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("car_menu")]]
            right_action_items: [["plus", lambda x: root.open_add_reminder()]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        ScrollView:
            MDList:
                id: reminders_list
"""

Builder.load_string(KV)


class RemindersScreen(Screen):
    def on_pre_enter(self, *args):
        self.reload()

    def reload(self):
        box = self.ids.reminders_list
        box.clear_widgets()
        car = db.get_car(self._app().current_car_id)
        if not car:
            return
        for rem in db.get_reminders(car["id"]):
            remaining = db.compute_remaining_km(rem, car["odometer"])
            remaining_text = f"{remaining:,} км".replace(",", " ") if remaining is not None else "—"
            item = TwoLineAvatarIconListItem(
                text=rem["name"],
                secondary_text=f"Залишилось: {remaining_text}",
            )
            item.add_widget(IconLeftWidget(icon="bell-outline"))
            check = IconRightWidget(icon="check-circle-outline")
            check.bind(on_release=lambda x, r=rem: self._mark_done(r))
            item.add_widget(check)
            box.add_widget(item)

    def _mark_done(self, reminder):
        car = db.get_car(self._app().current_car_id)
        db.mark_reminder_done(reminder["id"], car["odometer"])
        self.reload()

    def open_add_reminder(self):
        content = MDBoxLayout(orientation="vertical", spacing="8dp",
                               size_hint_y=None, height="160dp")
        name = MDTextField(hint_text="Назва (напр. Заміна фільтра салону)")
        interval_km = MDTextField(hint_text="Інтервал, км", input_filter="int")
        content.add_widget(name)
        content.add_widget(interval_km)

        def save(*_):
            car = db.get_car(self._app().current_car_id)
            db.add_reminder(car["id"], name.text, int(interval_km.text or 0),
                             last_done_odometer=car["odometer"], last_done_date=today(),
                             is_custom=1)
            dialog.dismiss()
            self.reload()

        dialog = MDDialog(
            title="Власне нагадування",
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
