# SafeHaul Kerala: Agent Rules

Project: flood-aware logistics planner for Kerala (IBM x Kerala Government Hackathon 2026, Challenge 5).

## Start of every session (do this first)
1. `git pull origin main`, then merge/rebase `main` into your branch.
2. Read `docs/TEAM_BRIEF.md` (Part 1, plus the section for your member letter A/B/C/D).
3. Read `docs/CONTRACT.md` (API contract), `docs/STATUS.md` and `docs/QUESTIONS.md`.
4. Work only on your own tasks and files.

## Stack
Python + Django + Django REST Framework, SQLite, Leaflet frontend served by Django (no Node build step), ESP32 + LoRa hardware for the SOS demo.

## Hard rules
- Safety is a HARD FILTER. Cargo shelf life is a second HARD FILTER. Never decide silently: present 2-3 labelled options with trade-offs.
- Every risk score has reasons, confidence, `data_source` and `data_timestamp`.
- Every data item carries `data_source`: `live` | `simulated` | `historical`. The UI shows a SIMULATED DATA banner when relevant.
- Warnings lean conservative. Never show a bare "safe". ETA is always a range with a reason.
- Mock data first. Live APIs always have automatic fallback to mock. The demo must not depend on live feeds.
- No in-house weather model. No payment code. No external CDN dependencies in the frontend (bundle assets locally).
- All tunable constants (weights, thresholds, speeds) live in `backend/safehaul/config.py`. Do not hard-code them elsewhere.
- No secrets in the repo. This repository is PUBLIC. Use environment variables and `.env` (git-ignored). Use fake data only; no real phone numbers, registrations or personal data.

## Ownership (edit only your own files)
| Member | Owns |
|---|---|
| A | `backend/safehaul/`, `backend/risk/`, `backend/routing/`, `backend/servicepoints/`, core tests, `docs/CONTRACT.md` |
| B | everything in `frontend/` |
| C | everything in `data/`, `backend/weather/`, data/weather tests |
| D | everything in `hardware/`, `backend/emergency/`, emergency tests |
| E (human) | `docs/PRD.md`, `README.md`, `AGENTS.md`, demo script, slides |

Need a change in someone else's area? Append a line to `docs/QUESTIONS.md` and continue with a mock or stub.

## API contract
Defined in `docs/TEAM_BRIEF.md` section 1.10 and mirrored in `docs/CONTRACT.md`. Do not change field names without E's approval. Additive fields are OK.

## Git rules
- One branch per person: `a/backend`, `b/frontend`, `c/data`, `d/hardware`. Never commit directly to `main`; open a pull request.
- Small, frequent commits with clear messages (for example `B: risk overlay popup with reasons`).
- `main` must always run. Merge only working code.
- Update only your own section in `docs/STATUS.md` at the end of each work session.

## Quality
- Write tests for risk scoring, hard filters, ETA, flood memory and the emergency API.
- Handle missing or empty data gracefully (clear message, never crash).
- Keep UI text in the i18n files (English and Malayalam), not in code.

## How to work with Bob
- Use Plan mode before each phase, Code mode to implement, Ask mode to understand code.
- Give small, specific tasks and paste example data into prompts.
- Review what Bob writes before committing. You must be able to explain it.
