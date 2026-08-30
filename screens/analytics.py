"""
screens/analytics.py
Monthly financial breakdown across maintenance, fuel and small expenses,
plus cost-per-km.
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

import database as db
import theme

KV = """
<AnalyticsScreen>:
    name: "analytics"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        MDTopAppBar:
            title: "Аналітика"
            left_action_items: [["arrow-left", lambda x: app.switch_screen("car_menu")]]
            md_bg_color: app.theme_colors["card"]
            specific_text_color: app.theme_colors["text_primary"]

        ScrollView:
            MDBoxLayout:
                id: months_box
                orientation: "vertical"
                adaptive_height: True
                padding: "16dp"
                spacing: "12dp"
"""

Builder.load_string(KV)


class AnalyticsScreen(Screen):
    def on_pre_enter(self, *args):
        self.reload()

    def reload(self):
        box = self.ids.months_box
        box.clear_widgets()
        car_id = self._app().current_car_id
        for month in db.get_monthly_summary(car_id):
            box.add_widget(self._build_month_card(month))

    def _build_month_card(self, m):
        card = MDCard(orientation="vertical", padding="14dp", spacing="4dp",
                       size_hint_y=None, radius=[18, 18, 18, 18],
                       md_bg_color=theme.hex_to_rgba(theme.BG_CARD))
        card.bind(minimum_height=card.setter("height"))

        card.add_widget(MDLabel(text=m["month"], bold=True, font_style="H6",
                                 theme_text_color="Custom",
                                 text_color=theme.hex_to_rgba(theme.TEXT_PRIMARY),
                                 size_hint_y=None, height="32dp"))
        for label, key in (("ТО", "maintenance"), ("Пальне", "fuel"), ("Витрати", "expenses")):
            card.add_widget(MDLabel(
                text=f"{label}: {m[key]:.0f}",
                theme_text_color="Custom", text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY),
                size_hint_y=None, height="22dp", font_style="Caption"))

        cost_per_km = f"{m['cost_per_km']:.2f}" if m["cost_per_km"] else "н/д"
        card.add_widget(MDLabel(
            text=f"Разом: {m['total']:.0f}  ·  {cost_per_km}/км",
            bold=True, theme_text_color="Custom", text_color=theme.hex_to_rgba(theme.ACCENT),
            size_hint_y=None, height="28dp"))
        return card

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
