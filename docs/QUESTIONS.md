# Open Questions

**How to use:** agents cannot talk to each other directly, so this file is the message board. Append only; never delete other people's lines. **E (human coordinator) answers and moves resolved items to the "Resolved" section.** While waiting for an answer, continue with a mock, stub or a clearly stated assumption.

Format:
`[YYYY-MM-DD] [from X to Y] Question. (Blocking: yes/no)`
Answer format (added by the answerer under the question):
`  -> [YYYY-MM-DD] [Y] Answer.`

---

## Open

[2026-10-08] [from D to E] Need 2x Heltec WiFi LoRa 32 V2 boards (or TTGO LoRa32 V2.1 / T-Beam as fallback) + 2x 868 MHz SMA antennas + 1x GPS module (u-blox NEO-6M or similar) + 2x micro-USB cables for the SOS demo. Can these be sourced before the demo? Using software simulation fallback in the meantime. (Blocking: no — simulation path works without boards)

[2026-10-08] [from C to E] `data/emergency_codes.json` has codes 01–07 with English text, but the `ml` (Malayalam) field is empty. Please arrange native Malayalam review and fill in the `ml` field before the demo. Do NOT use machine translation. (Blocking: no — demo can run with English only, but Malayalam is required for P1 UI toggle)

## Resolved

<!-- Move answered items here, keeping the question and answer together. -->

---

## Decisions log (agreed by the team; changes need E's approval)
- API field names follow `docs/TEAM_BRIEF.md` section 1.10.
- Safety and cargo shelf life are hard filters.
- Mock data first; live APIs have automatic fallback.
- Database for the MVP is SQLite (PostGIS only if time remains).
- Candidate routes are precomputed in `data/routes.json`; live OSRM is a stretch goal.
- No payment handling anywhere in the product.
