import json
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import EmergencyEvent, VALID_CODES
from .serializers import EmergencyEventCreateSerializer, EmergencyEventSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_codes() -> dict:
    """
    Load emergency_codes.json from data/ and return a dict keyed by code string.
    Falls back to a minimal hard-coded table if the file is missing (never crash).
    """
    try:
        data_dir = getattr(settings, "DATA_DIR", Path(settings.BASE_DIR).parent / "data")
        codes_path = Path(data_dir) / "emergency_codes.json"
        with open(codes_path, encoding="utf-8") as fh:
            entries = json.load(fh)
        return {entry["code"]: entry for entry in entries}
    except Exception:
        # Fallback so the dashboard still works during development
        return {
            "01": {"code": "01", "en": "SOS — driver needs help", "ml": "", "severity": "critical"},
            "02": {"code": "02", "en": "Landslide ahead",         "ml": "", "severity": "high"},
            "03": {"code": "03", "en": "Flood ahead",             "ml": "", "severity": "high"},
            "04": {"code": "04", "en": "Rescue needed",           "ml": "", "severity": "critical"},
            "05": {"code": "05", "en": "Need load transfer",      "ml": "", "severity": "medium"},
            "06": {"code": "06", "en": "Spare capacity offered",  "ml": "", "severity": "low"},
            "07": {"code": "07", "en": "All clear",               "ml": "", "severity": "low"},
        }


# ---------------------------------------------------------------------------
# REST API endpoints  (consumed by bridge.py, sos-demo, and the station poll)
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
def emergency_endpoint(request):
    """
    POST /api/emergency/ — submit a new emergency packet.
    GET  /api/emergency/?since=<ISO8601> — list events (station dashboard poll).

    Both methods share the same URL as specified in TEAM_BRIEF §1.10.
    """
    if request.method == "POST":
        return _emergency_create(request)
    return _emergency_list(request)


def _emergency_create(request):
    """
    Accept a new emergency packet from a truck device (real or simulated).
    Duplicate packets (same vehicle_id + seq) are silently accepted but not
    stored twice; the existing event is returned with HTTP 200.
    Invalid code → HTTP 400.
    """
    serializer = EmergencyEventCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Duplicate suppression: get_or_create on the unique (vehicle_id, seq) pair.
    event, created = EmergencyEvent.objects.get_or_create(
        vehicle_id=serializer.validated_data["vehicle_id"],
        seq=serializer.validated_data["seq"],
        defaults=serializer.validated_data,
    )
    out = EmergencyEventSerializer(event)
    http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(out.data, status=http_status)


def _emergency_list(request):
    """
    Return all events received after `since` (or all events if omitted).
    Used by the station dashboard poll loop and bridge.py ACK poller.
    """
    qs = EmergencyEvent.objects.all()
    since_str = request.query_params.get("since")
    if since_str:
        since_dt = parse_datetime(since_str)
        if since_dt is None:
            return Response(
                {"error": "Invalid 'since' timestamp; use ISO 8601."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = qs.filter(received_at__gt=since_dt)
    serializer = EmergencyEventSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def emergency_ack(request, event_id):
    """
    POST /api/emergency/<id>/ack/
    Mark an event as acknowledged. Records acked_by from request body
    (optional field; defaults to "station").
    The bridge polls for acked events and forwards the ACK over LoRa.
    """
    try:
        event = EmergencyEvent.objects.get(pk=event_id)
    except EmergencyEvent.DoesNotExist:
        return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

    if event.status == "acked":
        # Already acked — idempotent; return current state.
        return Response(EmergencyEventSerializer(event).data)

    event.status = "acked"
    event.acked_by = request.data.get("acked_by", "station")
    event.acked_at = timezone.now()
    event.save(update_fields=["status", "acked_by", "acked_at"])
    return Response(EmergencyEventSerializer(event).data)


# ---------------------------------------------------------------------------
# Dashboard views (HTML pages)
# ---------------------------------------------------------------------------

def station_dashboard(request):
    """
    GET /station/
    The station operator dashboard. Renders a template with the code table
    embedded as a JSON object; the JS poll loop uses it to decode code meanings.
    No internet required — all assets are served by Django static files.
    """
    codes = _load_codes()
    return render(request, "emergency/station.html", {
        "codes_json": json.dumps(codes),
        "valid_codes": VALID_CODES,
    })


def sos_demo(request):
    """
    GET /sos-demo/
    Truck-side simulation page. Buttons for codes 01-07 POST to /api/emergency/
    and wait for an ACK. Shows "RECEIVED by Station 1 [SIMULATED RADIO LINK]"
    when the event is acknowledged. No real hardware required.
    """
    codes = _load_codes()
    return render(request, "emergency/sos_demo.html", {
        "codes_json": json.dumps(codes),
        "codes_list": list(codes.values()),
        "valid_codes": VALID_CODES,
    })
