import os
import random
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv("AGMARKNET_API_KEY", "")

MOCK_PRICES = [
    {"commodity": "Tomato",      "district": "Bangalore",   "market": "KR Market",      "base": 1200},
    {"commodity": "Onion",       "district": "Hubli",       "market": "Hubli APMC",      "base": 900},
    {"commodity": "Potato",      "district": "Mysuru",      "market": "Mysuru APMC",     "base": 650},
    {"commodity": "Brinjal",     "district": "Tumkur",      "market": "Tumkur APMC",     "base": 900},
    {"commodity": "Cabbage",     "district": "Hassan",      "market": "Hassan APMC",     "base": 700},
    {"commodity": "Cauliflower", "district": "Shimoga",     "market": "Shimoga APMC",    "base": 1100},
    {"commodity": "Carrot",      "district": "Kolar",       "market": "Kolar APMC",      "base": 1250},
    {"commodity": "Beans",       "district": "Mandya",      "market": "Mandya APMC",     "base": 1400},
    {"commodity": "Capsicum",    "district": "Dharwad",     "market": "Dharwad APMC",    "base": 2100},
    {"commodity": "Chilli",      "district": "Gulbarga",    "market": "Gulbarga APMC",   "base": 6200},
    {"commodity": "Garlic",      "district": "Bijapur",     "market": "Bijapur APMC",    "base": 3500},
    {"commodity": "Ginger",      "district": "Bangalore",   "market": "Yeshwantpur",     "base": 4300},
]


def fetch_latest_prices():
    if API_KEY:
        try:
            url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
            params = {
                "api-key": API_KEY,
                "format": "json",
                "filters[state]": "Karnataka",
                "limit": 100,
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("records", [])
                return _parse_agmarknet(data)
        except Exception as e:
            print(f"Agmarknet API error: {e}. Using mock data.")

    return _generate_mock()


def _parse_agmarknet(records):
    today = datetime.now().strftime("%Y-%m-%d")
    results = []
    for r in records:
        try:
            modal = float(r.get("modal_price", 0))
            mn = float(r.get("min_price", modal * 0.8))
            mx = float(r.get("max_price", modal * 1.2))
            results.append({
                "commodity": r.get("commodity", "Unknown"),
                "district":  r.get("district", "Unknown"),
                "market":    r.get("market", "Unknown"),
                "min_price": mn,
                "max_price": mx,
                "modal_price": modal,
                "date": today,
            })
        except Exception:
            continue
    return results


def _generate_mock():
    today = datetime.now().strftime("%Y-%m-%d")
    results = []
    for item in MOCK_PRICES:
        base = item["base"]
        modal = base + random.randint(-80, 80)
        results.append({
            "commodity":   item["commodity"],
            "district":    item["district"],
            "market":      item["market"],
            "min_price":   round(modal * 0.8),
            "max_price":   round(modal * 1.2),
            "modal_price": modal,
            "date":        today,
        })
    return results
