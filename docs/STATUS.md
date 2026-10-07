# Project Status

**How to use:** each member updates **only their own section**, at the end of every work session. Keep entries short and factual. Commit the file with your branch. Other agents read this at the start of each session to see what is available and what is blocked.

Format for each entry: `YYYY-MM-DD HH:MM: what changed`.
Legend: Done / In progress / Blocked / Next.

---

## Member A: Backend and Risk Engine
- **Done:** A1–A5 complete — full backend live. Risk engine (`score_segment` with §1.11 formula, flood memory, overrides, confidence, reasons); ETA range with reason string, peak-hour + rest-break rules; route options hard filters (safety → shelf life → clearance P1 stub), `proceed/reroute/wait/divert_store` options, exactly-one `recommended`; service-point reachability ranking (`reachable=false` with reason for blocked hospitals); 48/48 tests passing.
- **In progress:** —
- **Blocked (waiting on whom/what):** `data/` files from C (stand-in fixture is live; loader auto-switches when C delivers)
- **Next:** A6 stretch (fleet endpoint) after demo stabilisation; wire weather client when C delivers
- **Endpoints available on `main`:** `GET /api/scenario/`, `POST /api/scenario/`, `GET /api/routes/`, `GET /api/segments/`, `POST /api/trip/options/`, `GET /api/service-points/`

## Member B: Frontend and Map
- **Done:** B0 (sample JSON), B1 (base template, Leaflet map, scaffold), B2 (risk overlay with colour+pattern+icon, segment detail popup), B3 (flood toggle → POST /api/scenario/ + map reload), B4 (option cards, ETA range, cargo window, excluded routes, receiver toast), B5 (hospital list from /api/service-points/)
- **In progress:** —
- **Blocked (waiting on whom/what):** A's Django skeleton for full integration (workaround: `python -m django runserver --settings=frontend_project.settings`)
- **Next:** B6 (Malayalam toggle polish, PWA/service worker, offline sliding window)
- **Using:** sample JSON

## Member C: Data and Integrations
- **Done:**
  - C1: `data/segments.json` (20 segs), `data/routes.json` (main 130.5 km, alt1 129.1 km); OSM geometry; validate_segments.py passes 0 errors
  - C2: `data/scenarios.json` (normal + flood); validate_risk.py passes all assertions — 4 high segs on main in flood, alt1 clean, wait excluded by shelf-life (8.47 h > 8 h)
  - C3: `data/service_points.json` (30 points: 4 hospitals, 7 fuel, 4 repair, 1 towing, 5 police, 2 fire, 4 safe_halt, 3 cold_store, 3 food); H-01/H-02 nearest-reachable flip wired in
  - C6 (partial): `data/vehicles.json` (4 types), `data/emergency_codes.json` (codes 01–07, ml empty pending native review)
  - `data/SOURCES.md` — full provenance for all files
  - `data/scripts/validate_risk.py`, `data/scripts/validate_segments.py` — both pass 0 errors
- **In progress:** (nothing — C1/C2/C3/C6-partial complete)
- **Blocked (waiting on whom/what):** `emergency_codes.json` `ml` field needs native Malayalam review — question logged for E
- **Next:** C4 (weather client + Open-Meteo), C5 (flood_history.json + flood_memory.py), fleet.json
- **Data files on `main`:** `data/segments.json`, `data/routes.json`, `data/scenarios.json`, `data/service_points.json`, `data/vehicles.json`, `data/emergency_codes.json`, `data/SOURCES.md`

## Member D: Hardware and Emergency Communication
- **Done:** 2026-10-08: D1 complete — hardware/README.md written, LoRa India band settings documented (865.2 MHz SF7 14 dBm), packet formats specified, simulation fallback declared, QUESTIONS.md updated for hardware sourcing.
- **In progress:** D2 firmware (blocked on board model confirmation from E).
- **Blocked (waiting on whom/what):** Physical boards not yet confirmed. Waiting for E to respond to QUESTIONS.md re sourcing. Also waiting for A to merge Django skeleton before D6 (emergency app) can be wired.
- **Next:** D4 simulation path (truck_sim.py + gateway_sim.py) — unblocked; D6 Django emergency app — unblocked once A merges skeleton.
- **Hardware on hand:** None confirmed yet. Target: 2× Heltec WiFi LoRa 32 V2 + antennas + 1× GPS module. Fallback: software simulation (full loop on one laptop).

## Member E: Product, Pitch and QA
- **Done:**
- **In progress:**
- **Next:**

---

## Integration checkpoints (E ticks these off)

### P0: must work flawlessly
- [ ] Map shows the Palakkad to Kochi route and segments
- [ ] Segment risk with reasons, confidence, data age and data source
- [ ] "Simulate flood" toggle changes risk, options and ETA
- [ ] Hard filters: unsafe route excluded; shelf-life check works
- [ ] 2-3 labelled options with trade-offs (reroute / wait / divert-and-store)
- [ ] ETA range with a reason, updated on reroute
- [ ] Service points ranked by safe reachable time ("nearest reachable hospital" flips in flood)

### P1: demo highlights
- [ ] LoRa SOS from device to station dashboard, internet off, with ACK
- [ ] Emergency-mode map
- [ ] English/Malayalam toggle
- [ ] Offline sliding-window simulation
- [ ] Dispatcher fleet view

### P2: designed or mocked (clearly labelled)
- [ ] Safe-harbor cold-store option
- [ ] Load Relay / Spare Capacity Pool screens
- [ ] WhatsApp Malayalam voice flow mock
- [ ] Disruption certificate
- [ ] 2018 flood replay

### Demo readiness
- [ ] Full demo run-through with no live-data dependence
- [ ] Backup screen recording captured
- [ ] Hardware runbook rehearsed at least 5 times
- [ ] Feature freeze announced (time: ______)
