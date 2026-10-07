"""
servicepoints/views.py — service-points endpoint.
"""

import logging
from datetime import datetime, timezone

from rest_framework.response import Response
from rest_framework.views import APIView

from safehaul.data_loader import get_routes, get_segments, get_scenarios, get_service_points
from risk.engine import score_segment
from risk.views import get_server_scenario
from servicepoints.ranking import rank_service_points

logger = logging.getLogger("servicepoints")


class ServicePointsView(APIView):
    """GET /api/service-points/"""

    def get(self, request):
        scenario = request.query_params.get("scenario") or get_server_scenario()
        vehicle_type = request.query_params.get("vehicle_type", "lcv")
        mode = request.query_params.get("mode", "normal")
        position_seg = request.query_params.get("position_segment_id")

        segments = get_segments()
        scenarios_data = get_scenarios()
        routes = get_routes()
        service_points = get_service_points()

        if not service_points:
            return Response({"error": "No service-point data available."}, status=503)

        scenario_data = scenarios_data.get(scenario, {})
        dynamic_by_seg = scenario_data.get("segments", {})
        scenario_ts = scenario_data.get("timestamp")
        scenario_source = scenario_data.get("data_source", "simulated")
        now = datetime.now(timezone.utc)

        # Score all segments
        scored_map = {}
        for seg in segments:
            seg_id = seg["segment_id"]
            raw_dyn = dynamic_by_seg.get(seg_id, {})
            dynamic = {"data_source": scenario_source, "data_timestamp": scenario_ts, **raw_dyn}
            scored_map[seg_id] = score_segment(seg, dynamic, vehicle_type, now)

        # Build a combined route covering all segment IDs across all routes,
        # so service points on any route are reachable-checked correctly.
        all_seg_ids: list[str] = []
        seen: set[str] = set()
        for r in routes:
            for sid in r.get("segment_ids", []):
                if sid not in seen:
                    all_seg_ids.append(sid)
                    seen.add(sid)
        combined_route = {"route_id": "combined", "segment_ids": all_seg_ids}

        if not combined_route["segment_ids"]:
            return Response({"error": "No route data available."}, status=503)

        ranked = rank_service_points(
            service_points,
            combined_route,
            scored_map,
            vehicle_type=vehicle_type,
            position_segment_id=position_seg,
            mode=mode,
        )
        return Response(ranked)
