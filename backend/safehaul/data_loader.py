"""
SafeHaul Kerala — data loader.

Reads JSON files from DATA_DIR (data/ in the repo root).
Falls back to backend/tests/fixtures/ if a file is missing and logs a visible
WARNING so every team member knows they are running on stand-in data.

Public API
----------
load_data()          – (re-)load all files; called once at startup by SafehaulConfig.ready()
get_segments()       – list of segment dicts
get_routes()         – list of route dicts
get_scenarios()      – dict keyed by scenario name
get_service_points() – list of service-point dicts
get_vehicles()       – dict keyed by vehicle_type
get_fleet()          – list of fleet vehicle dicts
get_emergency_codes()– dict keyed by code string
"""

import json
import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger("safehaul")

# ---------------------------------------------------------------------------
# Module-level cache — populated by load_data()
# ---------------------------------------------------------------------------
_cache: dict = {}

# The fixture directory (stand-in until C delivers data/)
_FIXTURE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# Mapping of logical name → filename
_FILES = {
    "segments":       "segments.json",
    "routes":         "routes.json",
    "scenarios":      "scenarios.json",
    "service_points": "service_points.json",
    "vehicles":       "vehicles.json",
    "fleet":          "fleet.json",
    "emergency_codes":"emergency_codes.json",
}


def _load_file(name: str, filename: str) -> object:
    """Try DATA_DIR first; fall back to fixture with a WARNING."""
    data_path = settings.DATA_DIR / filename
    if data_path.exists():
        with open(data_path, encoding="utf-8") as f:
            logger.info("Loaded %s from data/%s", name, filename)
            return json.load(f)

    fixture_path = _FIXTURE_DIR / filename
    if fixture_path.exists():
        with open(fixture_path, encoding="utf-8") as f:
            logger.warning(
                "⚠  data/%s not found — using STAND-IN FIXTURE from tests/fixtures/%s. "
                "This is simulated data.",
                filename,
                filename,
            )
            return json.load(f)

    logger.warning(
        "⚠  %s not found in data/ or tests/fixtures/ — returning empty value for '%s'.",
        filename,
        name,
    )
    # Return a sensible empty value per data shape
    return {} if name in ("scenarios", "vehicles", "emergency_codes") else []


def load_data() -> None:
    """Load (or reload) all data files into the module-level cache."""
    global _cache
    _cache = {name: _load_file(name, filename) for name, filename in _FILES.items()}
    logger.info("SafeHaul data loader: all files loaded.")


def _require(name: str):
    """Return cached data, loading if the cache is somehow empty."""
    if not _cache:
        load_data()
    return _cache.get(name)


def get_segments() -> list:
    return _require("segments") or []


def get_routes() -> list:
    return _require("routes") or []


def get_scenarios() -> dict:
    return _require("scenarios") or {}


def get_service_points() -> list:
    return _require("service_points") or []


def get_vehicles() -> dict:
    """Returns a dict keyed by vehicle_type."""
    raw = _require("vehicles")
    if isinstance(raw, list):
        return {v["vehicle_type"]: v for v in raw}
    return raw or {}


def get_fleet() -> list:
    return _require("fleet") or []


def get_emergency_codes() -> dict:
    """Returns a dict keyed by code string (e.g. '01')."""
    raw = _require("emergency_codes")
    if isinstance(raw, list):
        return {str(item["code"]): item for item in raw}
    return raw or {}
