# Open Questions

**How to use:** agents cannot talk to each other directly, so this file is the message board. Append only; never delete other people's lines. **E (human coordinator) answers and moves resolved items to the "Resolved" section.** While waiting for an answer, continue with a mock, stub or a clearly stated assumption.

Format:
`[YYYY-MM-DD] [from X to Y] Question. (Blocking: yes/no)`
Answer format (added by the answerer under the question):
`  -> [YYYY-MM-DD] [Y] Answer.`

---

## Open

<!-- Example (delete once real entries exist):
[2026-10-08] [from B to A] The options response has no `route_geometry` field; may I get the segment IDs from /api/routes/ instead? (Blocking: no)
-->

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
