"""
screens/dashboard.py
Main screen: digital clock/date top bar, swipeable car carousel,
oil-life progress widget, horizontal reminder strip.
"""

import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.screenmanager import Screen

import database as db
import theme

KV = """
<DashboardScreen>:
    name: "dashboard"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]

        # Верхня панель (годинник, дата, налаштування)
        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            padding: ["12dp", "4dp"]
            
            MDBoxLayout:
                orientation: "vertical"
                MDLabel:
                    id: clock_label
                    text: root.clock_text
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: app.theme_colors["text_primary"]
                MDLabel:
                    id: date_label
                    text: root.date_text
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: app.theme_colors["text_secondary"]
            
            MDIconButton:
                icon: "cog"
                theme_text_color: "Custom"
                text_color: app.theme_colors["text_primary"]
                on_release: root.open_settings()

        # Карусель авто з підтримкою свайпів пальцем
        Carousel:
            id: car_carousel
            size_hint_y: 0.72
            direction: "right"
            loop: False

        # Стрічка нагадувань
        ScrollView:
            size_hint_y: None
            height: "52dp"
            do_scroll_y: False
            do_scroll_x: True
            
            MDBoxLayout:
                id: reminder_strip
                orientation: "horizontal"
                size_hint_x: None
                width: self.minimum_width
                padding: ["8dp", "4dp"]
                spacing: "8dp"
"""

Builder.load_string(KV)


class DashboardScreen(Screen):
    clock_text = StringProperty("")
    date_text = StringProperty("")
    active_car_id = NumericProperty(0)

    def on_pre_enter(self, *args):
        self._tick(0)
        self._clock_ev = Clock.schedule_interval(self._tick, 1)
        # Початкове заповнення даних до появи екрана
        self.reload_cars()

    def on_enter(self, *args):
        # Відкладений примусовий перерахунок розмірів каруселі після завершення анімації
        Clock.schedule_once(lambda dt: self._force_refresh(), 0.05)

    def on_leave(self, *args):
        if hasattr(self, "_clock_ev"):
            self._clock_ev.cancel()

    def _tick(self, dt):
        now = datetime.datetime.now()
        self.clock_text = now.strftime("%H:%M")
        self.date_text = now.strftime("%d %B %Y")

    def _force_refresh(self):
        carousel = self.ids.car_carousel
        carousel.do_layout()
        self.refresh_reminder_strip()

    def open_settings(self):
        """Безпечний перехід у налаштування."""
        app = self._app()
        if hasattr(app, "switch_screen"):
            app.switch_screen("settings", "left")

    # ------------------------------------------------------------ cars

    def reload_cars(self):
        try:
            from screens.car_card import build_car_slide, build_add_car_slide

            carousel = self.ids.car_carousel
            
            # Відв'язуємо слухач перед очищенням, щоб уникнути помилкових викликів
            carousel.unbind(index=self._on_carousel_slide_change)
            carousel.clear_widgets()
            
            cars = db.get_cars()
            
            # Додаємо слайд кожного існуючого авто
            for car in cars:
                slide = build_car_slide(car, self)
                carousel.add_widget(slide)
            
            # ЗАВЖДИ додаємо слайд "Додати авто" в кінець
            add_slide = build_add_car_slide(self)
            carousel.add_widget(add_slide)

            # Відновлюємо активний автомобіль
            if cars:
                if not self.active_car_id:
                    self.active_car_id = cars[0]["id"]
                
                # Знаходимо потрібний індекс слайда для збереження позиції
                target_index = 0
                for idx, car in enumerate(cars):
                    if car["id"] == self.active_car_id:
                        target_index = idx
                        break
                carousel.index = target_index
            
            # Повертаємо слухач події зміни слайда
            carousel.bind(index=self._on_carousel_slide_change)
            self.refresh_reminder_strip()
        except Exception as e:
            print(f"Error loading cars: {e}")

    def _on_carousel_slide_change(self, carousel, index):
        cars = db.get_cars()
        if index < len(cars):
            self.active_car_id = cars[index]["id"]
            app = self._app()
            app.current_car_id = self.active_car_id
            self.refresh_reminder_strip()

    def open_car(self, car_id):
        self.active_car_id = car_id
        app = self._app()
        app.current_car_id = car_id
        app.switch_screen("car_menu", "left")

    def refresh_reminder_strip(self):
        strip = self.ids.reminder_strip
        strip.clear_widgets()
        if not self.active_car_id:
            return
            
        from kivymd.uix.label import MDLabel
        from kivymd.uix.card import MDCard

        car = db.get_car(self.active_car_id)
        if not car:
            return
            
        for rem in db.get_reminders(self.active_car_id):
            # Пропускаємо нагадування про оливу в нижній стрічці, щоб воно не дублювалося з карткою
            if "олива" in rem['name'].lower() or "масло" in rem['name'].lower():
                continue

            remaining = db.compute_remaining_km(rem, car["odometer"])
            if remaining is None:
                continue
                
            if remaining <= 0:
                text_color_rgba = [1, 0.2, 0.2, 1]  # Червоний
                status_msg = f"{rem['name']}: УВАГА!"
            else:
                color_hex = theme.status_color(remaining) if hasattr(theme, "status_color") else theme.ACCENT
                text_color_rgba = theme.hex_to_rgba(color_hex)
                status_msg = f"{rem['name']}: {remaining} км"
                
            card = MDCard(
                size_hint=(None, None),
                size=("160dp", "40dp"),
                radius=[12, 12, 12, 12],
                md_bg_color=theme.hex_to_rgba(theme.BG_CARD_ALT),
                padding="8dp",
            )
            
            lbl = MDLabel(
                text=status_msg,
                theme_text_color="Custom",
                text_color=text_color_rgba,
                font_style="Caption",
            )
            card.add_widget(lbl)
            strip.add_widget(card)

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
