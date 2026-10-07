"""
routing/views.py — trip options endpoint.
"""

import logging
from datetime import datetime, timezone

from rest_framework.response import Response
from rest_framework.views import APIView

from safehaul.data_loader import get_routes, get_segments, get_scenarios, get_service_points, get_vehicles
from risk.engine import score_segment
from risk.views import get_server_scenario
from routing.options import build_options

logger = logging.getLogger("routing")


class TripOptionsView(APIView):
    """POST /api/trip/options/"""

    def post(self, request):
        data = request.data

        # Validate required fields
        missing = [f for f in ("origin", "destination", "depart_at", "vehicle_type") if not data.get(f)]
        if missing:
            return Response({"error": f"Missing required fields: {missing}"}, status=400)

        cargo = data.get("cargo", {})
        if not cargo.get("type") or cargo.get("weight_kg") is None:
            return Response({"error": "cargo.type and cargo.weight_kg are required."}, status=400)

        vehicle_type = data.get("vehicle_type", "lcv")
        scenario = data.get("scenario") or get_server_scenario()

        # Load and score all segments for this scenario
        segments = get_segments()
        scenarios_data = get_scenarios()
        routes = get_routes()
        service_points = get_service_points()

        scenario_data = scenarios_data.get(scenario, {})
        dynamic_by_seg = scenario_data.get("segments", {})
        scenario_ts = scenario_data.get("timestamp")
        scenario_source = scenario_data.get("data_source", "simulated")
        now = datetime.now(timezone.utc)

        # Build scored_segments_map {segment_id -> scored dict}
        scored_map = {}
        for seg in segments:
            seg_id = seg["segment_id"]
            raw_dyn = dynamic_by_seg.get(seg_id, {})
            dynamic = {"data_source": scenario_source, "data_timestamp": scenario_ts, **raw_dyn}
            scored = score_segment(seg, dynamic, vehicle_type, now)
            scored_map[seg_id] = scored

        result = build_options(
            trip_request=data,
            scored_segments_map=scored_map,
            routes=routes,
            service_points=service_points,
            vehicle_type=vehicle_type,
            scenario=scenario,
            now=now,
        )
        return Response(result)
