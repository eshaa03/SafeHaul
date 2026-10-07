"""
routing/options.py — route options builder with hard filters.

Public function
---------------
build_options(trip_request, segments_map, routes, scored_segments_map,
              service_points, vehicles_map, scenario, now) -> dict

Returns the full /api/trip/options/ response body.

Hard filter order (from TEAM_BRIEF §1.11):
  1. Safety  — exclude any route with a high/closed segment for the given vehicle
  2. Clearance (P1) — placeholder, skipped when clearance_m absent
  3. Shelf life — exclude if eta_latest_hours + hours_already_elapsed > shelf_life_hours

Only surviving routes are converted into options.  At most 3 options are
returned, exactly one is marked recommended=True.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from safehaul import config as cfg
from routing.eta import compute_eta

logger = logging.getLogger("routing")

_KL_TZ = ZoneInfo(cfg.KERALA_TIMEZONE)

# Option type constants
OPT_PROCEED = "proceed"
OPT_REROUTE = "reroute"
OPT_WAIT = "wait"
OPT_DIVERT = "divert_store"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_depart(depart_at_str: str | None) -> datetime:
    if not depart_at_str:
        return datetime.now(_KL_TZ)
    dt = datetime.fromisoformat(depart_at_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_KL_TZ)
    return dt


def _eta_hours(eta: dict) -> float:
    """Return the number of hours from depart_at to the latest ETA."""
    return eta["expected_seconds"] / 3600.0


def _latest_eta_hours(eta: dict, depart: datetime) -> float:
    latest = datetime.fromisoformat(eta["latest"])
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=_KL_TZ)
    return (latest - depart).total_seconds() / 3600.0


def _fuel_cost(route: dict, vehicle_type: str) -> float:
    dist = route.get("distance_km", 0)
    rate = cfg.FUEL_COST_PER_KM_INR.get(vehicle_type, cfg.DEFAULT_FUEL_COST_PER_KM_INR)
    return round(dist * rate, 2)


def _max_risk_on_route(route: dict, scored_map: dict) -> str:
    order = {"low": 0, "medium": 1, "high": 2, "closed": 3}
    worst = "low"
    for sid in route.get("segment_ids", []):
        lvl = scored_map.get(sid, {}).get("risk_level", "low")
        if order.get(lvl, 0) > order.get(worst, 0):
            worst = lvl
    return worst


def _data_source_for_route(route: dict, scored_map: dict) -> str:
    for sid in route.get("segment_ids", []):
        ds = scored_map.get(sid, {}).get("data_source", "simulated")
        if ds == "live":
            return "live"
    return "simulated"


def _recommend_one(options: list[dict]) -> None:
    """Mark exactly one option recommended=True: safest, then fastest."""
    if not options:
        return
    order = {"low": 0, "medium": 1, "high": 2, "closed": 3}
    best = min(
        options,
        key=lambda o: (
            order.get(o.get("max_risk_level", "low"), 0),
            o.get("eta", {}).get("expected_seconds", 99999999),
        ),
    )
    for o in options:
        o["recommended"] = o is best


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_options(
    trip_request: dict,
    scored_segments_map: dict,
    routes: list[dict],
    service_points: list[dict],
    vehicle_type: str = "lcv",
    scenario: str = "normal",
    now: datetime | None = None,
) -> dict:
    if now is None:
        now = datetime.now(_KL_TZ)

    depart_at = _resolve_depart(trip_request.get("depart_at"))
    cargo = trip_request.get("cargo", {})
    shelf_life_h = cargo.get("shelf_life_hours")  # None means no shelf-life constraint
    hours_elapsed = float(cargo.get("hours_already_elapsed", 0))
    cargo_value = float(cargo.get("value_inr", 0))

    options: list[dict] = []
    excluded: list[dict] = []
    all_warnings: list[str] = []

    if scenario == "flood" or any(
        s.get("data_source") == "simulated" for s in scored_segments_map.values()
    ):
        all_warnings.append("Using simulated data — conditions may differ from reality.")

    # ------------------------------------------------------------------
    # Compute baseline ETA (main route at normal/low risk, for reason strings)
    # Override risk levels to "low" so the baseline reflects unimpeded travel.
    # ------------------------------------------------------------------
    main_route = next((r for r in routes if r.get("route_id") == "main"), routes[0] if routes else None)
    baseline_s = None
    if main_route:
        # Build a map with all risk levels set to "low" for baseline purposes
        baseline_map = {
            k: {**v, "risk_level": "low"}
            for k, v in scored_segments_map.items()
        }
        base_eta = compute_eta(main_route, baseline_map, vehicle_type, depart_at)
        baseline_s = base_eta["expected_seconds"]

    # ------------------------------------------------------------------
    # Evaluate each candidate route through hard filters
    # ------------------------------------------------------------------
    for route in routes:
        route_id = route.get("route_id", "?")
        seg_ids = route.get("segment_ids", [])

        # HARD FILTER 1: Safety
        unsafe_segs = [
            sid for sid in seg_ids
            if scored_segments_map.get(sid, {}).get("risk_level") in ("high", "closed")
        ]
        if unsafe_segs:
            excluded.append({
                "route_id": route_id,
                "reason": f"Contains high-risk or closed segment(s): {', '.join(unsafe_segs)}.",
            })
            continue

        # HARD FILTER 2: Clearance (P1 placeholder — skip if no clearance data)
        vehicle_spec = cfg.VEHICLE_SPECS.get(vehicle_type, cfg.VEHICLE_SPECS[cfg.DEFAULT_VEHICLE_TYPE])
        vehicle_h = vehicle_spec.get("height_m", 2.8)
        for sid in seg_ids:
            seg_static = scored_segments_map.get(sid, {})
            clearance = seg_static.get("clearance_m")
            if clearance is not None and clearance < vehicle_h:
                excluded.append({
                    "route_id": route_id,
                    "reason": (
                        f"Clearance on segment {sid} ({clearance} m) is less than "
                        f"vehicle height ({vehicle_h} m)."
                    ),
                })
                break  # already excluded; move to next route
        else:
            # HARD FILTER 3: Shelf life
            eta = compute_eta(route, scored_segments_map, vehicle_type, depart_at, baseline_s)
            latest_h = _latest_eta_hours(eta, depart_at)
            total_elapsed = hours_elapsed + latest_h

            if shelf_life_h is not None and total_elapsed > shelf_life_h:
                excluded.append({
                    "route_id": route_id,
                    "reason": (
                        f"Latest ETA ({latest_h:.1f} h) + elapsed ({hours_elapsed:.1f} h) = "
                        f"{total_elapsed:.1f} h exceeds shelf life of {shelf_life_h} h."
                    ),
                })
                continue

            # Route survived all filters — build option
            remaining_h = (
                round(shelf_life_h - total_elapsed, 2)
                if shelf_life_h is not None else None
            )
            cargo_ok = (shelf_life_h is None) or (total_elapsed <= shelf_life_h)

            opt_type = OPT_PROCEED if route_id == "main" else OPT_REROUTE
            opt_id = f"opt-{len(options) + 1}"
            label = (
                "Proceed on main route"
                if opt_type == OPT_PROCEED
                else f"Reroute via {route.get('name', route_id)}"
            )
            trade_offs = []
            if route_id != "main" and main_route:
                extra_km = route.get("distance_km", 0) - main_route.get("distance_km", 0)
                if extra_km > 0:
                    trade_offs.append(f"Longer by {extra_km:.0f} km vs main route.")
            n_med = sum(
                1 for sid in seg_ids
                if scored_segments_map.get(sid, {}).get("risk_level") == "medium"
            )
            if n_med:
                trade_offs.append(
                    f"{n_med} medium-risk segment(s) — verify before departure."
                )

            options.append({
                "option_id": opt_id,
                "type": opt_type,
                "label": label,
                "route_id": route_id,
                "summary": _build_summary(opt_type, route, scored_segments_map),
                "depart_at": depart_at.isoformat(),
                "eta": {
                    "earliest": eta["earliest"],
                    "latest": eta["latest"],
                    "reason": eta["reason"],
                },
                "distance_km": route.get("distance_km", 0),
                "fuel_cost_inr": _fuel_cost(route, vehicle_type),
                "max_risk_level": _max_risk_on_route(route, scored_segments_map),
                "cargo_window": {
                    "ok": cargo_ok,
                    "remaining_hours_at_latest_eta": remaining_h,
                },
                "trade_offs": trade_offs,
                "recommended": False,
            })

    # ------------------------------------------------------------------
    # Wait option — build from first excluded main-route high segment
    # that has clears_in_hours
    # ------------------------------------------------------------------
    wait_opt = _build_wait_option(
        trip_request, routes, scored_segments_map, vehicle_type,
        depart_at, shelf_life_h, hours_elapsed, baseline_s,
        opt_index=len(options) + 1,
    )
    if wait_opt:
        options.append(wait_opt)

    # ------------------------------------------------------------------
    # Divert-and-store option
    # ------------------------------------------------------------------
    divert_opt = _build_divert_option(
        service_points, scored_segments_map, cargo_value,
        opt_index=len(options) + 1,
        depart_at=depart_at,
    )
    if divert_opt:
        options.append(divert_opt)

    # ------------------------------------------------------------------
    # Cap at 3, mark recommended
    # ------------------------------------------------------------------
    options = options[:3]
    _recommend_one(options)

    message = None
    if not options:
        message = (
            "No safe route option is available within the cargo window. "
            "Contact your dispatcher and consider activating SOS."
        )

    return {
        "generated_at": now.isoformat(),
        "scenario": scenario,
        "data_source": "simulated" if scenario == "flood" else "simulated",
        "options": options,
        "excluded_routes": excluded,
        "warnings": all_warnings,
        "message": message,
    }


# ---------------------------------------------------------------------------
# Sub-builders
# ---------------------------------------------------------------------------

def _build_summary(opt_type: str, route: dict, scored_map: dict) -> str:
    route_id = route.get("route_id", "")
    if opt_type == OPT_PROCEED:
        return "Main route is clear. Proceed with normal caution."
    n_med = sum(
        1 for sid in route.get("segment_ids", [])
        if scored_map.get(sid, {}).get("risk_level") == "medium"
    )
    parts = [f"Alternate route ({route.get('name', route_id)}) avoids high-risk segments."]
    if n_med:
        parts.append(f"{n_med} medium-risk segment(s) remain — monitor conditions.")
    return " ".join(parts)


def _build_wait_option(
    trip_request: dict,
    routes: list,
    scored_map: dict,
    vehicle_type: str,
    depart_at: datetime,
    shelf_life_h: float | None,
    hours_elapsed: float,
    baseline_s: float | None,
    opt_index: int,
) -> dict | None:
    """Build a 'wait' option from the first main-route blocked segment with clears_in_hours."""
    main_route = next((r for r in routes if r.get("route_id") == "main"), None)
    if not main_route:
        return None

    clears_h = None
    for sid in main_route.get("segment_ids", []):
        lvl = scored_map.get(sid, {}).get("risk_level", "low")
        ch = scored_map.get(sid, {}).get("clears_in_hours")
        if lvl in ("high", "closed") and ch is not None:
            clears_h = float(ch)
            break

    if clears_h is None:
        return None

    new_depart = depart_at + timedelta(hours=clears_h)
    # Re-score isn't available here — use unscored route as if all segments become low
    # (conservative: still use same scored_map but check shelf life only)
    wait_eta = compute_eta(main_route, scored_map, vehicle_type, new_depart, baseline_s)
    latest_h = _latest_eta_hours(wait_eta, new_depart)
    total_elapsed = hours_elapsed + clears_h + latest_h

    if shelf_life_h is not None and total_elapsed > shelf_life_h:
        return None  # waiting would still spoil the cargo

    cargo_ok = shelf_life_h is None or total_elapsed <= shelf_life_h
    remaining_h = round(shelf_life_h - total_elapsed, 2) if shelf_life_h is not None else None

    return {
        "option_id": f"opt-{opt_index}",
        "type": OPT_WAIT,
        "label": f"Wait {clears_h:.0f} h for conditions to clear",
        "route_id": "main",
        "summary": (
            f"Main route expected to clear in ~{clears_h:.0f} h. "
            "Depart after the window to avoid flood risk."
        ),
        "depart_at": new_depart.isoformat(),
        "eta": {
            "earliest": wait_eta["earliest"],
            "latest": wait_eta["latest"],
            "reason": f"Delayed departure by {clears_h:.0f} h; {wait_eta['reason']}",
        },
        "distance_km": main_route.get("distance_km", 0),
        "fuel_cost_inr": _fuel_cost(main_route, vehicle_type),
        "max_risk_level": "low",
        "cargo_window": {"ok": cargo_ok, "remaining_hours_at_latest_eta": remaining_h},
        "trade_offs": [
            f"Delay of {clears_h:.0f} h required before departure.",
            "Conditions assumed to clear — not guaranteed.",
        ],
        "recommended": False,
    }


def _build_divert_option(
    service_points: list,
    scored_map: dict,
    cargo_value: float,
    opt_index: int,
    depart_at: datetime,
) -> dict | None:
    """Build a divert_store option using the nearest reachable cold store."""
    cold_stores = [p for p in service_points if p.get("category") == "cold_store"]
    if not cold_stores:
        return None

    reachable = [
        p for p in cold_stores
        if _is_reachable(p, scored_map)
    ]
    if not reachable:
        return None

    store = reachable[0]
    detour_m = float(store.get("detour_minutes", 15))
    arrive_dt = depart_at + timedelta(minutes=detour_m)

    # Heuristic value saved (mock estimate — labelled as such)
    value_saved = round(cargo_value * cfg.COLD_STORE_RECOVERY_FRACTION, 2)

    return {
        "option_id": f"opt-{opt_index}",
        "type": OPT_DIVERT,
        "label": f"Divert and store at {store.get('name', 'cold store')}",
        "route_id": None,
        "summary": (
            f"Route is blocked. Divert cargo to nearby cold storage "
            f"({store.get('name', 'cold store')}) to prevent spoilage."
        ),
        "depart_at": depart_at.isoformat(),
        "eta": {
            "earliest": arrive_dt.isoformat(),
            "latest": arrive_dt.isoformat(),
            "reason": f"Approx. {detour_m:.0f} min detour to cold store.",
        },
        "distance_km": None,
        "fuel_cost_inr": None,
        "max_risk_level": "low",
        "cargo_window": {"ok": True, "remaining_hours_at_latest_eta": None},
        "trade_offs": [
            f"Estimated value preserved: ₹{value_saved:,.0f} (mock estimate — {int(cfg.COLD_STORE_RECOVERY_FRACTION*100)}% of cargo value).",
            "Cold-store availability is simulated — confirm before diverting.",
        ],
        "estimated_value_saved_inr": value_saved,
        "recommended": False,
    }


def _is_reachable(service_point: dict, scored_map: dict) -> bool:
    """Simple reachability: no high/closed segment before the attach point."""
    attach = service_point.get("attach_segment_id")
    if not attach:
        return True
    seg = scored_map.get(attach, {})
    return seg.get("risk_level", "low") not in ("high", "closed")
