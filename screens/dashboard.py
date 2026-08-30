"""
screens/dashboard.py
Головний екран (Дашборд):
- Плавна Карусель (Carousel) для гортання авто свайпами.
- Слайд-заглушка з картинкою, якщо гараж порожній.
- Останній слайд каруселі — завжди картка "+ Додати нове авто".
- Паспорт авто: Марка, Модель, VIN-код, Двигун (об'єм + модифікація), В'язкість оливи, Тип пального.
- Перехід в меню авто ТІЛЬКИ по кліку на конкретне авто.
- Нижня стрічка індикаторів на 2 рядки:
    * Верхній рядок: єдиний довгий блок для заміни оливи.
    * Нижній рядок: 3 рівні блоки для інших нагадувань.
"""

import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.carousel import Carousel
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton

import database as db
import theme

# --- РОЗДІЛ 1: KV-РОЗМІТКА ІНТЕРФЕЙСУ ---
KV = """
<DashboardScreen>:
    name: "dashboard"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_colors["root"]
        padding: "0dp", "0dp", "0dp", "8dp"

        # 1.1 Верхня панель (Годинник + Налаштування)
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            padding: "16dp", "4dp"
            MDBoxLayout:
                orientation: "vertical"
                MDLabel:
                    id: clock_label
                    text: root.clock_text
                    font_style: "H6"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: app.theme_colors["text_primary"]
                MDLabel:
                    id: date_label
                    text: root.date_text
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: app.theme_colors["text_secondary"]
            MDIconButton:
                icon: "cog-outline"
                theme_text_color: "Custom"
                text_color: app.theme_colors["text_primary"]
                on_release: app.switch_screen("settings")

        # 1.2 Головна Карусель Автомобілів (Підтримує свайпи ліворуч/праворуч)
        Carousel:
            id: car_carousel
            direction: "right"
            loop: False
            size_hint_y: 0.65
            on_index: root.on_carousel_slide_change(self.index)

        # 1.3 Нижня панель індикаторів нагадувань (2 чіткі рядки)
        MDBoxLayout:
            id: reminders_container
            orientation: "vertical"
            size_hint_y: None
            height: "110dp"
            padding: "12dp", "4dp"
            spacing: "6dp"

            # Верхній рядок: Довга картка для Оливи
            MDBoxLayout:
                id: row_oil
                size_hint_y: None
                height: "46dp"

            # Нижній рядок: 3 рівні картки для інших ТО
            MDBoxLayout:
                id: row_three_items
                size_hint_y: None
                height: "50dp"
                spacing: "6dp"
"""

Builder.load_string(KV)


# --- РОЗДІЛ 2: ЛОГІКА ДАШБОРДУ ---
class DashboardScreen(Screen):
    clock_text = StringProperty("")
    date_text = StringProperty("")
    active_car_id = NumericProperty(0)
    cars_list = []

    def on_pre_enter(self, *args):
        self._tick(0)
        self._clock_ev = Clock.schedule_interval(self._tick, 1)
        self.reload_cars()

    def on_leave(self, *args):
        if hasattr(self, "_clock_ev"):
            self._clock_ev.cancel()

    def _tick(self, dt):
        now = datetime.datetime.now()
        self.clock_text = now.strftime("%H:%M")
        self.date_text = now.strftime("%d %B %Y")

    # --- 2.1 ЗАВАНТАЖЕННЯ КАРУСЕЛІ ---
    def reload_cars(self):
        carousel = self.ids.car_carousel
        carousel.clear_widgets()
        self.cars_list = db.get_cars()

        if not self.cars_list:
            # Порожній гараж: Показуємо заставку
            carousel.add_widget(self._build_empty_garage_slide())
            self.active_car_id = 0
            self.refresh_reminders_two_rows()
            return

        # Додаємо картку для кожного наявного авто
        for car in self.cars_list:
            carousel.add_widget(self.build_custom_car_slide(car))

        # Завжди додаємо останнім слайдом картку "+ Додати авто"
        carousel.add_widget(self._build_add_new_car_slide())

        # Активуємо перше авто
        self.active_car_id = self.cars_list[0]["id"]
        carousel.index = 0
        self.refresh_reminders_two_rows()

    def on_carousel_slide_change(self, index):
        """Викликається при свайпі каруселі на новий слайд."""
        if not self.cars_list:
            return
        if index < len(self.cars_list):
            self.active_car_id = self.cars_list[index]["id"]
            self.refresh_reminders_two_rows()
        else:
            # Перейшли на слайд "+ Додати авто"
            self.active_car_id = 0
            self.clear_reminders_display()

    # --- 2.2 ПАСПОРТ ТА КАРТКА АВТО ---
    def build_custom_car_slide(self, car):
        from kivymd.uix.fitimage import FitImage

        # Створюємо картку авто. Натискання ТІЛЬКИ сюди відкриває меню цього авто
        main_card = MDCard(
            orientation="vertical",
            radius=[24, 24, 24, 24],
            md_bg_color=theme.hex_to_rgba(theme.BG_CARD),
            padding="12dp",
            spacing="6dp",
            size_hint=(0.92, 0.96),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            on_release=lambda x, c_id=car["id"]: self.open_car(c_id)
        )

        # 2.2.1 Картинка авто (60% висоти, відступи по 20%, fit_mode contain)
        img_container = MDBoxLayout(
            size_hint_y=0.6,
            padding=["0dp", "8dp", "0dp", "8dp"]
        )
        photo_path = car.get("image_path") or ""
        if photo_path and db.os.path.exists(photo_path):
            car_img = FitImage(source=photo_path, fit_mode="contain", radius=[16])
        else:
            car_img = FitImage(source="assets/car_placeholder.png", fit_mode="contain", radius=[16])
        img_container.add_widget(car_img)
        main_card.add_widget(img_container)

        # 2.2.2 Паспортні дані (Марка, Модель, Двигун, VIN, Пальне, Олива)
        info_box = MDBoxLayout(orientation="vertical", spacing="2dp", size_hint_y=0.4)

        # Марка та Модель (Рік)
        title_lbl = MDLabel(
            text=f"{car['make']} {car['model']} ({car['year']})",
            font_style="H6",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.TEXT_PRIMARY)
        )
        info_box.add_widget(title_lbl)

        # VIN-код
        vin_str = car.get("vin") or "VIN: Не вказано"
        vin_lbl = MDLabel(
            text=f"🔑 {vin_str}",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.ACCENT)
        )
        info_box.add_widget(vin_lbl)

        # Двигун (Об'єм + Модифікація)
        engine_val = f"{car.get('engine_size', '')} {car.get('engine_code', '')}".strip() or "Стандарт"
        eng_lbl = MDLabel(
            text=f"⚙️ Двигун: {engine_val}",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY)
        )
        info_box.add_widget(eng_lbl)

        # Тип пального та Специфікація оливи
        fuel_val = car.get("fuel_type") or "Бензин"
        oil_val = car.get("oil_spec") or "5W-30"
        spec_lbl = MDLabel(
            text=f"⛽ Пальне: {fuel_val}  |  🛢️ Олива: {oil_val}",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY)
        )
        info_box.add_widget(spec_lbl)

        # Одометр
        odo_lbl = MDLabel(
            text=f"⏱ {car['odometer']:,} км".replace(",", " "),
            font_style="Subtitle2",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.STATUS_GREEN)
        )
        info_box.add_widget(odo_lbl)

        main_card.add_widget(info_box)
        return main_card

    # --- 2.3 ПОРОЖНІЙ СЛАЙД ТА СЛАЙД ДОДАВАННЯ ---
    def _build_empty_garage_slide(self):
        """Заставка, коли в гаражі немає жодної машини."""
        from kivymd.uix.fitimage import FitImage

        card = MDCard(
            orientation="vertical",
            radius=[24],
            md_bg_color=theme.hex_to_rgba(theme.BG_CARD),
            padding="16dp",
            spacing="8dp",
            size_hint=(0.92, 0.96),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            on_release=lambda x: self._app().switch_screen("add_car")
        )
        img_box = MDBoxLayout(size_hint_y=0.65)
        img_box.add_widget(FitImage(
            source="assets/car_placeholder.png",
            fit_mode="contain",
            radius=[16]
        ))
        card.add_widget(img_box)

        card.add_widget(MDLabel(
            text="Гараж порожній",
            font_style="H6",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.TEXT_PRIMARY)
        ))
        card.add_widget(MDLabel(
            text="Торкніться сюди, щоб додати перше авто",
            font_style="Caption",
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.TEXT_SECONDARY)
        ))
        return card

    def _build_add_new_car_slide(self):
        """Запасний слайд у каруселі для швидкого додавання авто."""
        card = MDCard(
            orientation="vertical",
            radius=[24],
            md_bg_color=theme.hex_to_rgba(theme.BG_CARD_ALT),
            padding="24dp",
            spacing="12dp",
            size_hint=(0.92, 0.96),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            on_release=lambda x: self._app().switch_screen("add_car")
        )
        btn = MDIconButton(
            icon="plus-circle-outline",
            user_font_size="64sp",
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.ACCENT),
            on_release=lambda x: self._app().switch_screen("add_car")
        )
        card.add_widget(btn)
        card.add_widget(MDLabel(
            text="Додати нове авто",
            font_style="Subtitle1",
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=theme.hex_to_rgba(theme.TEXT_PRIMARY)
        ))
        return card

    # --- 2.4 СТРІЧКА НАГАДУВАНЬ У 2 РЯДКИ ---
    def refresh_reminders_two_rows(self):
        """Заповнює 2 рядки нагадувань під каруселлю."""
        row_oil = self.ids.row_oil
        row_three = self.ids.row_three_items

        row_oil.clear_widgets()
        row_three.clear_widgets()

        if not self.active_car_id:
            return

        car = db.get_car(self.active_car_id)
        if not car:
            return

        reminders = db.get_reminders(self.active_car_id)
        
        # 1. Пошук нагадування про оливу
        oil_rem = None
        other_rems = []
        for r in reminders:
            if "олива" in r["name"].lower() or "масл" in r["name"].lower():
                if not oil_rem:
                    oil_rem = r
                    continue
            other_rems.append(r)

        # --- 2.4.1 ВЕРХНІЙ РЯДОК (Заміна оливи — на весь екран) ---
        if oil_rem:
            rem_km = db.compute_remaining_km(oil_rem, car["odometer"])
            card_oil = MDCard(
                size_hint=(1, 1),
                radius=[12],
                md_bg_color=theme.hex_to_rgba(theme.BG_CARD_ALT),
                padding=["12dp", "4dp"]
            )
            lbl_oil = MDLabel(
                text=f"🛢️ {oil_rem['name']}: залишилось {rem_km} км",
                font_style="Caption",
                bold=True,
                halign="center",
                theme_text_color="Custom",
                text_color=theme.hex_to_rgba(theme.status_color(rem_km))
            )
            card_oil.add_widget(lbl_oil)
            row_oil.add_widget(card_oil)

        # --- 2.4.2 НИЖНІЙ РЯДОК (3 рівні блоки) ---
        three_items = other_rems[:3]
        for rem in three_items:
            rem_km = db.compute_remaining_km(rem, car["odometer"])
            card_sub = MDCard(
                size_hint=(0.33, 1),
                radius=[10],
                md_bg_color=theme.hex_to_rgba(theme.BG_CARD_ALT),
                padding=["4dp", "2dp"]
            )
            lbl_sub = MDLabel(
                text=f"{rem['name']}\n{rem_km} км",
                font_style="Overline",
                bold=True,
                halign="center",
                theme_text_color="Custom",
                text_color=theme.hex_to_rgba(theme.status_color(rem_km))
            )
            card_sub.add_widget(lbl_sub)
            row_three.add_widget(card_sub)

    def clear_reminders_display(self):
        self.ids.row_oil.clear_widgets()
        self.ids.row_three_items.clear_widgets()

    def open_car(self, car_id):
        """Перехід в меню конкретного авто тільки при натисканні."""
        self.active_car_id = car_id
        app = self._app()
        app.current_car_id = car_id
        app.switch_screen("car_menu")

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
