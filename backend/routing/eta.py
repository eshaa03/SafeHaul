"""
routing/eta.py — ETA computation.

Public function
---------------
compute_eta(route, scored_segments_map, vehicle_type, depart_at) -> dict

Returns:
  {
    "expected_seconds": int,
    "earliest": ISO string,
    "latest":   ISO string,
    "reason":   str,
  }

All constants from safehaul/config.py.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from safehaul import config as cfg

_KL_TZ = ZoneInfo(cfg.KERALA_TIMEZONE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_speed(road_class: str) -> float:
    return cfg.BASE_SPEEDS_KMH.get(road_class, cfg.DEFAULT_BASE_SPEED_KMH)


def _in_peak_hour(dt: datetime) -> bool:
    h = dt.hour
    for start, end in cfg.PEAK_HOURS:
        if start <= h < end:
            return True
    return False


def _round_up_to(seconds: float, to_minutes: int) -> float:
    """Round seconds up to the nearest `to_minutes` minute boundary."""
    to_s = to_minutes * 60
    return math.ceil(seconds / to_s) * to_s


# ---------------------------------------------------------------------------
# Main ETA function
# ---------------------------------------------------------------------------

def compute_eta(
    route: dict,
    scored_segments_map: dict,
    vehicle_type: str = "lcv",
    depart_at: str | datetime | None = None,
    baseline_seconds: float | None = None,
) -> dict:
    """
    Compute ETA for a route given already-scored segments.

    Parameters
    ----------
    route               : route dict with "segment_ids" list
    scored_segments_map : {segment_id -> scored segment dict} for the current scenario
    vehicle_type        : used for fuel cost
    depart_at           : ISO string or datetime; defaults to "now"
    baseline_seconds    : optional normal-route expected seconds for the reason string

    Returns
    -------
    dict with expected_seconds, earliest, latest (ISO strings), reason (str)
    """
    if depart_at is None:
        depart_at = datetime.now(_KL_TZ)
    elif isinstance(depart_at, str):
        depart_at = datetime.fromisoformat(depart_at)
        if depart_at.tzinfo is None:
            depart_at = depart_at.replace(tzinfo=_KL_TZ)

    segment_ids = route.get("segment_ids", [])
    total_drive_s = 0.0
    accumulated_drive_s = 0.0
    total_rest_s = 0.0
    n_medium = 0
    current_time = depart_at

    rest_threshold_s = cfg.REST_AFTER_DRIVING_HOURS * 3600
    rest_break_s = cfg.REST_BREAK_MINUTES * 60

    for seg_id in segment_ids:
        scored = scored_segments_map.get(seg_id, {})
        length_km = float(scored.get("length_km", 0))
        road_class = scored.get("road_class", "highway")
        risk_level = scored.get("risk_level", "low")

        if risk_level == "medium":
            n_medium += 1

        speed = _base_speed(road_class)
        risk_mult = cfg.SPEED_MULTIPLIER.get(risk_level, 1.0)

        # Peak-hour multiplier: apply if the segment starts in a peak window
        peak_mult = cfg.PEAK_HOUR_MULTIPLIER if _in_peak_hour(current_time) else 1.0

        effective_speed = speed * risk_mult / peak_mult  # peak slows things down
        if effective_speed <= 0:
            effective_speed = 1.0  # safety guard

        seg_s = (length_km / effective_speed) * 3600
        total_drive_s += seg_s
        accumulated_drive_s += seg_s

        current_time += timedelta(seconds=seg_s)

        # Insert rest break if accumulated driving exceeds threshold
        if accumulated_drive_s >= rest_threshold_s:
            total_rest_s += rest_break_s
            current_time += timedelta(seconds=rest_break_s)
            accumulated_drive_s = 0.0

    expected_s = total_drive_s + total_rest_s

    earliest_s = expected_s * cfg.ETA_EARLIEST_FACTOR
    latest_s = _round_up_to(
        expected_s * (cfg.ETA_LATEST_BASE_FACTOR + cfg.ETA_LATEST_PER_MEDIUM_SEGMENT * n_medium),
        cfg.ETA_ROUND_TO_MINUTES,
    )

    earliest_dt = depart_at + timedelta(seconds=earliest_s)
    latest_dt = depart_at + timedelta(seconds=latest_s)

    # ------------------------------------------------------------------
    # Reason string — explain largest deviation vs baseline
    # ------------------------------------------------------------------
    reason_parts: list[str] = []

    if baseline_seconds is not None:
        delta_min = (expected_s - baseline_seconds) / 60
        if abs(delta_min) >= 5:
            sign = "+" if delta_min > 0 else ""
            reason_parts.append(f"{sign}{delta_min:.0f} min vs normal route")

    route_dist = route.get("distance_km")
    if route_dist:
        reason_parts.append(f"route {route_dist:.0f} km")

    if n_medium > 0:
        reason_parts.append(f"{n_medium} medium-risk segment(s) slow progress")

    if total_rest_s > 0:
        n_breaks = int(total_rest_s / rest_break_s)
        reason_parts.append(f"{n_breaks} rest break(s) of {cfg.REST_BREAK_MINUTES} min")

    if not reason_parts:
        reason_parts.append("normal conditions")

    reason = "; ".join(reason_parts)

    return {
        "expected_seconds": int(expected_s),
        "earliest": earliest_dt.isoformat(),
        "latest": latest_dt.isoformat(),
        "reason": reason,
    }
