"""
database.py
Single Source of Truth for all persistent data.
Every mileage update goes through update_odometer() so that reminders,
analytics and the dashboard all stay in sync automatically.
"""

import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "garage.db")

DEFAULT_INTERVALS = [
    # (name, interval_km, interval_days)
    ("Моторна олива та фільтр", 7000, 365),
    ("Гальмівні колодки", 35000, None),
    ("Ремінь ГРМ / свічки розжарювання", 75000, None),
    ("Гальмівна рідина", 40000, 730),
    ("Охолоджувальна рідина", 60000, 1095),
    ("Олива в КПП", 60000, None),
    ("Свічки запалювання", 45000, None),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates all tables if they do not exist yet and applies migrations."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            make TEXT,
            model TEXT,
            year INTEGER,
            vin TEXT,
            engine_code TEXT,
            engine_size TEXT,
            oil_spec TEXT,
            fuel_type TEXT,
            odometer INTEGER DEFAULT 0,
            image_path TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS mods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            date TEXT,
            category TEXT,
            description TEXT,
            photo_path TEXT,
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS maintenance_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            title TEXT,
            date TEXT,
            odometer INTEGER,
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS maintenance_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            part_name TEXT,
            brand TEXT,
            part_number TEXT,
            price REAL DEFAULT 0,
            labor_cost REAL DEFAULT 0,
            photo_path TEXT,
            FOREIGN KEY (event_id) REFERENCES maintenance_events(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            name TEXT,
            interval_km INTEGER,
            interval_days INTEGER,
            last_done_odometer INTEGER DEFAULT 0,
            last_done_date TEXT,
            is_custom INTEGER DEFAULT 0,
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS fuel_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            date TEXT,
            odometer INTEGER,
            amount REAL,
            liters REAL,
            full_tank INTEGER DEFAULT 1,
            avg_consumption REAL,
            photo_path TEXT,
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER NOT NULL,
            date TEXT,
            category TEXT,
            amount REAL,
            note TEXT,
            photo_path TEXT,
            FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    conn.commit()

    # Перевірка міграції: додаємо vin у старі бази даних, якщо поля ще немає
    cur.execute("PRAGMA table_info(cars)")
    columns = [row["name"] for row in cur.fetchall()]
    if "vin" not in columns:
        cur.execute("ALTER TABLE cars ADD COLUMN vin TEXT")
        conn.commit()

    # sensible defaults, only set once
    defaults = {
        "language": "uk",
        "unit_distance": "km",
        "unit_fuel": "l",
        "unit_consumption": "l100",
        "currency": "UAH",
        "notifications": "1",
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- settings

def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------------- cars

def add_car(make, model, year, vin="", engine_code="", engine_size="", oil_spec="",
            fuel_type="", odometer=0, image_path=""):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO cars (make, model, year, vin, engine_code, engine_size, oil_spec,
           fuel_type, odometer, image_path, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (make, model, year, vin, engine_code, engine_size, oil_spec, fuel_type,
         odometer, image_path, datetime.datetime.now().isoformat()),
    )
    car_id = cur.lastrowid
    conn.commit()
    conn.close()
    # seed default reminders for the new car
    for name, km, days in DEFAULT_INTERVALS:
        add_reminder(car_id, name, km, days, last_done_odometer=odometer, is_custom=0)
    return car_id


def get_cars():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cars ORDER BY sort_order, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_car(car_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_car(car_id, **fields):
    if not fields:
        return
    conn = get_connection()
    cols = ", ".join(f"{k}=?" for k in fields)
    conn.execute(f"UPDATE cars SET {cols} WHERE id=?", (*fields.values(), car_id))
    conn.commit()
    conn.close()


def update_car_passport(car_id, make, model, year, vin, engine_code, engine_size, oil_spec, fuel_type):
    """Швидка оновлювалка паспортних даних авто."""
    update_car(
        car_id,
        make=make,
        model=model,
        year=year,
        vin=vin,
        engine_code=engine_code,
        engine_size=engine_size,
        oil_spec=oil_spec,
        fuel_type=fuel_type
    )


def delete_car(car_id):
    conn = get_connection()
    conn.execute("DELETE FROM cars WHERE id=?", (car_id,))
    conn.commit()
    conn.close()


def update_odometer(car_id, new_odometer):
    """
    THE single source of truth for mileage.
    Called from Dashboard, Fuel Tracker, Maintenance Journal, etc.
    Updates the car record and refreshes every reminder's "remaining km".
    Returns the list of reminders that are now due (<=0 km left) for
    triggering notifications.
    """
    car = get_car(car_id)
    if car is None:
        return []
    if new_odometer < car["odometer"]:
        # never let mileage go backwards silently
        new_odometer = car["odometer"]
    update_car(car_id, odometer=new_odometer)

    due = []
    for rem in get_reminders(car_id):
        remaining = compute_remaining_km(rem, new_odometer)
        if remaining is not None and remaining <= 0:
            due.append(rem)
    return due


# ------------------------------------------------------------------- mods

def add_mod(car_id, date, category, description, photo_path=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO mods (car_id, date, category, description, photo_path) "
        "VALUES (?, ?, ?, ?, ?)",
        (car_id, date, category, description, photo_path),
    )
    conn.commit()
    conn.close()


def get_mods(car_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM mods WHERE car_id=? ORDER BY date DESC", (car_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------------------------------------------------- maintenance

def add_maintenance_event(car_id, title, date, odometer):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO maintenance_events (car_id, title, date, odometer) VALUES (?, ?, ?, ?)",
        (car_id, title, date, odometer),
    )
    event_id = cur.lastrowid
    conn.commit()
    conn.close()
    update_odometer(car_id, odometer)
    return event_id


def add_maintenance_item(event_id, part_name, brand="", part_number="",
                          price=0.0, labor_cost=0.0, photo_path=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO maintenance_items
           (event_id, part_name, brand, part_number, price, labor_cost, photo_path)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (event_id, part_name, brand, part_number, price, labor_cost, photo_path),
    )
    conn.commit()
    conn.close()


def get_maintenance_events(car_id):
    conn = get_connection()
    events = conn.execute(
        "SELECT * FROM maintenance_events WHERE car_id=? ORDER BY date DESC", (car_id,)
    ).fetchall()
    result = []
    for ev in events:
        items = conn.execute(
            "SELECT * FROM maintenance_items WHERE event_id=?", (ev["id"],)
        ).fetchall()
        ev_dict = dict(ev)
        ev_dict["items"] = [dict(i) for i in items]
        ev_dict["total_cost"] = sum(i["price"] + i["labor_cost"] for i in items)
        result.append(ev_dict)
    conn.close()
    return result


# ----------------------------------------------------------------- reminders

def add_reminder(car_id, name, interval_km, interval_days=None,
                  last_done_odometer=0, last_done_date=None, is_custom=1):
    conn = get_connection()
    conn.execute(
        """INSERT INTO reminders
           (car_id, name, interval_km, interval_days, last_done_odometer,
            last_done_date, is_custom)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (car_id, name, interval_km, interval_days, last_done_odometer,
         last_done_date or datetime.date.today().isoformat(), is_custom),
    )
    conn.commit()
    conn.close()


def get_reminders(car_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reminders WHERE car_id=?", (car_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_reminder_done(reminder_id, odometer, date=None):
    conn = get_connection()
    conn.execute(
        "UPDATE reminders SET last_done_odometer=?, last_done_date=? WHERE id=?",
        (odometer, date or datetime.date.today().isoformat(), reminder_id),
    )
    conn.commit()
    conn.close()


def delete_reminder(reminder_id):
    conn = get_connection()
    conn.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
    conn.commit()
    conn.close()


def compute_remaining_km(reminder, current_odometer):
    if not reminder.get("interval_km"):
        return None
    done_at = reminder.get("last_done_odometer") or 0
    return (done_at + reminder["interval_km"]) - current_odometer


# -------------------------------------------------------------------- fuel

def add_fuel_log(car_id, date, odometer, amount, liters, full_tank=1, photo_path=""):
    avg = None
    conn = get_connection()
    prev = conn.execute(
        """SELECT * FROM fuel_logs WHERE car_id=? AND odometer < ?
           ORDER BY odometer DESC LIMIT 1""",
        (car_id, odometer),
    ).fetchone()
    if prev and full_tank and prev["odometer"] is not None:
        distance = odometer - prev["odometer"]
        if distance > 0:
            avg = round((liters / distance) * 100, 2)

    conn.execute(
        """INSERT INTO fuel_logs
           (car_id, date, odometer, amount, liters, full_tank, avg_consumption, photo_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (car_id, date, odometer, amount, liters, full_tank, avg, photo_path),
    )
    conn.commit()
    conn.close()
    update_odometer(car_id, odometer)
    return avg


def get_fuel_logs(car_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM fuel_logs WHERE car_id=? ORDER BY date DESC", (car_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------------------------------------------------------- expenses

def add_expense(car_id, date, category, amount, note="", photo_path=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO expenses (car_id, date, category, amount, note, photo_path)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (car_id, date, category, amount, note, photo_path),
    )
    conn.commit()
    conn.close()


def get_expenses(car_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM expenses WHERE car_id=? ORDER BY date DESC", (car_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------------------------------------------------------- analytics

def get_monthly_summary(car_id):
    """
    Groups maintenance + fuel + small expenses by YYYY-MM and returns
    a dict: { "2026-08": {"maintenance": x, "fuel": y, "expenses": z, "total": t} }
    Also computes cost-per-km for each month using the odometer delta.
    """
    conn = get_connection()
    summary = {}

    def bucket(date_str):
        try:
            return date_str[:7]  # "YYYY-MM"
        except Exception:
            return "unknown"

    for ev in conn.execute(
        """SELECT me.date, COALESCE(SUM(mi.price + mi.labor_cost), 0) as cost
           FROM maintenance_events me
           LEFT JOIN maintenance_items mi ON mi.event_id = me.id
           WHERE me.car_id=? GROUP BY me.id""",
        (car_id,),
    ):
        m = bucket(ev["date"])
        summary.setdefault(m, {"maintenance": 0, "fuel": 0, "expenses": 0})
        summary[m]["maintenance"] += ev["cost"]

    for f in conn.execute(
        "SELECT date, amount FROM fuel_logs WHERE car_id=?", (car_id,)
    ):
        m = bucket(f["date"])
        summary.setdefault(m, {"maintenance": 0, "fuel": 0, "expenses": 0})
        summary[m]["fuel"] += f["amount"] or 0

    for e in conn.execute(
        "SELECT date, amount FROM expenses WHERE car_id=?", (car_id,)
    ):
        m = bucket(e["date"])
        summary.setdefault(m, {"maintenance": 0, "fuel": 0, "expenses": 0})
        summary[m]["expenses"] += e["amount"] or 0

    # odometer deltas per month, using fuel_logs + maintenance_events as mileage points
    odo_points = conn.execute(
        """SELECT date, odometer FROM fuel_logs WHERE car_id=?
           UNION SELECT date, odometer FROM maintenance_events WHERE car_id=?
           ORDER BY date""",
        (car_id, car_id),
    ).fetchall()
    conn.close()

    month_odo = {}
    for p in odo_points:
        m = bucket(p["date"])
        month_odo.setdefault(m, []).append(p["odometer"])

    result = []
    for month in sorted(summary.keys(), reverse=True):
        vals = summary[month]
        total = vals["maintenance"] + vals["fuel"] + vals["expenses"]
        km_driven = None
        if month in month_odo and len(month_odo[month]) >= 2:
            km_driven = max(month_odo[month]) - min(month_odo[month])
        cost_per_km = round(total / km_driven, 2) if km_driven and km_driven > 0 else None
        result.append({
            "month": month,
            "maintenance": round(vals["maintenance"], 2),
            "fuel": round(vals["fuel"], 2),
            "expenses": round(vals["expenses"], 2),
            "total": round(total, 2),
            "km_driven": km_driven,
            "cost_per_km": cost_per_km,
        })
    return result


if __name__ == "__main__":
    init_db()
    print("Фундамент (database.py) успішно оновлено та перевірено!")
