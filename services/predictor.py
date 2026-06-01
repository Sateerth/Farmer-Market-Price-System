import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta


def predict_price(price_rows: list, days_ahead: int = 7) -> dict:
    """
    Takes a list of dicts with keys: date (YYYY-MM-DD), modal_price.
    Returns prediction dict.
    """
    if len(price_rows) < 3:
        return {"error": "Not enough data for prediction (need at least 3 data points)"}

    df = pd.DataFrame(price_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date")

    # Convert dates to numeric (days from first date)
    origin = df["date"].min()
    df["day_num"] = (df["date"] - origin).dt.days

    X = df[["day_num"]].values
    y = df["modal_price"].values

    model = LinearRegression()
    model.fit(X, y)

    # Predict future
    last_day = int(df["day_num"].max())
    future_day = last_day + days_ahead
    predicted_price = float(model.predict([[future_day]])[0])
    predicted_price = max(0, round(predicted_price, 2))

    # Confidence: R² score clamped to 50-95%
    r2 = model.score(X, y)
    confidence = round(max(50, min(95, r2 * 100)), 1)

    # Trend
    slope = model.coef_[0]
    if slope > 5:
        trend = "rising"
        suggestion = f"Prices are trending upward. Consider waiting {days_ahead} days before selling."
    elif slope < -5:
        trend = "falling"
        suggestion = "Prices are falling. Consider selling now or storing produce."
    else:
        trend = "stable"
        suggestion = "Prices are stable. Current market conditions are suitable for selling."

    # Build chart data: historical + forecasted points
    historical = []
    for _, row in df.iterrows():
        historical.append({
            "date": row["date"].strftime("%b %d"),
            "price": round(row["modal_price"], 2),
        })

    forecast = []
    last_date = df["date"].max()
    for i in range(1, days_ahead + 1):
        fut_date = last_date + timedelta(days=i)
        fut_day = last_day + i
        fut_price = max(0, round(float(model.predict([[fut_day]])[0]), 2))
        forecast.append({
            "date": fut_date.strftime("%b %d"),
            "price": fut_price,
        })

    return {
        "predicted_price": predicted_price,
        "trend":           trend,
        "confidence":      confidence,
        "slope":           round(float(slope), 4),
        "suggestion":      suggestion,
        "historical":      historical,
        "forecast":        forecast,
    }
