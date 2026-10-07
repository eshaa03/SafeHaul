#!/usr/bin/env python3
"""
truck_sim.py — SafeHaul Kerala simulation: truck-side LoRa device.

Simulates an ESP32+LoRa truck board.  On each "button press" (controlled by
--code and --auto-interval) it:
  1. Builds a 14-byte SOS packet (same format as real firmware).
  2. Encodes it as a serial JSON line and writes it to stdout (to be piped to
     gateway_sim.py or read by a test).
  3. Waits on stdin for an ACK line (written back by gateway_sim.py after the
     bridge posts the ack).
  4. Retries up to RETRY_LIMIT times, then gives up.

All status lines are written to stderr, prefixed with [SIM].

Usage:
    # Single SOS, code 03, then wait for ACK:
    python truck_sim.py --code 03

    # Loop: send one SOS every 15 s indefinitely (for sustained demo):
    python truck_sim.py --code 01 --auto-interval 15

    # Pipe into gateway_sim (requires named pipes; see sim/README.md):
    python truck_sim.py --code 03 --sos-pipe /tmp/sos_pipe --ack-pipe /tmp/ack_pipe
"""

import argparse
import json
import struct
import sys
import time
import datetime

import config  # config.py in the same directory


# ---------------------------------------------------------------------------
# Packet builders
# ---------------------------------------------------------------------------

VALID_CODES = {"01", "02", "03", "04", "05", "06", "07"}


def build_sos_packet(code: str, vehicle_id: int, seq: int,
                     lat_deg: float, lon_deg: float) -> bytes:
    """Return a 14-byte big-endian SOS packet matching the firmware format."""
    if code not in VALID_CODES:
        raise ValueError(f"Invalid code {code!r}; must be one of {sorted(VALID_CODES)}")
    now_utc = datetime.datetime.utcnow()
    minutes_of_day = now_utc.hour * 60 + now_utc.minute
    lat_i32 = int(round(lat_deg * 1e5))
    lon_i32 = int(round(lon_deg * 1e5))
    return struct.pack(">BHBiiH",
                       int(code),       # u8  code
                       vehicle_id,      # u16 vehicle_id
                       seq & 0xFF,      # u8  seq (wraps)
                       lat_i32,         # i32 lat × 1e5
                       lon_i32,         # i32 lon × 1e5
                       minutes_of_day)  # u16 minutes of day


def packet_to_json(code: str, vehicle_id: int, seq: int,
                   lat_deg: float, lon_deg: float) -> str:
    """Produce the serial JSON line that the real gateway board would print."""
    now_utc = datetime.datetime.utcnow()
    device_ts = now_utc.replace(microsecond=0).isoformat() + "Z"
    obj = {
        "code": code,
        "vehicle_id": vehicle_id,
        "seq": seq & 0xFF,
        "lat": round(lat_deg, 5),
        "lng": round(lon_deg, 5),
        "device_ts": device_ts,
        "via": "sim",           # marks this as simulation data
        "station_id": config.STATION_ID,
    }
    return json.dumps(obj)


# ---------------------------------------------------------------------------
# ACK parsing
# ---------------------------------------------------------------------------

def parse_ack_line(line: str, vehicle_id: int, seq: int) -> bool:
    """
    Return True if `line` is an ACK command that matches vehicle_id and seq.
    Expected format (written by bridge.py):  ACK <vehicle_id> <seq>
    """
    line = line.strip()
    if not line.startswith("ACK "):
        return False
    parts = line.split()
    if len(parts) != 3:
        return False
    try:
        ack_vid = int(parts[1])
        ack_seq = int(parts[2])
    except ValueError:
        return False
    return ack_vid == vehicle_id and ack_seq == (seq & 0xFF)


# ---------------------------------------------------------------------------
# Main send-and-wait loop
# ---------------------------------------------------------------------------

def send_and_wait_ack(code: str, seq: int,
                      sos_out, ack_in,
                      vehicle_id: int = config.VEHICLE_ID,
                      lat_deg: float = config.LAT_DEG,
                      lon_deg: float = config.LON_DEG) -> bool:
    """
    Write the SOS JSON line to `sos_out`, then poll `ack_in` for a matching ACK.
    Retries up to RETRY_LIMIT times with RETRY_INTERVAL_S seconds between attempts.
    Returns True if ACKed, False if retry limit reached.
    """
    json_line = packet_to_json(code, vehicle_id, seq, lat_deg, lon_deg)

    for attempt in range(1, config.RETRY_LIMIT + 1):
        print(json_line, file=sos_out, flush=True)
        print(f"[SIM] TX attempt {attempt}/{config.RETRY_LIMIT} "
              f"code={code} vehicle_id={vehicle_id} seq={seq & 0xFF}",
              file=sys.stderr)

        # Wait up to RETRY_INTERVAL_S seconds for an ACK line on ack_in.
        deadline = time.monotonic() + config.RETRY_INTERVAL_S
        while time.monotonic() < deadline:
            # Non-blocking check: ack_in may be a file or sys.stdin.
            # We use a short sleep loop so we don't block the full interval.
            if hasattr(ack_in, 'readline'):
                ack_in_line = _readline_timeout(ack_in,
                                                timeout=config.RETRY_INTERVAL_S)
                if ack_in_line and parse_ack_line(ack_in_line, vehicle_id, seq):
                    print(f"[SIM] RECEIVED ACK from Station {config.STATION_ID} "
                          f"(attempt {attempt})", file=sys.stderr)
                    return True
                break  # readline returned; move to next retry
            time.sleep(0.1)

    print(f"[SIM] NO ACK after {config.RETRY_LIMIT} attempts — giving up.",
          file=sys.stderr)
    return False


def _readline_timeout(stream, timeout: float) -> str:
    """
    Read one line from `stream` with a wall-clock timeout.
    Returns the line (including \\n) or '' on timeout.
    Uses select on POSIX; falls back to a sleep loop on Windows.
    """
    import select as _select
    try:
        ready, _, _ = _select.select([stream], [], [], timeout)
        if ready:
            return stream.readline()
        return ""
    except (AttributeError, ValueError, OSError):
        # stream is not a real file descriptor (e.g. StringIO in tests)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = stream.readline()
            if line:
                return line
            time.sleep(0.05)
        return ""


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SafeHaul Kerala — truck-side LoRa simulation")
    parser.add_argument("--code", default="01",
                        choices=sorted(VALID_CODES),
                        help="Emergency code to transmit (default: 01 = SOS)")
    parser.add_argument("--vehicle-id", type=int, default=config.VEHICLE_ID,
                        help="Vehicle ID (default: from config.py)")
    parser.add_argument("--lat", type=float, default=config.LAT_DEG,
                        help="Latitude in decimal degrees")
    parser.add_argument("--lon", type=float, default=config.LON_DEG,
                        help="Longitude in decimal degrees")
    parser.add_argument("--auto-interval", type=float, default=0,
                        metavar="SECONDS",
                        help="If > 0, send a new SOS every N seconds indefinitely")
    parser.add_argument("--sos-pipe", default=None,
                        help="Path to a named pipe for SOS JSON output "
                             "(default: stdout)")
    parser.add_argument("--ack-pipe", default=None,
                        help="Path to a named pipe for ACK input "
                             "(default: stdin)")
    args = parser.parse_args()

    # Open pipes if specified, otherwise use stdout/stdin.
    if args.sos_pipe:
        sos_out = open(args.sos_pipe, "w")
    else:
        sos_out = sys.stdout

    if args.ack_pipe:
        ack_in = open(args.ack_pipe, "r")
    else:
        ack_in = sys.stdin

    seq = 0
    print(f"[SIM] truck_sim starting: code={args.code} "
          f"vehicle_id={args.vehicle_id}", file=sys.stderr)

    try:
        if args.auto_interval > 0:
            # Continuous mode: send a new SOS every auto_interval seconds.
            while True:
                send_and_wait_ack(args.code, seq, sos_out, ack_in,
                                  vehicle_id=args.vehicle_id,
                                  lat_deg=args.lat, lon_deg=args.lon)
                seq = (seq + 1) & 0xFF
                time.sleep(args.auto_interval)
        else:
            # Single shot.
            acked = send_and_wait_ack(args.code, seq, sos_out, ack_in,
                                      vehicle_id=args.vehicle_id,
                                      lat_deg=args.lat, lon_deg=args.lon)
            sys.exit(0 if acked else 1)
    finally:
        if args.sos_pipe:
            sos_out.close()
        if args.ack_pipe:
            ack_in.close()


if __name__ == "__main__":
    main()
