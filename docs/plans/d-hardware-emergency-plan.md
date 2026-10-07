# Plan: Member D — Hardware & Emergency Communication

**Branch:** `d/hardware`  
**Owner:** Member D  
**Scope:** ESP32 + LoRa truck-device firmware, gateway bridge, Django emergency API, station dashboard, simulation fallback, tests.

---

## Top-Level Overview

The goal is a live, demostrable SOS loop — no internet required:

1. A "truck" board (or simulated process) broadcasts a compact 14-byte LoRa packet when a driver presses a button.
2. A "gateway" board (or simulated process) receives it, streams one JSON line over USB serial to a laptop.
3. A Python bridge (`hardware/gateway/bridge.py`) reads that line and POSTs to the local Django server.
4. The Django `emergency` app stores the event and serves it via REST.
5. A station dashboard at `/station/` polls every 2 seconds, shows the event with its human-readable meaning, and lets the operator click **Acknowledge** — which pushes an ACK back to the gateway, which relays a 5-byte ACK packet over LoRa to the truck board.
6. The truck board lights up "RECEIVED by Station N".

Because hardware may not be available before the demo, **every layer has a software-simulation path** that behaves identically from the bridge inward. The simulation is clearly labelled.

**Target board (hardware path):** Heltec WiFi LoRa 32 V2 (ESP32 + SX1276, 128×64 OLED, India band 865–867 MHz).  
**Fallback (simulation path):** two Python processes on one laptop replace the two boards.

---

## Sub-Tasks

---

### D1 — Hardware Inventory & Legal Band Check
**Status:** [x] done

**Intent**  
Confirm exactly what physical hardware exists, set the correct LoRa frequency for India, and document the fallback plan so nothing blocks the rest of the work.

**Expected Outcomes**  
- `hardware/README.md` exists with: board model(s) on hand (or "none yet"), chosen LoRa frequency (865.2 MHz, 125 kHz BW, SF7, 14 dBm or lower), and the simulation fallback statement.
- `docs/QUESTIONS.md` has a line to E if boards are missing so they can be sourced.
- The simulation path is declared the safe default until real boards arrive.

**Todo List**  
1. Create `hardware/README.md` with sections: *Hardware on hand*, *LoRa settings for India*, *Wiring diagram reference*, *Fallback simulation plan*, *Flash & run instructions* (to be filled in D2/D3).
2. Confirm legal India ISM band (865–867 MHz) and note frequency, bandwidth, spreading factor, TX power.
3. If no boards are confirmed, add a line to `docs/QUESTIONS.md`: `[D to E] Need 2x Heltec LoRa32 V2 boards + antennas for the SOS demo — can these be sourced?`
4. Update D's section in `docs/STATUS.md`: hardware status, fallback declared.

**Relevant Context**  
- TEAM_BRIEF §2 Member D, task D1  
- India license-exempt LoRa band: 865–867 MHz (WPC rules); keep EIRP ≤ 1 W (30 dBm); demo uses 14 dBm  
- Heltec V2 pinout: SCK 5, MISO 19, MOSI 27, SS 18, RST 14, DIO0 26, OLED SDA 4, SCL 15, RST_OLED 16

---

### D2 — Packet Format Specification
**Status:** [ ] pending

**Intent**  
Lock down the two packet formats (14-byte SOS / 7-byte ACK) and the serial JSON envelope before writing a single line of firmware or bridge code, so all three layers (firmware, bridge, Django) agree without re-work.

**Expected Outcomes**  
- `hardware/README.md` extended with a *Packet format* section containing byte-by-byte layout for both packets and the serial JSON schema.
- The specification is consistent with TEAM_BRIEF §1.10 emergency packet fields.

**Todo List**  
1. Document the **14-byte SOS packet** (big-endian):

   | Byte(s) | Field | Type | Notes |
   |---|---|---|---|
   | 0 | code | u8 | 01–07 |
   | 1–2 | vehicle_id | u16 | |
   | 3 | seq | u8 | wraps at 255 |
   | 4–7 | lat | i32 | degrees × 1e5 |
   | 8–11 | lon | i32 | degrees × 1e5 |
   | 12–13 | minutes_of_day | u16 | UTC minutes 0–1439 |

2. Document the **5-byte ACK packet**:

   | Byte(s) | Field | Type |
   |---|---|---|
   | 0 | 'A' (0x41) | u8 |
   | 1 | station_id | u8 |
   | 2–3 | vehicle_id | u16 |
   | 4 | seq | u8 |

3. Document the **serial JSON line** the gateway board prints per received SOS:
   ```
   {"code":"03","vehicle_id":17,"seq":4,"lat":10.30660,"lng":76.33180,"device_ts":"...","via":"lora","station_id":1}
   ```
4. Confirm all field names match CONTRACT.md (§1.10 emergency packet).

**Relevant Context**  
- TEAM_BRIEF §1.10, emergency packet definition  
- `data/emergency_codes.json` (to be created in D6 / by C)

---

### D3 — Firmware: Truck Device (hardware path)
**Status:** [ ] pending

**Intent**  
Write MicroPython or Arduino (C++) firmware for the Heltec V2 "truck" board that sends a signed 14-byte LoRa packet on button press, retries until ACK, and displays result on the OLED.

**Expected Outcomes**  
- `hardware/firmware/truck/main.ino` (or `main.py` for MicroPython) compiles/runs on a Heltec V2.
- Pressing button 1 sends the current code; button 2 cycles through codes 01–07.
- Board retries the packet every 3 seconds (configurable) up to 10 times (configurable).
- On receiving a matching ACK it shows "RECEIVED by Station N" on the OLED and stops retrying.
- On retry exhaustion it shows "NO ACK — retry?" and blinks an LED.

**Todo List**  
1. Choose library: **Arduino IDE** with `LoRa` by Sandeep Mistry (well-tested on SX127x, Heltec-compatible) and `U8g2` for OLED. Note these in `hardware/README.md`.
2. Implement `buildPacket(code, vehicle_id, seq, lat_deg, lon_deg)` → 14-byte array.
3. Implement `sendAndWaitAck()` loop with retry limit and timeout, calling `buildPacket`.
4. Implement `parseAck(buf, len)` → match by vehicle_id + seq.
5. Wire button debounce (25 ms).
6. OLED: show code name, seq number, retry count, and ACK status.
7. Keep LoRa settings (frequency, BW, SF, power) in a `#define` block at the top; they must match the spec in D1.
8. Do **not** hard-code vehicle_id or coordinates; read from a `config.h` (or a `config.py` for MicroPython) so values can be swapped for each device.

**Relevant Context**  
- `hardware/firmware/` (currently empty)  
- Heltec V2 LoRa pin mapping from D1  
- Packet format from D2  
- All tunable constants (retry count, interval, LoRa settings) must be in a config header, not scattered

---

### D4 — Firmware: Simulation Fallback (two Python processes)
**Status:** [x] done

**Intent**  
Provide a laptop-only demo path that is behaviourally identical to the real hardware from the bridge layer inward, clearly labelled as simulation. This is the **primary demo path** until boards arrive.

**Expected Outcomes**  
- `hardware/firmware/sim/truck_sim.py`: a Python script that sends the same 14-byte packet (encoded in the serial JSON format) to stdout or a named pipe, loops with retries, waits for an ACK line, and prints status.
- `hardware/firmware/sim/gateway_sim.py`: reads from stdin (or a named pipe), relays JSON to the bridge, receives ACK commands and prints matching ACK lines.
- Running `truck_sim.py | gateway_sim.py | bridge.py` demonstrates the full loop on one laptop.
- Output is prefixed with `[SIM]` in every log line.

**Todo List**  
1. Implement `truck_sim.py` with configurable code, vehicle_id, lat/lon, retry interval, retry limit. Accepts a `--code` CLI argument.
2. Implement `gateway_sim.py` that wraps each simulated SOS in the serial JSON envelope and forwards to stdout.
3. Write a `hardware/firmware/sim/README.md` explaining the pipe command and how to trigger different codes.
4. Ensure the JSON output is bit-for-bit identical to what the real gateway board would produce, so the bridge cannot tell the difference.

**Relevant Context**  
- `hardware/firmware/` (empty)  
- Serial JSON schema from D2  
- Bridge in D5 must need zero changes to switch between real serial port and the simulation pipe

---

### D5 — Gateway Bridge (`hardware/gateway/bridge.py`)
**Status:** [ ] pending

**Intent**  
A small, robust Python script that sits between the hardware (or simulation) and the Django API. It reads serial JSON lines, POSTs to the local server, polls for ACK events, and sends ACK commands back to the board.

**Expected Outcomes**  
- `hardware/gateway/bridge.py` runs with `python bridge.py [--port /dev/ttyUSB0 | --sim]`.
- In `--sim` mode it reads from stdin instead of a serial port.
- It POSTs each new event to `http://localhost:8000/api/emergency/` and logs the response.
- It polls `GET /api/emergency/?since=<ts>` every 2 seconds; for any event with `status=acked` it sends `ACK <vehicle_id> <seq>\n` to the serial port (or stdout in sim mode).
- Handles connection refused gracefully (server not yet running): queues up to 50 events in memory and retries.
- No secrets, no external dependencies beyond `pyserial` and `requests` (both pip-installable offline).

**Todo List**  
1. Implement `read_serial_line(port_or_stdin)` → dict.
2. Implement `post_event(event_dict)` with a 3-second timeout; log success/failure.
3. Implement `poll_acks(since_ts)` → list of acked event dicts.
4. Implement `send_ack_to_board(vehicle_id, seq)` → writes ACK command to port/stdout.
5. Main loop: read → post → poll → ack cycle.
6. Document required pip packages in `hardware/gateway/requirements.txt`.
7. Add a `--dry-run` flag that logs without actually POSTing (useful for testing packet parsing).

**Relevant Context**  
- `hardware/gateway/` (currently empty)  
- Serial JSON schema from D2  
- Emergency API endpoints from TEAM_BRIEF §1.10  
- `pyserial`, `requests` are the only external dependencies

---

### D6 — Django Emergency App (`backend/emergency/`)
**Status:** [ ] pending

**Intent**  
Create the `emergency` Django app with the three API endpoints defined in CONTRACT.md, de-duplication logic, and the data model. This is a pure Django/DRF task with no hardware dependency; it can be built immediately in parallel with D2–D5.

**Expected Outcomes**  
- `backend/emergency/` is a proper Django app: `models.py`, `serializers.py`, `views.py`, `urls.py`, `apps.py`.
- `EmergencyEvent` model has all fields from TEAM_BRIEF §1.10 plus `status` (new/acked).
- `POST /api/emergency/` stores events; duplicate (same vehicle_id + seq) is silently accepted but not stored twice.
- `GET /api/emergency/?since=<ISO8601>` returns all events received after that timestamp.
- `POST /api/emergency/<id>/ack/` sets status to `acked`, records `acked_by` and `acked_at`.
- Invalid code (not 01–07) returns HTTP 400.
- All responses include `data_source: "live"` for real events.

**Todo List**  
1. Create `backend/emergency/models.py`: `EmergencyEvent` with fields: `code`, `vehicle_id`, `seq`, `lat`, `lng`, `device_ts`, `received_at` (auto), `via` (choices: lora/app/sms/sim), `station_id`, `status` (new/acked), `acked_by`, `acked_at`.
2. Add a unique-together constraint on `(vehicle_id, seq)` for de-duplication.
3. Create `backend/emergency/serializers.py` with `EmergencyEventSerializer` (read) and `EmergencyEventCreateSerializer` (write, validates code is 01–07).
4. Create `backend/emergency/views.py`: `EmergencyEventListCreateView`, `EmergencyEventAckView`.
5. Create `backend/emergency/urls.py` and wire into the main URL conf (coordinate with A).
6. Create `data/emergency_codes.json` with codes 01–07, English text, empty `ml` fields (leave for E/native speaker).
7. Register the app in Django settings (coordinate with A).

**Relevant Context**  
- TEAM_BRIEF §1.10 emergency packet + event object  
- `data/emergency_codes.json` (D owns this file per the repo layout)  
- A creates the Django skeleton and stub app first; D fills the stub

---

### D7 — Emergency Tests (`backend/tests/test_emergency.py`)
**Status:** [ ] pending

**Intent**  
Automated tests for the emergency API covering every case judges are likely to probe.

**Expected Outcomes**  
- All tests pass with `pytest` (or `python manage.py test`).
- Coverage: create event, duplicate suppression, ack flow, `?since=` filter, invalid code rejected.

**Todo List**  
1. Test `POST /api/emergency/` with a valid packet → HTTP 201, event in DB.
2. Test duplicate: same vehicle_id + seq → HTTP 200 (or 201) but only one DB row.
3. Test invalid code (e.g. `"00"`, `"08"`) → HTTP 400.
4. Test `GET /api/emergency/?since=<ts>` returns only events after that timestamp.
5. Test `POST /api/emergency/<id>/ack/` sets status, acked_at, acked_by.
6. Test `GET /api/emergency/` with no `since` parameter returns all events.
7. Use Django `TestCase` with in-memory SQLite; no external dependencies.

**Relevant Context**  
- `backend/tests/` (empty; D creates `test_emergency.py`)  
- TEAM_BRIEF §1.13 quality rules  
- AGENTS.md: tests required for the emergency API

---

### D8 — Station Dashboard (`/station/`)
**Status:** [ ] pending

**Intent**  
A standalone Django-served page (no Node, no CDN) that shows incoming emergency events in near-real-time, allows the operator to acknowledge them, and is fully usable with no internet.

**Expected Outcomes**  
- `/station/` renders a high-contrast, mobile-usable dashboard.
- A JavaScript `setInterval` polls `GET /api/emergency/?since=<last_ts>` every 2 seconds.
- Each event card shows: code meaning (from the bundled `emergency_codes.json`), vehicle ID, time, lat/lng, via (lora/app/sms/sim), status.
- New/unacked events are visually prominent (e.g. red border, bold text) and trigger a browser `Audio` beep (a short tone generated with the Web Audio API — no audio file needed, no CDN).
- The **Acknowledge** button sends `POST /api/emergency/<id>/ack/` and immediately updates the card status without a full page reload.
- A small embedded Leaflet map (bundled locally, same vendor copy as the main app) shows the event location as a marker.
- All assets are served by Django's static files; page works with the laptop in flight-mode.

**Todo List**  
1. Create `backend/emergency/templates/emergency/station.html`: base layout, event list container, map container.
2. Create `backend/emergency/static/emergency/station.js`: poll loop, render event cards, ack button handler, map marker update, Web Audio beep on new event.
3. Create `backend/emergency/static/emergency/station.css`: high-contrast theme (dark background, bright status colours).
4. Load emergency code meanings from a small embedded JSON object in the template (generated from `data/emergency_codes.json` at template render time via a Django view context variable) — avoids a second fetch.
5. Reuse or symlink the vendored Leaflet from `frontend/static/vendor/leaflet/` (coordinate with B on the path).
6. Add a `GET /station/` view in `backend/emergency/views.py` that passes the code table to the template.
7. Add a visible `[SIMULATED DATA]` banner when any displayed event has `via=sim`.

**Relevant Context**  
- `frontend/static/vendor/` (B owns; coordinate for Leaflet reuse)  
- `data/emergency_codes.json` (D creates in D6)  
- TEAM_BRIEF §1.7 principle 5 (honesty about data source)  
- No CDN dependencies (AGENTS.md hard rule)

---

### D9 — Demo Hardening & Runbook
**Status:** [ ] pending

**Intent**  
Make the demo repeatable and failure-safe. A runbook means anyone on the team can run the SOS demo without D present.

**Expected Outcomes**  
- `hardware/README.md` extended with a *Demo Runbook* section.
- The runbook covers both the hardware path and the simulation fallback path.
- Backup plan (pre-recorded video + sim script) is documented.

**Todo List**  
1. Write step-by-step power-on order (server first, then gateway/sim, then truck device).
2. Document how to turn the internet off on the demo laptop (disable Wi-Fi; confirm `localhost:8000` still works).
3. List what the audience should see at each step of TEAM_BRIEF §1.6 steps 5–6.
4. Document failure modes and recovery: radio link fails → switch to `--sim`; server not running → restart command.
5. Add a `hardware/firmware/sim/run_demo.sh` convenience script that starts the server, simulation, and bridge in three terminal panes (using `tmux` if available, otherwise plain background processes).
6. Note the 5-rehearsal minimum (TEAM_BRIEF §2 D8).

**Relevant Context**  
- TEAM_BRIEF §1.6 demo scenario steps 5–6  
- TEAM_BRIEF §2 Member D, task D8  
- `hardware/README.md` (started in D1)

---

## Dependency & Sequencing Notes

- **D6 (Django app) has no hardware dependency** and can start as soon as A merges the project skeleton to `main`. Start here in parallel with D1/D2.
- **D1 and D2** (inventory + packet spec) must complete before D3/D4 (firmware).
- **D5 (bridge)** depends on D2 (packet spec) and D6 (API running).
- **D7 (tests)** depends on D6.
- **D8 (dashboard)** depends on D6 (API) and a Leaflet vendor copy from B.
- **D3 (real firmware)** is the only task that requires physical boards; everything else can proceed without them.
- **D4 (simulation)** is the unblocked fallback for D3 and should be built first.

## Files D Will Create or Fill

| File | Task |
|---|---|
| `hardware/README.md` | D1, D9 |
| `hardware/firmware/truck/main.ino` (or `.py`) | D3 |
| `hardware/firmware/sim/truck_sim.py` | D4 |
| `hardware/firmware/sim/gateway_sim.py` | D4 |
| `hardware/firmware/sim/README.md` | D4 |
| `hardware/firmware/sim/run_demo.sh` | D9 |
| `hardware/gateway/bridge.py` | D5 |
| `hardware/gateway/requirements.txt` | D5 |
| `backend/emergency/__init__.py` | D6 |
| `backend/emergency/apps.py` | D6 |
| `backend/emergency/models.py` | D6 |
| `backend/emergency/serializers.py` | D6 |
| `backend/emergency/views.py` | D6, D8 |
| `backend/emergency/urls.py` | D6 |
| `backend/emergency/templates/emergency/station.html` | D8 |
| `backend/emergency/static/emergency/station.js` | D8 |
| `backend/emergency/static/emergency/station.css` | D8 |
| `backend/tests/test_emergency.py` | D7 |
| `data/emergency_codes.json` | D6 |
| `docs/STATUS.md` (D section only) | D1 |
| `docs/QUESTIONS.md` (append only if hardware missing) | D1 |
