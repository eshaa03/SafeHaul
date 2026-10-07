"""
risk/views.py — scenario toggle, routes, and segment risk endpoint.
"""

import logging
from datetime import datetime, timezone

from rest_framework.response import Response
from rest_framework.views import APIView

from safehaul.data_loader import get_routes, get_segments, get_scenarios
from risk.engine import score_segment

logger = logging.getLogger("risk")

# ---------------------------------------------------------------------------
# Server-wide scenario state
# ---------------------------------------------------------------------------
_SERVER_SCENARIO: str = "normal"
VALID_SCENARIOS = {"normal", "flood"}


def get_server_scenario() -> str:
    return _SERVER_SCENARIO


class ScenarioView(APIView):
    """GET/POST /api/scenario/"""

    def get(self, request):
        return Response({"scenario": get_server_scenario()})

    def post(self, request):
        global _SERVER_SCENARIO
        scenario = request.data.get("scenario")
        if scenario not in VALID_SCENARIOS:
            return Response(
                {"error": f"Invalid scenario '{scenario}'. Choose from: {sorted(VALID_SCENARIOS)}."},
                status=400,
            )
        _SERVER_SCENARIO = scenario
        logger.info("Scenario switched to '%s'.", scenario)
        return Response({"scenario": _SERVER_SCENARIO})


class RoutesView(APIView):
    """GET /api/routes/"""

    def get(self, request):
        routes = get_routes()
        if not routes:
            return Response({"error": "No route data available."}, status=503)
        return Response(routes)


class SegmentsView(APIView):
    """GET /api/segments/?scenario="""

    def get(self, request):
        scenario = request.query_params.get("scenario") or get_server_scenario()
        vehicle_type = request.query_params.get("vehicle_type", "lcv")

        segments = get_segments()
        scenarios = get_scenarios()

        if not segments:
            return Response({"error": "No segment data available."}, status=503)

        scenario_data = scenarios.get(scenario, {})
        dynamic_by_seg = scenario_data.get("segments", {})
        scenario_ts = scenario_data.get("timestamp")
        scenario_source = scenario_data.get("data_source", "simulated")

        now = datetime.now(timezone.utc)
        result = []
        for seg in segments:
            seg_id = seg["segment_id"]
            raw_dyn = dynamic_by_seg.get(seg_id, {})
            # Inject scenario-level timestamp if segment doesn't have its own
            dynamic = {
                "data_source": scenario_source,
                "data_timestamp": scenario_ts,
                **raw_dyn,
            }
            scored = score_segment(seg, dynamic, vehicle_type, now)
            result.append(scored)

        return Response(result)
