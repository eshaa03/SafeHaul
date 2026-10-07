"""
servicepoints/ranking.py — service-point reachability and ranking.

Public function
---------------
rank_service_points(points, route, scored_segments_map, vehicle_type,
                    position_segment_id, mode) -> list[dict]

Returns a list of service-point objects sorted:
  1. reachable=True first
  2. reachable_minutes ascending

A point is unreachable if any segment between the current position
(position_segment_id) and the point's attach_segment_id is high/closed.
"""

from __future__ import annotations

import logging

from safehaul import config as cfg

logger = logging.getLogger("servicepoints")


def rank_service_points(
    points: list[dict],
    route: dict,
    scored_segments_map: dict,
    vehicle_type: str = "lcv",
    position_segment_id: str | None = None,
    mode: str = "normal",
) -> list[dict]:
    """
    Parameters
    ----------
    points              : raw service-point dicts (from data loader)
    route               : the route dict (segment_ids in order)
    scored_segments_map : {segment_id -> scored segment dict}
    vehicle_type        : for future depth/clearance checks
    position_segment_id : vehicle's current segment (default: first segment)
    mode                : "normal" or "emergency" (filters categories)
    """
    seg_ids: list[str] = route.get("segment_ids", [])

    # Determine vehicle's position index in the route
    if position_segment_id and position_segment_id in seg_ids:
        pos_idx = seg_ids.index(position_segment_id)
    else:
        pos_idx = 0

    # Emergency mode restricts categories
    if mode == "emergency":
        points = [p for p in points if p.get("category") in cfg.EMERGENCY_MODE_CATEGORIES]

    result = []
    for pt in points:
        attach = pt.get("attach_segment_id")
        detour_m = float(pt.get("detour_minutes", 0))

        # Find attach segment in route
        if attach and attach in seg_ids:
            attach_idx = seg_ids.index(attach)
        else:
            attach_idx = None

        # Determine reachability: check segments between pos and attach
        reachable = True
        block_reason = None
        reachable_minutes = None

        if attach_idx is not None:
            # Segments the truck must pass through to reach this point
            path_ids = seg_ids[pos_idx: attach_idx + 1]
            for sid in path_ids:
                lvl = scored_segments_map.get(sid, {}).get("risk_level", "low")
                if lvl in ("high", "closed"):
                    reachable = False
                    block_reason = f"Blocked by segment {sid} ({lvl} risk)."
                    break

            if reachable:
                # Compute along-route drive time + detour
                drive_s = 0.0
                for sid in path_ids:
                    scored = scored_segments_map.get(sid, {})
                    length_km = float(scored.get("length_km", 0))
                    road_class = scored.get("road_class", "highway")
                    risk_level = scored.get("risk_level", "low")
                    speed = cfg.BASE_SPEEDS_KMH.get(road_class, cfg.DEFAULT_BASE_SPEED_KMH)
                    mult = cfg.SPEED_MULTIPLIER.get(risk_level, 1.0)
                    if mult > 0:
                        drive_s += (length_km / (speed * mult)) * 3600
                reachable_minutes = round(drive_s / 60 + detour_m, 1)
        else:
            # Point not on this route — mark unreachable with explanation
            reachable = False
            block_reason = "Service point is not on the selected route."

        # Risk level of the attach segment (for informational display)
        attach_risk = (
            scored_segments_map.get(attach, {}).get("risk_level", "low")
            if attach else "low"
        )

        result.append({
            **pt,
            "reachable": reachable,
            "reachable_minutes": reachable_minutes,
            "reason": block_reason,
            "risk_level": attach_risk,
        })

    # Sort: reachable first, then by reachable_minutes (None last)
    result.sort(key=lambda p: (
        0 if p["reachable"] else 1,
        p["reachable_minutes"] if p["reachable_minutes"] is not None else 999999,
    ))
    return result
