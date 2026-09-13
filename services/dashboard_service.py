from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
NORMAL_COLLECTION_MINUTES = 8 * 60 + 30
TOTAL_HOUSES_DEFAULT = 12
HISTORY_COLUMNS = {"day", "collection_time", "total_houses", "houses_ready"}
HOUSEHOLD_COLUMNS = {"house_id", "status", "last_updated"}
MODEL_FEATURES = ["houses_ready"]


class DataValidationError(ValueError):
    """Raised when a CSV is missing or contains unusable values."""


def _time_to_minutes(value: Any) -> float:
    if pd.isna(value) or str(value).strip() in {"", "—", "-", "nan", "None"}:
        return float("nan")
    text = str(value).strip()
    try:
        parsed = datetime.strptime(text, "%H:%M")
    except ValueError:
        raise DataValidationError(f"Invalid time '{text}'. Use HH:MM (24-hour format).") from None
    return float(parsed.hour * 60 + parsed.minute)


def _format_time(minutes: float | int | None) -> str:
    if minutes is None or pd.isna(minutes):
        return "Not recorded"
    minutes = int(round(float(minutes))) % (24 * 60)
    hours, mins = divmod(minutes, 60)
    suffix = "AM" if hours < 12 else "PM"
    return f"{hours % 12 or 12:02d}:{mins:02d} {suffix}"


def _read_csv(filename: str, required_columns: set[str]) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise DataValidationError(f"Dataset file is missing: {path.name}")
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as exc:
        raise DataValidationError(f"Could not read {path.name}: {exc}") from exc
    missing = required_columns - set(frame.columns)
    if missing:
        raise DataValidationError(f"{path.name} is missing columns: {', '.join(sorted(missing))}")
    if frame.empty:
        raise DataValidationError(f"{path.name} does not contain any rows.")
    return frame


def _load_history() -> pd.DataFrame:
    filename = "demo_collection_history.csv" if os.getenv("SWC_DATA_MODE", "field").lower() == "demo" else "collection_history.csv"
    history = _read_csv(filename, HISTORY_COLUMNS).copy()
    for column in ("total_houses", "houses_ready"):
        history[column] = pd.to_numeric(history[column], errors="coerce")
    if history[["total_houses", "houses_ready"]].isna().any().any():
        raise DataValidationError(f"{filename} has invalid numeric values.")
    if (history["total_houses"] <= 0).any() or (history["houses_ready"] < 0).any():
        raise DataValidationError(f"{filename} contains negative or zero house counts.")
    if (history["houses_ready"] > history["total_houses"]).any():
        raise DataValidationError(f"{filename} has more ready houses than total houses.")
    history["collection_minutes"] = history["collection_time"].apply(_time_to_minutes)
    history["delay_minutes"] = history["collection_minutes"] - NORMAL_COLLECTION_MINUTES
    history["houses_waiting"] = history["total_houses"] - history["houses_ready"]
    history["readiness_ratio"] = history["houses_ready"] / history["total_houses"]
    return history


def _load_households() -> pd.DataFrame:
    households = _read_csv("household_status.csv", HOUSEHOLD_COLUMNS).copy()
    households["status"] = households["status"].astype(str).str.strip().str.title()
    invalid = ~households["status"].isin({"Ready", "Waiting"})
    if invalid.any():
        raise DataValidationError("household_status.csv contains a status other than Ready or Waiting.")
    households["last_updated"] = households["last_updated"].apply(_time_to_minutes)
    households["last_updated_display"] = households["last_updated"].apply(_format_time)
    return households


def _build_model(history: pd.DataFrame) -> tuple[RandomForestRegressor, dict[str, Any]]:
    training = history.dropna(subset=["delay_minutes", "collection_minutes"]).copy()
    if len(training) < 5:
        raise DataValidationError("At least 5 recorded collection times are required to train the model.")
    model = RandomForestRegressor(n_estimators=200, random_state=42, min_samples_leaf=2)
    metrics: dict[str, Any] = {"available": False, "note": "Dataset is too small for a stable evaluation."}
    if len(training) >= 10:
        # Preserve chronological order: earlier observations train the model,
        # and the final observations represent a forward-looking test period.
        train, test = training.iloc[:-3], training.iloc[-3:]
        evaluation_model = RandomForestRegressor(n_estimators=200, random_state=42, min_samples_leaf=2)
        evaluation_model.fit(train[MODEL_FEATURES], train["delay_minutes"])
        actual = test["delay_minutes"]
        predicted = evaluation_model.predict(test[MODEL_FEATURES])
        baseline_prediction = train["delay_minutes"].mean()
        metrics = {
            "available": True,
            "test_records": int(len(test)),
            "mae_minutes": round(float(mean_absolute_error(actual, predicted)), 2),
            "rmse_minutes": round(float(mean_squared_error(actual, predicted) ** 0.5), 2),
            "r2": round(float(r2_score(actual, predicted)), 3),
            "baseline_mae_minutes": round(float(mean_absolute_error(actual, [baseline_prediction] * len(actual))), 2),
            "baseline_name": "Historical-average baseline",
            "split": "Chronological hold-out: first 8 usable observations train, final 3 test",
            "note": "Forward-looking evaluation; the dataset remains small, so metrics may vary with new observations.",
        }
    model.fit(training[MODEL_FEATURES], training["delay_minutes"])
    return model, metrics


def _status_for_delay(delay: float) -> str:
    if delay <= 5:
        return "On Time"
    if delay <= 20:
        return "Slight Delay"
    return "Delayed"


def predict_delay(ready: int) -> dict[str, Any]:
    history = _load_history()
    households = _load_households()
    total = int(max(history["total_houses"].max(), len(households), TOTAL_HOUSES_DEFAULT))
    if not isinstance(ready, int) or ready < 0 or ready > total:
        raise DataValidationError(f"Ready houses must be an integer between 0 and {total}.")
    model, _ = _build_model(history)
    waiting = total - ready
    ratio = ready / total
    input_frame = pd.DataFrame([[ready]], columns=MODEL_FEATURES)
    predicted_delay = max(0, round(float(model.predict(input_frame)[0])))
    estimated = NORMAL_COLLECTION_MINUTES + predicted_delay
    return {
        "predicted_delay": predicted_delay,
        "estimated_collection": _format_time(estimated),
        "status": _status_for_delay(predicted_delay),
        "inputs": {"houses_ready": ready, "houses_waiting": waiting, "readiness_ratio": round(ratio, 3)},
        "explanation": "Estimate generated by the trained Random Forest model from pre-collection houses-ready information. Waiting houses and readiness ratio are derived display values, not independent model features. Actual collection time is not used as a feature.",
    }


def build_dashboard_data() -> dict[str, Any]:
    history = _load_history()
    households = _load_households()
    model, metrics = _build_model(history)
    total_houses = int(len(households))
    ready = int((households["status"] == "Ready").sum())
    waiting = total_houses - ready
    current = predict_delay(ready)
    historical = []
    for _, row in history.iterrows():
        historical.append({
            "day": str(row["day"]),
            "collection_time": row["collection_time"] if pd.notna(row["collection_time"]) else "Not recorded",
            "delay_minutes": int(row["delay_minutes"]) if pd.notna(row["delay_minutes"]) else None,
            "houses_ready": int(row["houses_ready"]),
            "houses_waiting": int(row["houses_waiting"]),
            "status": _status_for_delay(max(0, float(row["delay_minutes"]))) if pd.notna(row["delay_minutes"]) else "Not recorded",
        })
    households = households.drop(columns=["last_updated"], errors="ignore")
    households = households.rename(columns={"last_updated_display": "last_updated"})
    return {
        "summary": {
            "total_houses": total_houses,
            "ready": ready,
            "waiting": waiting,
            "expected_collection": current["estimated_collection"],
            "predicted_delay": current["predicted_delay"],
            "status": current["status"],
        },
        "households": households.to_dict(orient="records"),
        "history": historical,
        "model": {
            "name": "Random Forest Regression",
            "training_records": int(history["delay_minutes"].notna().sum()),
            "normal_time": _format_time(NORMAL_COLLECTION_MINUTES),
            "evaluation": metrics,
            "data_mode": "DEMO DATA — 31 synthetic observations" if os.getenv("SWC_DATA_MODE", "field").lower() == "demo" else "FIELD DATA — 12 supplied observations",
        },
        "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }


def load_data_error() -> str | None:
    try:
        build_dashboard_data()
    except (DataValidationError, OSError, ValueError) as exc:
        return str(exc)
    return None
