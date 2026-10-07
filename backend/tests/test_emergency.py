"""
Tests for backend/emergency/ — covers the four cases from TEAM_BRIEF §2 Member D:
  1. Create a valid event → HTTP 201, object stored.
  2. Duplicate packet (same vehicle_id + seq) → HTTP 200, one DB row.
  3. Acknowledge → status flips to "acked", acked_at set.
  4. List ?since= filter returns only events after the given timestamp.

Bonus (also required by AGENTS.md quality rule):
  5. Invalid code rejected → HTTP 400.

Run with:  cd backend && python manage.py test tests   (or pytest with pytest-django)
"""

import json
from datetime import datetime, timezone
from urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse

from emergency.models import EmergencyEvent


VALID_PAYLOAD = {
    "code": "03",
    "vehicle_id": 17,
    "seq": 4,
    "lat": 10.3066,
    "lng": 76.3318,
    "device_ts": "2026-10-07T14:30:00+05:30",
    "via": "sim",
    "station_id": 1,
}


class EmergencyAPITest(TestCase):

    # ------------------------------------------------------------------
    # Test 1: valid POST creates event
    # ------------------------------------------------------------------
    def test_create_valid_event_returns_201(self):
        resp = self.client.post(
            "/api/emergency/",
            data=json.dumps(VALID_PAYLOAD),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["code"], "03")
        self.assertEqual(data["vehicle_id"], 17)
        self.assertEqual(data["seq"], 4)
        self.assertEqual(data["status"], "new")
        self.assertIsNone(data["acked_at"])
        # Row in DB
        self.assertEqual(EmergencyEvent.objects.count(), 1)

    # ------------------------------------------------------------------
    # Test 2: duplicate packet → same row, HTTP 200, not stored twice
    # ------------------------------------------------------------------
    def test_duplicate_packet_suppressed(self):
        # First POST
        self.client.post(
            "/api/emergency/",
            data=json.dumps(VALID_PAYLOAD),
            content_type="application/json",
        )
        # Second POST — identical vehicle_id + seq
        resp = self.client.post(
            "/api/emergency/",
            data=json.dumps(VALID_PAYLOAD),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)          # existing event returned
        self.assertEqual(EmergencyEvent.objects.count(), 1)  # still only one row

    # ------------------------------------------------------------------
    # Test 3: acknowledge sets status and acked_at
    # ------------------------------------------------------------------
    def test_ack_sets_status(self):
        create_resp = self.client.post(
            "/api/emergency/",
            data=json.dumps(VALID_PAYLOAD),
            content_type="application/json",
        )
        event_id = create_resp.json()["id"]

        ack_resp = self.client.post(
            f"/api/emergency/{event_id}/ack/",
            data=json.dumps({"acked_by": "test-station"}),
            content_type="application/json",
        )
        self.assertEqual(ack_resp.status_code, 200)
        data = ack_resp.json()
        self.assertEqual(data["status"], "acked")
        self.assertEqual(data["acked_by"], "test-station")
        self.assertIsNotNone(data["acked_at"])

        # Re-ACKing is idempotent
        ack_resp2 = self.client.post(
            f"/api/emergency/{event_id}/ack/",
            data=json.dumps({"acked_by": "other"}),
            content_type="application/json",
        )
        self.assertEqual(ack_resp2.status_code, 200)
        # acked_by should not change on a re-ack
        self.assertEqual(ack_resp2.json()["acked_by"], "test-station")

    # ------------------------------------------------------------------
    # Test 4: ?since= filter returns only events after the timestamp
    # ------------------------------------------------------------------
    def test_since_filter(self):
        old_ts = datetime(2026, 10, 7, 6, 0, tzinfo=timezone.utc)
        new_ts = datetime(2026, 10, 7, 9, 0, tzinfo=timezone.utc)

        # Create both events via the API (so auto_now_add fires), then
        # backdate received_at using update() which bypasses auto_now_add.
        r1 = self.client.post(
            "/api/emergency/",
            data=json.dumps(dict(VALID_PAYLOAD, vehicle_id=1, seq=1)),
            content_type="application/json",
        )
        ev1_id = r1.json()["id"]
        EmergencyEvent.objects.filter(pk=ev1_id).update(received_at=old_ts)

        r2 = self.client.post(
            "/api/emergency/",
            data=json.dumps(dict(VALID_PAYLOAD, vehicle_id=2, seq=2)),
            content_type="application/json",
        )
        ev2_id = r2.json()["id"]
        EmergencyEvent.objects.filter(pk=ev2_id).update(received_at=new_ts)

        # since= between the two events — should return only ev2.
        # Use urlencode so the '+' in the timezone offset is percent-encoded;
        # a bare '+' in a URL query string is decoded as a space by Django.
        cutoff = "2026-10-07T07:00:00+00:00"
        resp = self.client.get("/api/emergency/?" + urlencode({"since": cutoff}))
        self.assertEqual(resp.status_code, 200)
        ids = [e["id"] for e in resp.json()]
        self.assertIn(ev2_id, ids)
        self.assertNotIn(ev1_id, ids)

    # ------------------------------------------------------------------
    # Test 5 (bonus): invalid code rejected with HTTP 400
    # ------------------------------------------------------------------
    def test_invalid_code_rejected(self):
        bad = dict(VALID_PAYLOAD, code="99")
        resp = self.client.post(
            "/api/emergency/",
            data=json.dumps(bad),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("code", resp.json())
        self.assertEqual(EmergencyEvent.objects.count(), 0)
