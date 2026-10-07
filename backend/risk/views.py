"""
risk/views.py — scenario toggle and routes pass-through.

Endpoints owned here (A1):
  GET  /api/scenario/
  POST /api/scenario/
  GET  /api/routes/

Risk engine and /api/segments/ are added in A2.
"""

import logging

from rest_framework.response import Response
from rest_framework.views import APIView

from safehaul.data_loader import get_routes

logger = logging.getLogger("risk")

# ---------------------------------------------------------------------------
# Server-wide scenario state
# Stored as a module-level variable so it persists across requests in a
# single process. For the hackathon demo this is sufficient.
# Every endpoint also accepts a ?scenario= query-param override.
# ---------------------------------------------------------------------------
_SERVER_SCENARIO: str = "normal"
VALID_SCENARIOS = {"normal", "flood"}


def get_server_scenario() -> str:
    return _SERVER_SCENARIO


class ScenarioView(APIView):
    """
    GET  /api/scenario/  → {"scenario": "normal"}
    POST /api/scenario/  body: {"scenario": "flood"} → {"scenario": "flood"}
    """

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
    """
    GET /api/routes/  → list of route metadata objects
    """

    def get(self, request):
        routes = get_routes()
        if not routes:
            return Response(
                {"error": "No route data available. Check data/ or tests/fixtures/."},
                status=503,
            )
        return Response(routes)
