# Project Status

**How to use:** each member updates **only their own section**, at the end of every work session. Keep entries short and factual. Commit the file with your branch. Other agents read this at the start of each session to see what is available and what is blocked.

Format for each entry: `YYYY-MM-DD HH:MM: what changed`.
Legend: Done / In progress / Blocked / Next.

---

## Member A: Backend and Risk Engine
- **Done:**
- **In progress:**
- **Blocked (waiting on whom/what):**
- **Next:**
- **Endpoints available on `main`:** (list)

## Member B: Frontend and Map
- **Done:**
- **In progress:**
- **Blocked (waiting on whom/what):**
- **Next:**
- **Using:** sample JSON / real API (circle one)

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
- **Done:**
- **In progress:**
- **Blocked (waiting on whom/what):**
- **Next:**
- **Hardware on hand:** (boards, GPS, antennas, cables)

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
