#!/usr/bin/env python3
"""
gateway_sim.py — SafeHaul Kerala simulation: gateway-side LoRa station.

Simulates the gateway ESP32+LoRa board that sits at the police/rescue station.
It:
  1. Reads SOS JSON lines from stdin (piped from truck_sim.py).
  2. Writes them to stdout unchanged (to be piped into bridge.py).
  3. Reads ACK commands from a second stream (written by bridge.py back to the
     gateway) and prints a matching "[SIM] SENT ACK" status line to stderr, and
     writes an "ACK <vehicle_id> <seq>" line back toward truck_sim via its ack pipe.

All status lines are written to stderr, prefixed with [SIM].

Usage (named-pipe mode — see sim/README.md for the full demo setup):
    mkfifo /tmp/sos_pipe /tmp/ack_pipe /tmp/bridge_ack_pipe

    # Terminal 1 — truck side:
    python truck_sim.py --code 03 --sos-pipe /tmp/sos_pipe --ack-pipe /tmp/ack_pipe

    # Terminal 2 — gateway side:
    python gateway_sim.py --sos-pipe /tmp/sos_pipe --bridge-ack-pipe /tmp/bridge_ack_pipe --truck-ack-pipe /tmp/ack_pipe

    # Terminal 3 — bridge:
    python ../../gateway/bridge.py --sim --ack-out /tmp/bridge_ack_pipe

Simple stdin/stdout pipe (no ACK back to truck — useful for testing bridge alone):
    python truck_sim.py --code 03 | python gateway_sim.py | python ../../gateway/bridge.py --sim
"""

import argparse
import json
import sys
import threading

import config  # config.py in the same directory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    """Write a [SIM]-prefixed status line to stderr."""
    print(f"[SIM] gateway: {msg}", file=sys.stderr, flush=True)


def relay_sos(sos_in, bridge_out) -> None:
    """
    Read SOS JSON lines from `sos_in` and write them verbatim to `bridge_out`.
    Each line is validated as JSON before forwarding; malformed lines are
    logged and discarded.
    """
    for raw_line in sos_in:
        raw_line = raw_line.rstrip("\n")
        if not raw_line:
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            log(f"Malformed SOS line discarded: {exc} | raw={raw_line!r}")
            continue

        # Enforce via="sim" so the bridge always knows this is simulated.
        obj["via"] = "sim"
        forwarded = json.dumps(obj)
        print(forwarded, file=bridge_out, flush=True)
        log(f"Relayed SOS code={obj.get('code')} vehicle_id={obj.get('vehicle_id')} "
            f"seq={obj.get('seq')}")


def relay_ack(bridge_ack_in, truck_ack_out) -> None:
    """
    Read ACK commands from the bridge (format: "ACK <vehicle_id> <seq>\\n")
    and forward them to truck_ack_out so truck_sim can detect the ACK.
    Also logs a status line to stderr.
    """
    for raw_line in bridge_ack_in:
        raw_line = raw_line.rstrip("\n")
        if not raw_line:
            continue
        if not raw_line.startswith("ACK "):
            log(f"Unexpected line from bridge (ignored): {raw_line!r}")
            continue
        parts = raw_line.split()
        if len(parts) == 3:
            log(f"ACK forwarded to truck: vehicle_id={parts[1]} seq={parts[2]}")
        print(raw_line, file=truck_ack_out, flush=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SafeHaul Kerala — gateway-side LoRa simulation")
    parser.add_argument("--sos-pipe", default=None,
                        help="Named pipe to read SOS JSON from truck_sim "
                             "(default: stdin)")
    parser.add_argument("--bridge-ack-pipe", default=None,
                        help="Named pipe to read ACK commands from bridge.py "
                             "(default: none — ACK relay disabled)")
    parser.add_argument("--truck-ack-pipe", default=None,
                        help="Named pipe to write ACK lines back to truck_sim "
                             "(default: none — ACK relay disabled)")
    args = parser.parse_args()

    # --- Open streams ---
    sos_in = open(args.sos_pipe, "r") if args.sos_pipe else sys.stdin
    bridge_out = sys.stdout  # always stdout → piped to bridge.py

    ack_relay_enabled = (args.bridge_ack_pipe is not None
                         and args.truck_ack_pipe is not None)

    if ack_relay_enabled:
        bridge_ack_in = open(args.bridge_ack_pipe, "r")
        truck_ack_out = open(args.truck_ack_pipe, "w")

    log("gateway_sim starting"
        + (" (ACK relay enabled)" if ack_relay_enabled else
           " (ACK relay disabled — bridge stdin/stdout mode)"))

    try:
        if ack_relay_enabled:
            # Run ACK relay in a background thread so SOS relay can block on
            # reading lines without stalling ACK delivery.
            ack_thread = threading.Thread(
                target=relay_ack,
                args=(bridge_ack_in, truck_ack_out),
                daemon=True,
            )
            ack_thread.start()

        relay_sos(sos_in, bridge_out)

    finally:
        if args.sos_pipe:
            sos_in.close()
        if ack_relay_enabled:
            bridge_ack_in.close()
            truck_ack_out.close()


if __name__ == "__main__":
    main()
