# Project Status

**How to use:** each member updates **only their own section**, at the end of every work session. Keep entries short and factual. Commit the file with your branch. Other agents read this at the start of each session to see what is available and what is blocked.

Format for each entry: `YYYY-MM-DD HH:MM: what changed`.
Legend: Done / In progress / Blocked / Next.

---

## Member A: Backend and Risk Engine
- **Done:** A1 complete — Django 5.2/DRF skeleton; all apps (risk, routing, servicepoints, weather stub, emergency stub); `safehaul/config.py` (all §1.11 constants); `safehaul/data_loader.py` (reads `data/`; falls back to `tests/fixtures/` with visible WARNING); `GET /api/scenario/`, `POST /api/scenario/`, `GET /api/routes/`; 19/19 A1 tests passing; `docs/CONTRACT.md` written.
- **In progress:** A2 — risk engine (`risk/engine.py`, `GET /api/segments/`)
- **Blocked (waiting on whom/what):** `data/` files from C (stand-in fixture is live and working)
- **Next:** A2 → A3 (ETA) → A4 (options) → A5 (service points)
- **Endpoints available on `main`:** `GET /api/scenario/`, `POST /api/scenario/`, `GET /api/routes/`

## Member B: Frontend and Map
- **Done:** B0 (sample JSON — all 6 files, full contract), B1 (base template, Leaflet map, SIMULATED banner, language toggle, config/api/i18n scaffold, standalone Django project)
- **In progress:** —
- **Blocked (waiting on whom/what):** A's Django skeleton for full integration (workaround: `frontend_project/manage.py runserver`)
- **Next:** B2 (risk overlay patterns + segment detail popup)
- **Using:** sample JSON

## Member C: Data and Integrations
- **Done:**
- **In progress:**
- **Blocked (waiting on whom/what):**
- **Next:**
- **Data files on `main`:** (list)

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
