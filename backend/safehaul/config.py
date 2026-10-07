"""
SafeHaul Kerala — ALL tunable constants live here.

Rule (from AGENTS.md): do NOT hard-code any of these values elsewhere in the codebase.
Import from this module: `from safehaul.config import RISK_WEIGHTS, BASE_SPEEDS, ...`

Sources: docs/TEAM_BRIEF.md §1.11 and §1.8.
"""

# ---------------------------------------------------------------------------
# Risk score weights (must sum to 1.0 within each group)
# ---------------------------------------------------------------------------

# Top-level combination weights
RISK_WEIGHT_STATIC: float = 0.35
RISK_WEIGHT_DYNAMIC: float = 0.50
RISK_WEIGHT_CROWD: float = 0.15

# Static sub-factor weights (must sum to 1.0)
STATIC_WEIGHT_ELEVATION: float = 0.30
STATIC_WEIGHT_RIVER_PROXIMITY: float = 0.25
STATIC_WEIGHT_HISTORY: float = 0.25
STATIC_WEIGHT_STRUCTURE: float = 0.20

# Dynamic sub-factor weights (must sum to 1.0)
DYNAMIC_WEIGHT_RAIN_24H: float = 0.40
DYNAMIC_WEIGHT_RIVER_LEVEL: float = 0.35
DYNAMIC_WEIGHT_FORECAST_3H: float = 0.25

# ---------------------------------------------------------------------------
# Static factor normalisation denominators
# ---------------------------------------------------------------------------
ELEVATION_NORMALISE_M: float = 60.0        # elevation_m / this, then clamp to [0, 1]
RIVER_DISTANCE_NORMALISE_M: float = 2000.0 # river_distance_m / this, then clamp
HISTORY_NORMALISE_COUNT: float = 3.0       # historical_flood_count / this, then clamp

# ---------------------------------------------------------------------------
# Dynamic factor normalisation denominators
# ---------------------------------------------------------------------------
RAIN_24H_NORMALISE_MM: float = 120.0       # rain_24h_mm / this, then clamp
RIVER_LEVEL_NORMALISE_PCT: float = 100.0   # river_level_pct / this, then clamp
FORECAST_3H_NORMALISE_MM: float = 40.0     # forecast_3h_mm / this, then clamp

# Crowd factor normalisation
CROWD_NORMALISE_COUNT: float = 3.0         # crowd_reports / this, then clamp

# ---------------------------------------------------------------------------
# Risk level thresholds (score boundaries, exclusive upper bound)
# ---------------------------------------------------------------------------
RISK_THRESHOLD_LOW: float = 0.30     # score < 0.30 → low
RISK_THRESHOLD_MEDIUM: float = 0.55  # 0.30 ≤ score < 0.55 → medium
RISK_THRESHOLD_HIGH: float = 0.80    # 0.55 ≤ score < 0.80 → high
                                     # score ≥ 0.80 → closed

# Minimum contributing factor weight to generate a reason for that factor
REASON_CONTRIBUTION_THRESHOLD: float = 0.05

# ---------------------------------------------------------------------------
# Confidence rules
# ---------------------------------------------------------------------------
# Max age (seconds) for a data item to still count as "fresh" (→ high confidence)
CONFIDENCE_FRESH_SECONDS: int = 3600        # 1 hour
# Age beyond which confidence drops to "low" even if simulated
CONFIDENCE_STALE_SECONDS: int = 10800       # 3 hours

# ---------------------------------------------------------------------------
# ETA base speeds by road_class (km/h)
# ---------------------------------------------------------------------------
BASE_SPEEDS_KMH: dict = {
    "highway": 45.0,
    "state_road": 30.0,
    "district_road": 25.0,  # fallback; not in brief but defensive
    "urban": 20.0,           # fallback
}
DEFAULT_BASE_SPEED_KMH: float = 30.0  # used when road_class is unknown

# ---------------------------------------------------------------------------
# ETA risk-level speed multipliers
# ---------------------------------------------------------------------------
SPEED_MULTIPLIER: dict = {
    "low": 1.0,
    "medium": 0.75,
    "high": 0.4,    # only used for wait/compare view; high routes are hard-filtered out
    "closed": 0.0,  # should never be driven; defensive
}

# ---------------------------------------------------------------------------
# ETA range factors
# ---------------------------------------------------------------------------
ETA_EARLIEST_FACTOR: float = 0.92          # earliest = expected * this
ETA_LATEST_BASE_FACTOR: float = 1.10       # latest base = expected * this
ETA_LATEST_PER_MEDIUM_SEGMENT: float = 0.05  # +5% per medium-risk segment on the route
ETA_ROUND_TO_MINUTES: int = 5             # round latest up to nearest N minutes

# ---------------------------------------------------------------------------
# Peak-hour multiplier
# ---------------------------------------------------------------------------
PEAK_HOUR_MULTIPLIER: float = 1.2
PEAK_HOURS: list = [
    (8, 10),   # 08:00 – 10:00 inclusive
    (17, 19),  # 17:00 – 19:00 inclusive
]

# ---------------------------------------------------------------------------
# Rest-break rule
# ---------------------------------------------------------------------------
REST_AFTER_DRIVING_HOURS: float = 4.5   # add a break after this many driving hours
REST_BREAK_MINUTES: int = 30            # duration of each break in minutes

# ---------------------------------------------------------------------------
# Fuel cost per km (INR) by vehicle type
# ---------------------------------------------------------------------------
FUEL_COST_PER_KM_INR: dict = {
    "lcv": 14.0,
    "mini_truck": 12.0,
    "heavy_truck": 20.0,
    "tipper": 18.0,
}
DEFAULT_FUEL_COST_PER_KM_INR: float = 14.0  # fallback

# ---------------------------------------------------------------------------
# Vehicle capabilities (max_depth_level and height_m)
# Values are assumptions from TEAM_BRIEF §1.11; E to verify.
# ---------------------------------------------------------------------------
VEHICLE_SPECS: dict = {
    "mini_truck":  {"max_depth_level": 1, "height_m": 2.2},
    "lcv":         {"max_depth_level": 2, "height_m": 2.8},
    "heavy_truck": {"max_depth_level": 3, "height_m": 3.8},
    "tipper":      {"max_depth_level": 3, "height_m": 3.5},
}
DEFAULT_VEHICLE_TYPE: str = "lcv"

# ---------------------------------------------------------------------------
# Divert-and-store spoilage heuristic
# (clearly labelled as a mock estimate in all API responses)
# ---------------------------------------------------------------------------
# Fraction of cargo value assumed lost per hour of delay past the shelf-life window.
SPOILAGE_VALUE_LOSS_PER_HOUR_FRACTION: float = 0.15
# Fraction of cargo value recoverable by diverting to a cold store (mock assumption).
COLD_STORE_RECOVERY_FRACTION: float = 0.70

# ---------------------------------------------------------------------------
# Service-point reachability
# ---------------------------------------------------------------------------
# Categories shown in mode=emergency (all others are filtered out)
EMERGENCY_MODE_CATEGORIES: list = ["hospital", "police", "fire", "safe_halt"]

# ---------------------------------------------------------------------------
# Timezone
# ---------------------------------------------------------------------------
KERALA_TIMEZONE: str = "Asia/Kolkata"  # UTC+5:30
