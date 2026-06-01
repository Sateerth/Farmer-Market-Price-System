# import sqlite3
# import os
# import random
# from datetime import datetime, timedelta

# DB_PATH = os.path.join(os.path.dirname(__file__), "mandiAlert.db")


# def get_db():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     conn.execute("PRAGMA foreign_keys = ON")
#     return conn


# def init_db():
#     conn = get_db()
#     cur = conn.cursor()

#     cur.executescript("""
#         CREATE TABLE IF NOT EXISTS farmers (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             phone TEXT NOT NULL UNIQUE,
#             state TEXT NOT NULL DEFAULT 'Karnataka',
#             village TEXT,
#             nearest_market TEXT,
#             created_at TEXT DEFAULT (datetime('now'))
#         );

#         CREATE TABLE IF NOT EXISTS farmer_crops (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
#             commodity TEXT NOT NULL
#         );

#         CREATE TABLE IF NOT EXISTS prices (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             commodity TEXT NOT NULL,
#             district TEXT NOT NULL,
#             market TEXT NOT NULL,
#             min_price REAL NOT NULL,
#             max_price REAL NOT NULL,
#             modal_price REAL NOT NULL,
#             date TEXT NOT NULL,
#             created_at TEXT DEFAULT (datetime('now'))
#         );

#         CREATE TABLE IF NOT EXISTS sms_logs (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             farmer_id INTEGER REFERENCES farmers(id) ON DELETE SET NULL,
#             phone TEXT NOT NULL,
#             commodity TEXT NOT NULL,
#             message TEXT NOT NULL,
#             status TEXT NOT NULL DEFAULT 'pending',
#             sent_at TEXT DEFAULT (datetime('now'))
#         );
#     """)
#     conn.commit()
#     conn.close()


# def seed_db():
#     conn = get_db()
#     cur = conn.cursor()

#     cur.execute("SELECT COUNT(*) FROM farmers")
#     if cur.fetchone()[0] > 0:
#         conn.close()
#         return

#     farmers = [
#         ("Ramesh Gowda", "+919845012345", "Karnataka", "Kolar Farms", "Kolar APMC", ["Tomato", "Potato"]),
#         ("Suresh Kumar", "+919876543210", "Karnataka", "Hassan Fields", "Hassan APMC", ["Onion", "Garlic", "Chilli"]),
#         ("Lakshmi Devi", "+918762345678", "Karnataka", "Mysuru Garden", "Mysuru APMC", ["Tomato", "Capsicum", "Brinjal"]),
#         ("Manjunath Reddy", "+917654321098", "Karnataka", "Tumkur Farm", "Tumkur APMC", ["Potato", "Beans", "Carrot"]),
#     ]

#     for name, phone, state, village, market, crops in farmers:
#         cur.execute(
#             "INSERT INTO farmers (name, phone, state, village, nearest_market) VALUES (?, ?, ?, ?, ?)",
#             (name, phone, state, village, market)
#         )
#         farmer_id = cur.lastrowid
#         for crop in crops:
#             cur.execute("INSERT INTO farmer_crops (farmer_id, commodity) VALUES (?, ?)", (farmer_id, crop))

#     commodities = [
#         ("Tomato",     "Bangalore",  "KR Market",     800,  1600),
#         ("Onion",      "Hubli",      "Hubli APMC",    600,  1200),
#         ("Potato",     "Mysuru",     "Mysuru APMC",   400,   900),
#         ("Brinjal",    "Tumkur",     "Tumkur APMC",   700,  1100),
#         ("Cabbage",    "Hassan",     "Hassan APMC",   500,   900),
#         ("Cauliflower","Shimoga",    "Shimoga APMC",  800,  1500),
#         ("Carrot",     "Kolar",      "Kolar APMC",    900,  1600),
#         ("Beans",      "Mandya",     "Mandya APMC",  1000,  1800),
#         ("Capsicum",   "Dharwad",    "Dharwad APMC", 1500,  2800),
#         ("Chilli",     "Gulbarga",   "Gulbarga APMC",5000,  7500),
#         ("Garlic",     "Bijapur",    "Bijapur APMC", 2500,  4500),
#         ("Ginger",     "Bangalore",  "Yeshwantpur",  3000,  5500),
#     ]

#     today = datetime.now()
#     for commodity, district, market, base_min, base_max in commodities:
#         base_modal = (base_min + base_max) // 2
#         for i in range(15):
#             day = today - timedelta(days=14 - i)
#             date_str = day.strftime("%Y-%m-%d")
#             drift = random.uniform(-0.05, 0.05) * i
#             modal = int(base_modal * (1 + drift) + random.randint(-50, 50))
#             mn = int(modal * 0.8)
#             mx = int(modal * 1.2)
#             cur.execute(
#                 "INSERT INTO prices (commodity, district, market, min_price, max_price, modal_price, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
#                 (commodity, district, market, mn, mx, modal, date_str)
#             )

#     conn.commit()
#     conn.close()
#     print("Database seeded successfully.")


import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "mandiAlert.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            state TEXT NOT NULL DEFAULT 'Karnataka',
            village TEXT,
            nearest_market TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS farmer_crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
            commodity TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commodity TEXT NOT NULL,
            district TEXT NOT NULL,
            market TEXT NOT NULL,
            min_price REAL NOT NULL,
            max_price REAL NOT NULL,
            modal_price REAL NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sms_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER REFERENCES farmers(id) ON DELETE SET NULL,
            phone TEXT NOT NULL,
            commodity TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            sent_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def clear_existing_farmers():
    """Remove all existing farmer-related data while preserving prices and other features."""
    conn = get_db()
    cur = conn.cursor()

    # Remove dependent farmer crop records
    cur.execute("DELETE FROM farmer_crops")

    # Remove SMS logs related to farmers
    cur.execute("DELETE FROM sms_logs")

    # Remove all farmers
    cur.execute("DELETE FROM farmers")

    # Reset only farmer-related auto increment counters
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('farmers', 'farmer_crops', 'sms_logs')")

    conn.commit()
    conn.close()

    print("Existing farmers data removed successfully.")


def seed_db():
    conn = get_db()
    cur = conn.cursor()

    # Only seed prices if not already present
    cur.execute("SELECT COUNT(*) FROM prices")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    commodities = [
        ("Tomato",     "Bangalore",  "KR Market",     800,  1600),
        ("Onion",      "Hubli",      "Hubli APMC",    600,  1200),
        ("Potato",     "Mysuru",     "Mysuru APMC",   400,   900),
        ("Brinjal",    "Tumkur",     "Tumkur APMC",   700,  1100),
        ("Cabbage",    "Hassan",     "Hassan APMC",   500,   900),
        ("Cauliflower", "Shimoga",   "Shimoga APMC",  800,  1500),
        ("Carrot",     "Kolar",      "Kolar APMC",    900,  1600),
        ("Beans",      "Mandya",     "Mandya APMC",  1000,  1800),
        ("Capsicum",   "Dharwad",    "Dharwad APMC", 1500,  2800),
        ("Chilli",     "Gulbarga",   "Gulbarga APMC", 5000, 7500),
        ("Garlic",     "Bijapur",    "Bijapur APMC", 2500, 4500),
        ("Ginger",     "Bangalore",  "Yeshwantpur",  3000, 5500),
    ]

    today = datetime.now()
    for commodity, district, market, base_min, base_max in commodities:
        base_modal = (base_min + base_max) // 2
        for i in range(15):
            day = today - timedelta(days=14 - i)
            date_str = day.strftime("%Y-%m-%d")
            drift = random.uniform(-0.05, 0.05) * i
            modal = int(base_modal * (1 + drift) + random.randint(-50, 50))
            mn = int(modal * 0.8)
            mx = int(modal * 1.2)
            cur.execute(
                "INSERT INTO prices (commodity, district, market, min_price, max_price, modal_price, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (commodity, district, market, mn, mx, modal, date_str)
            )

    conn.commit()
    conn.close()
    print("Price database seeded successfully.")


if __name__ == "__main__":
    init_db()
    clear_existing_farmers()   # Removes old farmer records only
    seed_db()                  # Keeps market price data intact