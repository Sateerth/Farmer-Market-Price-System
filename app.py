import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from dotenv import load_dotenv

load_dotenv()

from database import init_db, seed_db, get_db
from services.agmarknet import fetch_latest_prices
from services.sms import send_price_alert, send_sms
from services.predictor import predict_price

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mandiAlertSecretKey2024")


# ─── Init DB on startup ───────────────────────────────────────────────────────
with app.app_context():
    init_db()
    seed_db()


# ─── Dashboard ────────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    db = get_db()

    total_farmers    = db.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
    total_commodities = db.execute("SELECT COUNT(DISTINCT commodity) FROM prices").fetchone()[0]
    total_districts  = db.execute("SELECT COUNT(DISTINCT district) FROM prices").fetchone()[0]
    total_markets    = db.execute("SELECT COUNT(DISTINCT market) FROM prices").fetchone()[0]
    alerts_today     = db.execute(
        "SELECT COUNT(*) FROM sms_logs WHERE date(sent_at)=date('now')"
    ).fetchone()[0]

    commodities = db.execute(
        "SELECT DISTINCT commodity FROM prices ORDER BY commodity"
    ).fetchall()
    commodities = [r["commodity"] for r in commodities]

    trends = []
    for c in commodities:
        rows = db.execute(
            "SELECT date, modal_price FROM prices WHERE commodity=? ORDER BY date",
            (c,)
        ).fetchall()
        if len(rows) < 2:
            continue
        latest = rows[-1]["modal_price"]
        prev   = rows[-2]["modal_price"]
        change = round(latest - prev)
        pct    = round((change / prev * 100) if prev else 0, 1)
        trend  = "rising" if change > 50 else ("falling" if change < -50 else "stable")
        spark  = [r["modal_price"] for r in rows[-7:]]
        trends.append({
            "commodity": c,
            "latest_price": latest,
            "change": change,
            "change_pct": pct,
            "trend": trend,
            "sparkline": spark,
        })

    recent_alerts = db.execute(
        "SELECT * FROM sms_logs ORDER BY sent_at DESC LIMIT 5"
    ).fetchall()
    recent_alerts = [dict(r) for r in recent_alerts]

    agmarknet_sync = db.execute(
        "SELECT MAX(created_at) FROM prices"
    ).fetchone()[0] or "Never"

    db.close()

    return render_template("dashboard.html",
        total_farmers=total_farmers,
        total_commodities=total_commodities,
        total_districts=total_districts,
        total_markets=total_markets,
        alerts_today=alerts_today,
        trends=trends,
        recent_alerts=recent_alerts,
        agmarknet_sync=agmarknet_sync,
        trends_json=json.dumps(trends),
    )


# ─── Live Prices ──────────────────────────────────────────────────────────────
@app.route("/prices")
def prices():
    db = get_db()
    commodity = request.args.get("commodity", "")
    district  = request.args.get("district", "")
    market    = request.args.get("market", "")

    query  = "SELECT * FROM prices WHERE 1=1"
    params = []
    if commodity:
        query += " AND commodity=?"; params.append(commodity)
    if district:
        query += " AND district=?";  params.append(district)
    if market:
        query += " AND market=?";    params.append(market)
    query += " ORDER BY date DESC, commodity LIMIT 200"

    rows = db.execute(query, params).fetchall()
    rows = [dict(r) for r in rows]

    commodities = [r["commodity"] for r in db.execute(
        "SELECT DISTINCT commodity FROM prices ORDER BY commodity").fetchall()]
    districts = [r["district"] for r in db.execute(
        "SELECT DISTINCT district FROM prices ORDER BY district").fetchall()]
    markets = [r["market"] for r in db.execute(
        "SELECT DISTINCT market FROM prices ORDER BY market").fetchall()]

    db.close()
    return render_template("prices.html",
        rows=rows, commodities=commodities,
        districts=districts, markets=markets,
        selected_commodity=commodity,
        selected_district=district,
        selected_market=market,
    )


@app.route("/prices/sync", methods=["POST"])
def sync_prices():
    db = get_db()
    new_prices = fetch_latest_prices()
    count = 0
    today = datetime.now().strftime("%Y-%m-%d")
    for p in new_prices:
        existing = db.execute(
            "SELECT id FROM prices WHERE commodity=? AND market=? AND date=?",
            (p["commodity"], p["market"], today)
        ).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO prices (commodity,district,market,min_price,max_price,modal_price,date) VALUES (?,?,?,?,?,?,?)",
                (p["commodity"], p["district"], p["market"], p["min_price"], p["max_price"], p["modal_price"], today)
            )
            count += 1

    farmers = db.execute("SELECT f.*, fc.commodity FROM farmers f JOIN farmer_crops fc ON f.id=fc.farmer_id").fetchall()
    alerts_sent = 0
    for farmer in farmers:
        price_row = db.execute(
            "SELECT modal_price, market FROM prices WHERE commodity=? ORDER BY date DESC LIMIT 1",
            (farmer["commodity"],)
        ).fetchone()
        if price_row:
            result = send_price_alert(
                farmer["name"], farmer["phone"],
                farmer["commodity"], price_row["modal_price"], price_row["market"]
            )
            db.execute(
                "INSERT INTO sms_logs (farmer_id,phone,commodity,message,status) VALUES (?,?,?,?,?)",
                (farmer["id"], farmer["phone"], farmer["commodity"],
                 f"{farmer['commodity']} @ Rs.{price_row['modal_price']}/q at {price_row['market']}",
                 result["status"])
            )
            alerts_sent += 1

    db.commit()
    db.close()
    flash(f"Synced {count} new price records. {alerts_sent} SMS alerts triggered.", "success")
    return redirect(url_for("prices"))


# ─── AI Prediction ────────────────────────────────────────────────────────────
@app.route("/predict")
def predict():
    db = get_db()
    commodities = [r["commodity"] for r in db.execute(
        "SELECT DISTINCT commodity FROM prices ORDER BY commodity").fetchall()]
    selected = request.args.get("commodity", commodities[0] if commodities else "")

    prediction = None
    if selected:
        rows = db.execute(
            "SELECT date, modal_price FROM prices WHERE commodity=? ORDER BY date",
            (selected,)
        ).fetchall()
        rows = [{"date": r["date"], "modal_price": r["modal_price"]} for r in rows]
        if rows:
            prediction = predict_price(rows)

    db.close()
    return render_template("predict.html",
        commodities=commodities,
        selected=selected,
        prediction=prediction,
        prediction_json=json.dumps(prediction) if prediction else "null",
    )


# ─── Farmer Registration ──────────────────────────────────────────────────────
CROP_LIST = ["Tomato","Onion","Potato","Brinjal","Cabbage","Cauliflower",
             "Carrot","Beans","Capsicum","Chilli","Garlic","Ginger"]

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name    = request.form.get("name","").strip()
        phone   = request.form.get("phone","").strip()
        village = request.form.get("village","").strip()
        market  = request.form.get("market","").strip()
        crops   = request.form.getlist("crops")

        if not name or not phone:
            flash("Name and phone number are required.", "danger")
            return render_template("register.html", crops=CROP_LIST)

        if not phone.startswith("+91"):
            phone = "+91" + phone.lstrip("0")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO farmers (name,phone,state,village,nearest_market) VALUES (?,?,?,?,?)",
                (name, phone, "Karnataka", village, market)
            )
            farmer_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            for crop in crops:
                db.execute("INSERT INTO farmer_crops (farmer_id,commodity) VALUES (?,?)", (farmer_id, crop))
            db.commit()
            flash(f"Farmer '{name}' registered successfully!", "success")
            return redirect(url_for("farmers"))
        except Exception as e:
            db.rollback()
            flash(f"Registration failed: {str(e)}", "danger")
        finally:
            db.close()

    return render_template("register.html", crops=CROP_LIST)


# ─── Registered Farmers ───────────────────────────────────────────────────────
@app.route("/farmers")
def farmers():
    db = get_db()
    rows = db.execute("SELECT * FROM farmers ORDER BY created_at DESC").fetchall()
    farmers_list = []
    for r in rows:
        crops = db.execute(
            "SELECT commodity FROM farmer_crops WHERE farmer_id=?", (r["id"],)
        ).fetchall()
        d = dict(r)
        d["crops"] = [c["commodity"] for c in crops]
        farmers_list.append(d)
    db.close()
    return render_template("farmers.html", farmers=farmers_list)


# ─── SMS Alerts ───────────────────────────────────────────────────────────────
@app.route("/alerts")
def alerts():
    db = get_db()
    logs = db.execute(
        "SELECT s.*, f.name as farmer_name FROM sms_logs s LEFT JOIN farmers f ON s.farmer_id=f.id ORDER BY s.sent_at DESC LIMIT 100"
    ).fetchall()
    logs = [dict(r) for r in logs]
    db.close()
    return render_template("alerts.html", logs=logs)


@app.route("/alerts/send", methods=["POST"])
def send_alert():
    data       = request.get_json()
    farmer_id  = data.get("farmer_id")
    commodity  = data.get("commodity")
    db = get_db()
    farmer = db.execute("SELECT * FROM farmers WHERE id=?", (farmer_id,)).fetchone()
    if not farmer:
        db.close()
        return jsonify({"error": "Farmer not found"}), 404

    price_row = db.execute(
        "SELECT modal_price, market FROM prices WHERE commodity=? ORDER BY date DESC LIMIT 1",
        (commodity,)
    ).fetchone()
    price  = price_row["modal_price"] if price_row else 0
    market = price_row["market"] if price_row else "Unknown"

    result = send_price_alert(farmer["name"], farmer["phone"], commodity, price, market)
    db.execute(
        "INSERT INTO sms_logs (farmer_id,phone,commodity,message,status) VALUES (?,?,?,?,?)",
        (farmer_id, farmer["phone"], commodity,
         f"{commodity} @ Rs.{price}/q at {market}", result["status"])
    )
    db.commit()
    db.close()
    return jsonify(result)


# ─── Debug: Test SMS Endpoint ─────────────────────────────────────────────────
@app.route("/test-sms", methods=["GET", "POST"])
def test_sms():
    """
    Test SMS sending with detailed debugging.
    GET: Shows form | POST: Sends test SMS
    """
    if request.method == "GET":
        db = get_db()
        farmers = db.execute("SELECT id, name, phone FROM farmers LIMIT 10").fetchall()
        db.close()
        return render_template("test_sms.html", farmers=farmers)
    
    # POST: Send test SMS
    phone = request.form.get("phone", "").strip()
    test_message = request.form.get("message", "Test message from KrishiVani").strip()
    
    if not phone:
        flash("Phone number is required", "danger")
        return redirect(url_for("test_sms"))
    
    result = send_sms(phone, test_message)
    
    # Log to database for tracking
    db = get_db()
    db.execute(
        "INSERT INTO sms_logs (phone, commodity, message, status) VALUES (?,?,?,?)",
        (phone, "TEST", test_message, result["status"])
    )
    db.commit()
    db.close()
    
    # Show detailed result
    flash(f"SMS Status: {result.get('status', 'unknown')} | Details: {result}", "info")
    return redirect(url_for("test_sms"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
