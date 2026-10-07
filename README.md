# SafeHaul Kerala

**A flood-aware logistics planner for Kerala.** Built for the IBM x Kerala Government Hackathon 2026, Challenge 5.

> We don't just reroute the truck. We protect the cargo, the driver and the community.

## The problem
During Kerala's monsoon, floods, waterlogging and landslides cut freight corridors. Operators usually learn about a blockage after the truck is already committed, perishable cargo spoils, and drivers in dead network zones cannot call for help.

## What SafeHaul does
- **Predict:** explainable, segment-level flood-risk scores (with confidence and data age) from rainfall, river levels, terrain and flood history.
- **Protect:** safety and cargo shelf life are *hard filters*. The driver gets 2-3 labelled options (reroute / wait / divert-and-store) and an ETA range that updates automatically.
- **Stay connected:** offline corridor map, flood-aware service map, and an emergency signalling ladder (app, SMS, LoRa radio mesh, Morse as a last resort).
- **Help each other:** Load Relay and Spare Capacity Pool (communication and matching only, no payments), crowd and vehicle sensing, voice-first Malayalam on WhatsApp (designed and mocked).

## Repository layout
```
docs/        PRD, team brief, API contract, status and questions
data/        mock and curated datasets (segments, routes, scenarios, service points)
backend/     Django project (risk engine, routing, ETA, service points, weather, emergency)
frontend/    mobile-first map web app (templates + static assets)
hardware/    ESP32 + LoRa firmware and the serial-to-API gateway bridge
```

## Quick start
> To be completed by Member A once the Django skeleton is merged.
```
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env               # then fill in values
python backend/manage.py migrate
python backend/manage.py runserver
```

## Team and workflow
- Branch per person (`a/backend`, `b/frontend`, `c/data`, `d/hardware`); pull requests into `main`.
- Read `AGENTS.md` and `docs/TEAM_BRIEF.md` before contributing.
- Track progress in `docs/STATUS.md`; raise questions in `docs/QUESTIONS.md`.

## Honest limits
Demo data is **simulated or historical** unless labelled `live`. Cold-store availability, police gateway, relief-camp matching, relay user base and some river-gauge feeds are mocked. This is a prototype, not a safety-certified system.

## Data sources and licences
- Map and road data: OpenStreetMap contributors (ODbL). Attribution required.
- Weather: Open-Meteo (check its current terms).
- See `data/SOURCES.md` (maintained by Member C) for the full list.

## Licence
To be decided by the team (add a `LICENSE` file).
