"""
screens/settings.py
5-item settings screen: language, units, currency, notifications, backup.
"""

import os
import shutil
import datetime
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import (OneLineAvatarIconListItem, IconLeftWidget,
                              TwoLineAvatarIconListItem)
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.filemanager import MDFileManager

import database as db

KV = """
<SettingsScreen>:
    name: "settings"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Налаштування"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("dashboard")]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        MDList:
            id: settings_list
"""

Builder.load_string(KV)

LANGUAGES = ["uk", "en"]
UNITS_DISTANCE = ["km", "mi"]
UNITS_FUEL = ["l", "gal"]
UNITS_CONSUMPTION = ["l100", "mpg"]
CURRENCIES = ["UAH", "USD", "EUR"]


class SettingsScreen(Screen):
    def on_pre_enter(self, *args):
        self.reload()

    def reload(self):
        box = self.ids.settings_list
        box.clear_widgets()

        box.add_widget(self._cycle_item(
            "translate", "Мова", "language", LANGUAGES))
        box.add_widget(self._cycle_item(
            "map-marker-distance", "Одиниці відстані", "unit_distance", UNITS_DISTANCE))
        box.add_widget(self._cycle_item(
            "gas-station", "Одиниці пального", "unit_fuel", UNITS_FUEL))
        box.add_widget(self._cycle_item(
            "chart-bell-curve", "Одиниці витрати", "unit_consumption", UNITS_CONSUMPTION))
        box.add_widget(self._cycle_item(
            "cash", "Валюта", "currency", CURRENCIES))
        box.add_widget(self._notification_item())
        box.add_widget(self._backup_item())
        box.add_widget(self._restore_item())

    def _cycle_item(self, icon, title, key, options):
        current = db.get_setting(key, options[0])
        item = TwoLineAvatarIconListItem(text=title, secondary_text=current)
        item.add_widget(IconLeftWidget(icon=icon))

        def cycle(*_):
            idx = (options.index(db.get_setting(key, options[0])) + 1) % len(options)
            db.set_setting(key, options[idx])
            self.reload()

        item.bind(on_release=cycle)
        return item

    def _notification_item(self):
        enabled = db.get_setting("notifications", "1") == "1"
        item = OneLineAvatarIconListItem(text="Сповіщення про ТО")
        item.add_widget(IconLeftWidget(icon="bell-outline"))
        switch = MDSwitch(active=enabled, pos_hint={"center_y": 0.5})

        def toggle(instance, value):
            db.set_setting("notifications", "1" if value else "0")

        switch.bind(active=toggle)
        item.add_widget(switch)
        return item

    def _backup_item(self):
        item = OneLineAvatarIconListItem(text="Резервне копіювання (експорт)")
        item.add_widget(IconLeftWidget(icon="cloud-upload-outline"))
        item.bind(on_release=lambda x: self._export_db())
        return item

    def _restore_item(self):
        item = OneLineAvatarIconListItem(text="Відновлення з файлу (імпорт)")
        item.add_widget(IconLeftWidget(icon="cloud-download-outline"))
        item.bind(on_release=lambda x: self._import_db())
        return item

    def _export_db(self):
        dest_dir = os.path.expanduser("~")
        dest = os.path.join(
            dest_dir, f"garage_backup_{datetime.datetime.now():%Y%m%d_%H%M%S}.db")
        try:
            shutil.copy(db.DB_PATH, dest)
            Snackbar(text=f"Збережено: {dest}").open()
        except Exception as e:
            Snackbar(text=f"Помилка експорту: {e}").open()

    def _import_db(self):
        def select_path(path):
            manager.close()
            try:
                shutil.copy(path, db.DB_PATH)
                Snackbar(text="Базу даних відновлено. Перезапустіть додаток.").open()
            except Exception as e:
                Snackbar(text=f"Помилка імпорту: {e}").open()

        def exit_manager(*args):
            manager.close()

        manager = MDFileManager(exit_manager=exit_manager, select_path=select_path,
                                 ext=[".db"])
        manager.show(os.path.expanduser("~"))
