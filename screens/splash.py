"""
screens/splash.py
Startup splash screen — shows the branded artwork for a couple of
seconds, then hands off to the Dashboard.
"""

import os
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

SPLASH_SECONDS = 2.2

KV = """
<SplashScreen>:
    name: "splash"
    MDFloatLayout:
        md_bg_color: app.theme_colors["root"]
        Image:
            source: root.image_path
            allow_stretch: True
            keep_ratio: True
            size_hint: 0.9, 0.9
            pos_hint: {"center_x": 0.5, "center_y": 0.55}
        MDLabel:
            text: "Multi-Garage & Auto Care Assistant"
            halign: "center"
            theme_text_color: "Custom"
            text_color: app.theme_colors["text_secondary"]
            font_style: "Caption"
            size_hint_y: None
            height: "24dp"
            pos_hint: {"center_x": 0.5, "y": 0.06}
"""

Builder.load_string(KV)


class SplashScreen(Screen):
    image_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "default_car.png",
    )

    def on_enter(self, *args):
        Clock.schedule_once(self._go_to_dashboard, SPLASH_SECONDS)

    def _go_to_dashboard(self, dt):
        self.manager.transition.direction = "left"
        self.manager.current = "dashboard"

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
