from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
NORMAL_COLLECTION_MINUTES = 8 * 60 + 30


def _load_history() -> pd.DataFrame:
    history = pd.read_csv(DATA_DIR / "collection_history.csv")
    history["collection_minutes"] = history["collection_time"].apply(_time_to_minutes)
    history["delay_minutes"] = history["collection_minutes"].apply(
        lambda value: value - NORMAL_COLLECTION_MINUTES if pd.notna(value) else pd.NA
    )
    history["delay_minutes"] = pd.to_numeric(history["delay_minutes"], errors="coerce")
    history["houses_waiting"] = history["total_houses"] - history["houses_ready"]
    return history


def _load_households() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "household_status.csv")


def _time_to_minutes(value: str | float) -> float:
    if pd.isna(value) or str(value).strip() in {"", "—", "-"}:
        return float("nan")
    return datetime.strptime(str(value).strip(), "%H:%M").hour * 60 + datetime.strptime(
        str(value).strip(), "%H:%M"
    ).minute


def _format_time(minutes: float | int | None) -> str:
    if minutes is None or pd.isna(minutes):
        return "Not recorded"
    hours = int(minutes) // 60
    mins = int(minutes) % 60
    suffix = "AM" if hours < 12 else "PM"
    display_hour = hours % 12 or 12
    return f"{display_hour:02d}:{mins:02d} {suffix}"


def _predict_delay(history: pd.DataFrame, ready: int, waiting: int) -> float:
    training = history.dropna(subset=["delay_minutes"]).copy()
    features = ["houses_ready", "houses_waiting", "collection_minutes"]
    training["collection_minutes"] = training["collection_minutes"].fillna(
        NORMAL_COLLECTION_MINUTES
    )
    training["houses_waiting"] = training["houses_waiting"].fillna(
        training["total_houses"] - training["houses_ready"]
    )
    model = RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=1)
    model.fit(training[["houses_ready", "houses_waiting", "collection_minutes"]], training["delay_minutes"])

    latest_collection = training["collection_minutes"].iloc[-1]
    prediction_input = pd.DataFrame(
        [[ready, waiting, latest_collection]],
        columns=["houses_ready", "houses_waiting", "collection_minutes"],
    )
    prediction = model.predict(prediction_input)[0]
    return max(0, round(float(prediction)))


def build_dashboard_data() -> dict:
    history = _load_history()
    households = _load_households()
    total_houses = int(len(households))
    ready = int((households["status"].str.lower() == "ready").sum())
    waiting = total_houses - ready
    predicted_delay = _predict_delay(history, ready, waiting)
    expected_minutes = NORMAL_COLLECTION_MINUTES + predicted_delay

    historical = []
    for _, row in history.iterrows():
        historical.append(
            {
                "day": row["day"],
                "collection_time": row["collection_time"] if pd.notna(row["collection_time"]) else "Not recorded",
                "delay_minutes": int(row["delay_minutes"]) if pd.notna(row["delay_minutes"]) else None,
                "houses_ready": int(row["houses_ready"]),
            }
        )

    return {
        "summary": {
            "total_houses": total_houses,
            "ready": ready,
            "waiting": waiting,
            "expected_collection": _format_time(expected_minutes),
            "predicted_delay": predicted_delay,
            "status": "Delayed" if predicted_delay >= 20 else "On schedule",
        },
        "households": households.to_dict(orient="records"),
        "history": historical,
        "model": {
            "name": "Random Forest Regression",
            "training_records": int(history["delay_minutes"].notna().sum()),
            "normal_time": _format_time(NORMAL_COLLECTION_MINUTES),
        },
        "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }
