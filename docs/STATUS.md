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
- **In progress:**
- **Blocked (waiting on whom/what):**
- **Next:**
- **Data files on `main`:** (list)

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
