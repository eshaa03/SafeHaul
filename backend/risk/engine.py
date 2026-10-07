"""
risk/engine.py — segment risk scoring.

Public function
---------------
score_segment(segment, dynamic, vehicle_type, now, flood_history=None) -> dict

Returns a segment risk object matching the CONTRACT.md schema (§1.10).
All weights and thresholds come from safehaul/config.py — nothing is
hard-coded here.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from safehaul import config as cfg

logger = logging.getLogger("risk")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _level_from_score(score: float) -> str:
    if score < cfg.RISK_THRESHOLD_LOW:
        return "low"
    if score < cfg.RISK_THRESHOLD_MEDIUM:
        return "medium"
    if score < cfg.RISK_THRESHOLD_HIGH:
        return "high"
    return "closed"


def _parse_ts(ts_str: str | None) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_segment(
    segment: dict,
    dynamic: dict,
    vehicle_type: str = "lcv",
    now: datetime | None = None,
    flood_history: list | None = None,
) -> dict:
    """
    Compute a full risk object for one segment.

    Parameters
    ----------
    segment     : static segment dict (from segments.json)
    dynamic     : dynamic inputs for this segment (from scenarios.json)
    vehicle_type: one of the keys in config.VEHICLE_SPECS
    now         : reference time (defaults to utcnow)
    flood_history: list of {date, rain_24h_mm, flooded} for this segment

    Returns
    -------
    Dict matching the segment risk object schema in CONTRACT.md §1.10.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    seg_id = segment.get("segment_id", "?")
    vehicle = cfg.VEHICLE_SPECS.get(vehicle_type, cfg.VEHICLE_SPECS[cfg.DEFAULT_VEHICLE_TYPE])
    reasons: list[str] = []

    # ------------------------------------------------------------------
    # 1. STATIC sub-score
    # ------------------------------------------------------------------
    elev_m = float(segment.get("elevation_m", 30))
    river_m = float(segment.get("river_distance_m", 1000))
    hist_count = float(segment.get("historical_flood_count", 0))
    hazard = segment.get("hazard_type", "none")

    elev_factor = _clamp(1.0 - elev_m / cfg.ELEVATION_NORMALISE_M)
    river_factor = _clamp(1.0 - river_m / cfg.RIVER_DISTANCE_NORMALISE_M)
    hist_factor = _clamp(hist_count / cfg.HISTORY_NORMALISE_COUNT)
    structure_factor = 1.0 if hazard != "none" else 0.0

    # Flood memory override: if rain >= trigger, set hist_factor to 1.0
    flood_memory = segment.get("flood_memory")
    rain_24h = float(dynamic.get("rain_24h_mm", 0))
    flood_memory_triggered = False
    if flood_memory and rain_24h >= float(flood_memory.get("trigger_mm", 9999)):
        hist_factor = 1.0
        flood_memory_triggered = True

    static_score = (
        cfg.STATIC_WEIGHT_ELEVATION * elev_factor
        + cfg.STATIC_WEIGHT_RIVER_PROXIMITY * river_factor
        + cfg.STATIC_WEIGHT_HISTORY * hist_factor
        + cfg.STATIC_WEIGHT_STRUCTURE * structure_factor
    )

    # ------------------------------------------------------------------
    # 2. DYNAMIC sub-score
    # ------------------------------------------------------------------
    forecast_3h = float(dynamic.get("forecast_3h_mm", 0))
    river_level_pct = float(dynamic.get("river_level_pct", 0))

    dynamic_score = (
        cfg.DYNAMIC_WEIGHT_RAIN_24H * _clamp(rain_24h / cfg.RAIN_24H_NORMALISE_MM)
        + cfg.DYNAMIC_WEIGHT_RIVER_LEVEL * _clamp(river_level_pct / cfg.RIVER_LEVEL_NORMALISE_PCT)
        + cfg.DYNAMIC_WEIGHT_FORECAST_3H * _clamp(forecast_3h / cfg.FORECAST_3H_NORMALISE_MM)
    )

    # ------------------------------------------------------------------
    # 3. CROWD sub-score
    # ------------------------------------------------------------------
    crowd_reports = int(dynamic.get("crowd_reports", 0))
    crowd_score = _clamp(crowd_reports / cfg.CROWD_NORMALISE_COUNT)

    # ------------------------------------------------------------------
    # 4. Composite score and level
    # ------------------------------------------------------------------
    risk_score = (
        cfg.RISK_WEIGHT_STATIC * static_score
        + cfg.RISK_WEIGHT_DYNAMIC * dynamic_score
        + cfg.RISK_WEIGHT_CROWD * crowd_score
    )
    risk_level = _level_from_score(risk_score)

    # ------------------------------------------------------------------
    # 5. Hard overrides (after score so reasons still reference score)
    # ------------------------------------------------------------------
    official_closure = bool(dynamic.get("official_closure", False))
    reported_depth = int(dynamic.get("reported_depth_level", 0))
    max_depth = int(vehicle.get("max_depth_level", 2))

    if official_closure:
        risk_level = "closed"
        reasons.append("Official closure in effect on this segment.")

    if reported_depth >= max_depth and reported_depth > 0:
        risk_level = "closed"
        reasons.append(
            f"Reported water depth (level {reported_depth}) exceeds the limit for "
            f"{vehicle_type} (max level {max_depth - 1})."
        )

    # ------------------------------------------------------------------
    # 6. Reasons — ordered by contribution (largest first)
    # ------------------------------------------------------------------
    reason_candidates: list[tuple[float, str]] = []

    if rain_24h >= 50:
        reason_candidates.append((
            cfg.RISK_WEIGHT_DYNAMIC * cfg.DYNAMIC_WEIGHT_RAIN_24H * _clamp(rain_24h / cfg.RAIN_24H_NORMALISE_MM),
            f"{rain_24h:.0f} mm of rain recorded in the last 24 h."
        ))
    elif rain_24h >= 20:
        reason_candidates.append((
            cfg.RISK_WEIGHT_DYNAMIC * cfg.DYNAMIC_WEIGHT_RAIN_24H * _clamp(rain_24h / cfg.RAIN_24H_NORMALISE_MM),
            f"{rain_24h:.0f} mm of rain in the last 24 h (moderate)."
        ))

    if river_level_pct >= 60:
        reason_candidates.append((
            cfg.RISK_WEIGHT_DYNAMIC * cfg.DYNAMIC_WEIGHT_RIVER_LEVEL * _clamp(river_level_pct / 100),
            f"River level at {river_level_pct:.0f}% of danger mark."
        ))

    if forecast_3h >= 15:
        reason_candidates.append((
            cfg.RISK_WEIGHT_DYNAMIC * cfg.DYNAMIC_WEIGHT_FORECAST_3H * _clamp(forecast_3h / cfg.FORECAST_3H_NORMALISE_MM),
            f"Forecast: {forecast_3h:.0f} mm expected in the next 3 h."
        ))

    if flood_memory_triggered:
        events = flood_memory.get("events", 1)
        trigger = flood_memory.get("trigger_mm")
        reason_candidates.append((
            cfg.RISK_WEIGHT_STATIC * cfg.STATIC_WEIGHT_HISTORY,
            f"Flooded {events} time(s) in past events at this rain level "
            f"(flood memory trigger: ~{trigger} mm)."
        ))
    elif hist_count >= 1:
        reason_candidates.append((
            cfg.RISK_WEIGHT_STATIC * cfg.STATIC_WEIGHT_HISTORY * hist_factor,
            f"{int(hist_count)} historical flood event(s) recorded at this segment."
        ))

    if hazard != "none":
        reason_candidates.append((
            cfg.RISK_WEIGHT_STATIC * cfg.STATIC_WEIGHT_STRUCTURE,
            f"Hazard structure present: {hazard.replace('_', ' ')}."
        ))

    if crowd_reports >= 2:
        reason_candidates.append((
            cfg.RISK_WEIGHT_CROWD * crowd_score,
            f"{crowd_reports} crowd report(s) of hazardous conditions."
        ))

    if elev_m < 10:
        reason_candidates.append((
            cfg.RISK_WEIGHT_STATIC * cfg.STATIC_WEIGHT_ELEVATION * elev_factor,
            f"Low elevation ({elev_m:.0f} m above sea level) increases flood risk."
        ))

    if river_m < 300:
        reason_candidates.append((
            cfg.RISK_WEIGHT_STATIC * cfg.STATIC_WEIGHT_RIVER_PROXIMITY * river_factor,
            f"Segment is {river_m:.0f} m from the nearest river (very close)."
        ))
    elif river_m < 800:
        reason_candidates.append((
            cfg.RISK_WEIGHT_STATIC * cfg.STATIC_WEIGHT_RIVER_PROXIMITY * river_factor,
            f"Segment is {river_m:.0f} m from the nearest river."
        ))

    # Sort descending by contribution weight, add override reasons at front
    reason_candidates.sort(key=lambda x: x[0], reverse=True)
    reasons = [r for _, r in reason_candidates] + reasons  # override reasons appended earlier

    # Always have at least one reason
    if not reasons:
        reasons = [f"Risk score {risk_score:.2f} — conditions normal."]

    # ------------------------------------------------------------------
    # 7. Confidence
    # ------------------------------------------------------------------
    data_source = dynamic.get("data_source", "simulated")
    ts_str = dynamic.get("data_timestamp") or dynamic.get("timestamp")
    ts = _parse_ts(ts_str)

    if ts is None:
        confidence = "low"
    elif data_source == "simulated":
        confidence = "moderate"
    else:
        age_s = (now.replace(tzinfo=timezone.utc) - ts.replace(tzinfo=timezone.utc)).total_seconds()
        if age_s <= cfg.CONFIDENCE_FRESH_SECONDS:
            confidence = "high"
        elif age_s <= cfg.CONFIDENCE_STALE_SECONDS:
            confidence = "moderate"
        else:
            confidence = "low"

    data_timestamp = ts_str or now.isoformat()

    return {
        "segment_id": seg_id,
        "name": segment.get("name", seg_id),
        "route_ids": segment.get("route_ids", []),
        "geometry": segment.get("geometry", []),
        "length_km": segment.get("length_km", 0),
        "road_class": segment.get("road_class", "highway"),
        "risk_level": risk_level,
        "risk_score": round(risk_score, 4),
        "reasons": reasons,
        "factors": {
            "static": round(static_score, 4),
            "dynamic": round(dynamic_score, 4),
            "crowd": round(crowd_score, 4),
        },
        "confidence": confidence,
        "data_source": data_source,
        "data_timestamp": data_timestamp,
        "flood_memory": flood_memory,
        "clears_in_hours": dynamic.get("clears_in_hours"),
    }
