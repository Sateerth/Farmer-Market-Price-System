"""
Automatic price sync + SMS alert scheduler.
Runs independently alongside app.py.
Fetches latest prices every day at 8:00 AM and sends SMS to all registered farmers.
"""

import time
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(__file__))

from database import get_db, init_db, seed_db, DB_PATH
from services.agmarknet import fetch_latest_prices
from services.sms import send_price_alert

SYNC_HOUR   = int(os.getenv("ALERT_HOUR", "8"))    # Default: 8 AM
SYNC_MINUTE = int(os.getenv("ALERT_MINUTE", "0"))  # Default: :00


def run_sync():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running price sync + SMS alerts...")

    db = get_db()
    new_prices = fetch_latest_prices()
    today = datetime.now().strftime("%Y-%m-%d")

    inserted = 0
    for p in new_prices:
        existing = db.execute(
            "SELECT id FROM prices WHERE commodity=? AND market=? AND date=?",
            (p["commodity"], p["market"], today)
        ).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO prices (commodity,district,market,min_price,max_price,modal_price,date) VALUES (?,?,?,?,?,?,?)",
                (p["commodity"], p["district"], p["market"],
                 p["min_price"], p["max_price"], p["modal_price"], today)
            )
            inserted += 1
    db.commit()
    print(f"  Inserted {inserted} new price records.")

    # Send SMS to every farmer for each of their subscribed crops
    farmers = db.execute("""
        SELECT f.id, f.name, f.phone, fc.commodity
        FROM farmers f
        JOIN farmer_crops fc ON f.id = fc.farmer_id
    """).fetchall()

    alerts_sent = 0
    for farmer in farmers:
        price_row = db.execute(
            "SELECT modal_price, market FROM prices WHERE commodity=? ORDER BY date DESC LIMIT 1",
            (farmer["commodity"],)
        ).fetchone()

        if not price_row:
            continue

        result = send_price_alert(
            farmer["name"], farmer["phone"],
            farmer["commodity"], price_row["modal_price"], price_row["market"]
        )

        db.execute(
            "INSERT INTO sms_logs (farmer_id, phone, commodity, message, status) VALUES (?,?,?,?,?)",
            (farmer["id"], farmer["phone"], farmer["commodity"],
             f"{farmer['commodity']} @ Rs.{price_row['modal_price']}/q at {price_row['market']}",
             result["status"])
        )
        alerts_sent += 1

    db.commit()
    db.close()
    print(f"  Sent {alerts_sent} SMS alerts.")


def main():
    init_db()
    seed_db()
    print(f"Scheduler started. Alerts will run daily at {SYNC_HOUR:02d}:{SYNC_MINUTE:02d}.")
    print("Press Ctrl+C to stop.\n")

    last_run_date = None

    while True:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # Run once per day at the configured hour:minute
        if (now.hour == SYNC_HOUR and now.minute == SYNC_MINUTE
                and last_run_date != today):
            try:
                run_sync()
                last_run_date = today
            except Exception as e:
                print(f"[ERROR] Sync failed: {e}")

        time.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    main()
