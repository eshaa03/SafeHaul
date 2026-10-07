# Product Requirement Document

**IBM x Kerala Government Hackathon 2026, Challenge 5**

Priority tags: **P0** = must work flawlessly; **P1** = demo highlight; **P2** = designed, partly built or mocked (clearly labelled).

---

## 1. Problem Title

**SafeHaul Kerala: A Flood-Aware Logistics Planner for Route Safety, Cargo Protection and Emergency Communication**

---

## 2. Problem Statement

During Kerala's monsoon, floods, waterlogging, landslides and bridge or underpass closures regularly cut road freight corridors. The core problem is **late and fragmented information**:

- Operators usually learn about a blockage after the truck has started its journey or reached the blocked point.
- Turning back wastes fuel, driver hours and time. For perishable cargo such as vegetables, fish and dairy, it directly causes spoilage and financial loss.
- Mainstream navigation apps show traffic, not flood risk. They also ignore truck constraints (height, weight, wading capability) and cargo constraints (shelf life).
- When a truck breaks down or is stranded, there is no quick way to move its cargo to another vehicle.
- In flood or landslide zones mobile networks can fail, leaving drivers unable to call for help.

**Why it matters:** the cost falls on small transport operators with thin margins, on farmers and traders who lose produce, and on drivers who face physical danger. Reliable logistics also matters for food supply and relief delivery during disasters.

---

## 3. Target Users

| Group | Who | Primary need |
|---|---|---|
| Primary | Lorry operators and owner-drivers | Know route risk before and during the trip; have a safe alternative |
| Primary | Logistics companies and fleet dispatchers | Monitor many vehicles; decide which loads go, wait or divert |
| Primary | FMCG distributors | Reliable delivery times and updated ETAs |
| Primary | Agricultural traders and farmer collectives | Protect perishable cargo; reduce spoilage |
| Secondary | Receivers (markets, retailers, warehouses) | Accurate arrival information |
| Secondary | Cold storage and warehouse operators | Fill spare capacity; receive diverted loads |
| Secondary | Police, fire and rescue stations; disaster authorities | Receive structured emergency signals |

---

## 4. Existing Problem / Current System

**How people cope today:** WhatsApp forwards, phone calls to other drivers and word of mouth; generic navigation apps; weather apps and TV/news bulletins; official channels (IMD, KSDMA, district alerts) that are not tailored to individual road segments or truck journeys; SMS or phone calls for emergencies, which fail when the network is down.

| Gap | Consequence |
|---|---|
| Weather forecasts are not translated into road-segment consequences | Operators see rainfall but not "this underpass will likely flood" |
| Routing ignores flood risk, cargo shelf life and vehicle limits | A route may be "fastest" yet unsafe or spoil the cargo |
| No offline, risk-aware corridor navigation | Drivers lose guidance exactly when signal fails |
| No fallback emergency communication | SOS is impossible in a dead zone |
| No way to relocate cargo from a stranded vehicle | The load is delayed or lost |
| Freight marketplaces exist but are not flood-aware, proximity-based or emergency-oriented | They do not address disaster conditions |
| Risk scores, where they exist, are unexplained | Drivers do not trust them |

---

## 5. Proposed Solution

SafeHaul Kerala is a mobile-first (PWA) route-planning and logistics-visibility platform with a dispatcher dashboard. It protects the **truck, the driver, the cargo and the community** through four pillars.

**Pillar 1: Predict (know before you go)**
- Segment-level flood-risk scoring combining static factors (elevation, river proximity, underpasses, landslide-prone slopes, flood history), dynamic factors (recent and forecast rainfall, river and dam levels, official alerts) and crowd/vehicle signals.
- Every score is **explainable** ("High: 92 mm in 24 h, river at 85% of danger level, this underpass flooded in 2018") and shows a confidence level and data age.
- **Segment flood memory** records the rainfall level at which each segment has flooded before.
- Weather is **ingested** (IMD / Open-Meteo), not modelled in-house. The added value is translating rainfall into road-segment consequences.

**Pillar 2: Protect (safety first, cargo second, cost and time after)**
- Routing applies **hard filters**: unsafe segments and routes exceeding the cargo shelf life or the vehicle's limits are rejected. Cost and time are optimised only among what remains.
- The driver sees **2-3 labelled options** with trade-offs (reroute / wait / divert-and-store). Nothing is decided silently.
- **Safe-harbor network:** for perishables on a blocked route, compare divert-and-store (cold store or ice plant), wait and reroute by expected cargo value saved.
- **Auto-updating ETA** as a range with a reason, pushed to the receiver.

**Pillar 3: Stay connected (works when the network does not)**
- **Offline sliding-window corridor map:** download the corridor ahead with a timestamped risk snapshot and service points; keep a configurable **retreat buffer** behind the vehicle (turning back is the most common flood response) and delete beyond it.
- **Emergency signalling ladder:** app data, then SMS, then LoRa radio mesh with a compact coded packet, then Morse via torch or horn as a zero-hardware last resort.
- **Code set:** `01` SOS, `02` landslide ahead, `03` flood, `04` rescue needed, `05` need load transfer, `06` spare capacity offered, `07` all clear. Signals are acknowledged; nearby trucks receive peer warnings directly.
- **Flood-aware service map:** hospitals, fuel, repair and towing, police and fire, safe halt points, cold stores, food and toilets, ranked by **safe reachable time** rather than straight-line distance, with a "last verified" time. Emergency mode shows only hospitals, police, fire and high ground.

**Pillar 4: Help each other (community layer)**
- **Load Relay (truck-to-truck):** a driver with a breakdown or stranded vehicle requests that nearby trucks with spare capacity take the cargo.
- **Spare Capacity Pool (warehouse-to-truck):** companies post stock for delivery to a point; trucks with spare capacity respond.
- **Communication and matching only, no payment handling.** The platform offers a suggested rate range and a settlement record. Handover uses QR/OTP confirmation, a photo checklist and a digital handover note.
- **Trucks as passive sensors** (phone GPS/accelerometer detect slowdowns and stopped queues) and a **truck-relative depth scale** (tyre mid-height, wheel hub, floorboard) compared against vehicle-specific crossing limits.
- **Voice-first Malayalam on WhatsApp:** drivers send a voice note and receive a short voice/text reply; watsonx.ai (subject to verified availability) parses messy inputs and forwarded bulletins and generates plain-language Malayalam advisories.

**Example flow (Palakkad to Kochi, vegetables, 8-hour shelf life):**
1. The operator enters origin, destination, cargo, shelf-life window, departure time and vehicle type.
2. The system scores every segment and evaluates candidate routes.
3. It warns: "Main route has high flood risk between X and Y in the next 4 hours (confidence: moderate)."
4. It presents options: reroute with a revised ETA range, wait, or divert to a cold store.
5. En route, if conditions change, a live alert and updated ETA go to the driver and receiver.
6. If the truck is stranded, a Load Relay request ranks nearby trucks and proposes a safe handover point.
7. With no signal, an SOS goes out over the LoRa mesh to the nearest gateway station, which acknowledges it.

---

## 6. Functional Requirements

### A. Route visualisation and risk mapping
| ID | Requirement | Priority |
|---|---|---|
| FR-A1 | Display origin-destination route(s) on an interactive map with live vehicle position | P0 |
| FR-A2 | Overlay segment-level flood risk (low / medium / high / closed) and weather alerts | P0 |
| FR-A3 | Compute a risk score per segment from static, dynamic and crowd/vehicle factors | P0 |
| FR-A4 | Show an explanation for every score, a confidence indicator and the data timestamp | P0 |
| FR-A5 | Maintain segment flood memory (learned rainfall triggers) | P2 |
| FR-A6 | Estimate time-dependent crossing windows where river-gauge data exists | P2 |

### B. Weather and alerts
| ID | Requirement | Priority |
|---|---|---|
| FR-B1 | Ingest rainfall forecasts (IMD / Open-Meteo) and official warnings (KSDMA / IMD / NDMA) | P0 |
| FR-B2 | Translate rainfall into segment-level consequences (no in-house weather model) | P0 |
| FR-B3 | Alert drivers and dispatchers when risk on their route changes materially | P0 |

### C. Risk-aware routing and decision support
| ID | Requirement | Priority |
|---|---|---|
| FR-C1 | Generate multiple candidate routes and apply hard safety filters before optimising cost and time | P0 |
| FR-C2 | Apply cargo shelf life as a hard constraint and vehicle limits (height, wading capability) as filters | P0 |
| FR-C3 | Present 2-3 labelled options with trade-offs; never decide silently | P0 |
| FR-C4 | Re-evaluate the route continuously and alert on material change | P0 |

### D. ETA
| ID | Requirement | Priority |
|---|---|---|
| FR-D1 | Compute ETA as a range with reasons (reduced speeds, detours, time of day, rest breaks) | P0 |
| FR-D2 | Update ETA automatically on reroute or disruption and notify the receiver | P0 |
| FR-D3 | Compare ETA against the cargo window and flag shelf-life breaches | P0 |

### E. Cargo protection and safe-harbor network
| ID | Requirement | Priority |
|---|---|---|
| FR-E1 | Maintain a curated list of cold stores, ice plants and warehouses (mock availability) | P2 |
| FR-E2 | Run each storage site through the risk engine (flood exposure, power risk) | P2 |
| FR-E3 | Compare divert-and-store, wait and reroute by estimated cargo value saved | P2 |

### F. Offline operation
| ID | Requirement | Priority |
|---|---|---|
| FR-F1 | Download the corridor ahead (route, risk snapshot, service points) for offline use | P1 |
| FR-F2 | Sliding window: keep a configurable retreat buffer behind the vehicle, delete beyond it | P1 |
| FR-F3 | Show the age of offline risk data prominently; re-sync when connectivity returns | P1 |
| FR-F4 | Prioritise hospitals, police and high-ground points in the offline cache | P1 |

### G. Service map
| ID | Requirement | Priority |
|---|---|---|
| FR-G1 | Show hospitals, fuel, repair/tyre, towing, police/fire, safe halt points, food and toilets | P0 (hospital, fuel, repair, police, safe halt); P2 (others) |
| FR-G2 | Rank service points by safe reachable time, not straight-line distance | P0 |
| FR-G3 | Show "last verified" time per point; allow driver confirmation | P2 |
| FR-G4 | Switch to emergency mode on alert or SOS | P1 |

### H. Emergency communication
| ID | Requirement | Priority |
|---|---|---|
| FR-H1 | Send coded messages (`01`-`07`) via app data, then SMS, then LoRa mesh, with graceful degradation | P1 |
| FR-H2 | LoRa device (ESP32 + LoRa + GPS) sends a compact packet: code, GPS, time, vehicle ID | P1 |
| FR-H3 | Repeat the signal until acknowledged; show "received by Station X" | P1 |
| FR-H4 | Relay packets between trucks and broadcast peer warnings with no internet | P1 |
| FR-H5 | Gateway at a police/control station forwards messages to a dashboard (simulated in the demo) | P1 |
| FR-H6 | Morse via torch or horn as a manual last-resort pattern guide | P2 |
| FR-H7 | Attach nearest reachable help to the SOS payload | P2 |

### I. Load Relay and Spare Capacity Pool
| ID | Requirement | Priority |
|---|---|---|
| FR-I1 | Driver posts a Load Relay request with one tap (cargo, weight, destination, cargo window) | P2 |
| FR-I2 | Warehouses post stock-delivery requests (pickup, drop, deadline) | P2 |
| FR-I3 | Match trucks by direction fit, added detour, flood-safe reachability, vehicle compatibility and time remaining | P2 |
| FR-I4 | Propose a flood-safe, preferably covered handover point | P2 |
| FR-I5 | Structured handover: QR/OTP confirmation, photo checklist, digital handover note | P2 |
| FR-I6 | Suggested rate range and settlement record, with **no payment processing** | P2 |
| FR-I7 | Verified profiles, ratings, trusted-circle mode and live location sharing during relay | P2 |

### J. Crowd and vehicle sensing
| ID | Requirement | Priority |
|---|---|---|
| FR-J1 | Detect sudden slowdowns and stopped queues from phone GPS/accelerometer data (opt-in) | P2 |
| FR-J2 | Drivers report water depth using the truck-relative scale, with optional photo | P2 |
| FR-J3 | Apply vehicle-specific crossing limits to depth reports | P2 |
| FR-J4 | Score crowd reports for trust (reporter history, geotag/timestamp, corroboration) | P2 |

### K. WhatsApp and Malayalam interface
| ID | Requirement | Priority |
|---|---|---|
| FR-K1 | Accept voice notes and text on WhatsApp; respond in voice or text | P2 |
| FR-K2 | Parse unstructured inputs and forwarded bulletins into structured alerts (watsonx.ai) | P2 |
| FR-K3 | Generate plain-language Malayalam advisories; support English and Malayalam in the app | P1 (UI language); P2 (voice) |

### L. Dispatcher dashboard
| ID | Requirement | Priority |
|---|---|---|
| FR-L1 | Show fleet positions, route risk and ETA for all vehicles | P1 |
| FR-L2 | Triage board ranking loads (perishables and most-at-risk first) with go / hold / divert | P2 |
| FR-L3 | Generate a disruption certificate (timestamped GPS trail, alerts, closure evidence) for insurance and force-majeure claims | P2 |

### M. Simulation and replay
| ID | Requirement | Priority |
|---|---|---|
| FR-M1 | "Flood event" toggle to simulate disruptions for a reliable demonstration | P0 |
| FR-M2 | Historical replay of 2018 flood conditions to compare recommendations with actual outcomes | P2 |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | Route and risk computation within a few seconds for one corridor; smooth map interaction on mid-range Android phones; alerts within about 1 minute of a risk change (target) |
| Reliability | Core navigation and emergency functions work offline; graceful degradation if a data feed fails (last known data shown with its age) |
| Data integrity and honesty | Every risk score and ETA carries a timestamp, confidence and data source; stale or missing data is labelled; warnings lean conservative because a false "safe" is worse than a false "caution" |
| Usability | Mobile-first, large touch targets, readable in a moving vehicle in poor light; Malayalam and English; voice interaction for hands-busy use; minimal icons by default with filters |
| Low bandwidth | Works on 2G/3G and patchy connections; compressed payloads; SMS and mesh fallbacks |
| Security and privacy | Encrypted transport; role-based access (driver, dispatcher, station, admin); location sharing only with consent; opt-in passive sensing; minimal personal data retention; no secrets or personal data in the public repository |
| Trust and safety | Verified profiles for relay participants; abuse and spam controls on reports; audit trail for handovers |
| Scalability | Corridor-first (Palakkad-Kochi), extensible to other Kerala corridors; modular data connectors |
| Maintainability | Modular services (risk engine, routing, comms, relay); documented APIs; thresholds and weights in configuration |
| Compliance awareness | Check LoRa spectrum rules, data and alert usage terms, goods-carriage permits and e-way bill requirements before any real deployment |

---

## 8. Inputs

| Category | Input | Source / form |
|---|---|---|
| User | Origin, destination, departure time, vehicle type, cargo type, weight, shelf-life window, receiver contact | App / WhatsApp / dashboard form |
| Road data | Road network, bridges, underpasses, truck restrictions | OpenStreetMap plus curated corrections |
| Terrain | Elevation, flood-prone zones, historical flood extents (2018/2019), landslide-prone areas | DEM/SRTM, Bhuvan, historical records |
| Weather | Rainfall observations and forecasts, warnings | IMD, Open-Meteo |
| Hydrology | River gauge levels, dam release notices | CWC, KSEB, irrigation dept. (where parseable), plus labelled simulated data |
| Official alerts | District warnings, disaster alerts | KSDMA, NDMA Sachet (CAP) |
| Vehicle sensing | GPS position, speed, accelerometer data | Phone sensors (opt-in) |
| Crowd reports | Water depth (truck-relative scale), photos, road status, service-point confirmations | Driver app / WhatsApp |
| Device signals | Coded packets (`01`-`07`), GPS, vehicle ID | LoRa module, SMS |
| Service points | Hospitals, fuel, repair, police, cold stores, safe halt points | OSM Overpass plus manual curation |
| Relay data | Load requests, spare capacity postings, vehicle capacity and type | Driver / warehouse input |
| Unstructured text/voice | Voice notes, forwarded bulletins | WhatsApp, processed with watsonx.ai |

---

## 9. Outputs

| Output | Description |
|---|---|
| Risk map | Segment-level overlays with score, explanation, confidence and data age |
| Route options | 2-3 labelled alternatives (reroute / wait / divert-and-store) with trade-offs |
| ETA | Range with reasons, auto-updated and shared with the receiver |
| Cargo window check | Pass/fail against shelf life with time remaining |
| Alerts | App push, SMS, WhatsApp, voice and text (Malayalam / English) |
| Offline package | Corridor, risk snapshot, service points, retreat buffer |
| Service map results | Nearest reachable hospitals, fuel, repair, police and safe halt points |
| Emergency messages | Coded signals, acknowledgements, peer warnings, station dashboard alerts |
| Relay matches | Ranked candidate trucks, proposed handover points, handover notes and tracking |
| Fleet view | Dispatcher dashboard and load triage board |
| Disruption certificate | Timestamped evidence pack for insurance and force-majeure claims |
| Replay report | Comparison of system recommendations against the 2018 flood timeline |

---

## 10. Technology Requirements

| Layer | Technology |
|---|---|
| Backend | Python, Django and Django REST Framework (Celery + Redis for scheduled ingestion if time allows) |
| Database | **SQLite for the MVP** (geometry stored as JSON); PostgreSQL + PostGIS as the long-term option |
| Routing | MVP: **precomputed candidate routes** evaluated by the backend; stretch: OSRM / GraphHopper / Valhalla on OSM data with a custom cost function |
| Risk engine | Rule-based, weighted, explainable scoring; per-segment rainfall-trigger statistics; optional gradient-boosting model only if enough historical data exists |
| AI/ML | watsonx.ai for parsing unstructured alerts and generating Malayalam advisories (verify availability; mock otherwise); optional speech-to-text and text-to-speech |
| Frontend | Mobile-first PWA served by Django; Leaflet map; service worker and local caching for offline use |
| Maps and data | OpenStreetMap, Overpass API, DEM/SRTM, Bhuvan |
| External APIs | Open-Meteo, IMD, NDMA Sachet (CAP), CWC/dam data where accessible |
| Messaging | WhatsApp Business API (sandbox or mock for the demo), SMS gateway (mock) |
| Hardware | ESP32 + LoRa (SX127x) + GPS for trucks and a gateway unit; Python serial-to-API bridge; optional ultrasonic water-level sensors |
| Dashboard | Web dashboards for dispatchers and a simulated police/control-room station view |
| DevOps | GitHub (public repo), Docker optional, environment-based configuration |
| Development tooling | IBM Bob IDE |

---

## 11. Constraints

| Constraint | Detail |
|---|---|
| Time and scope | Hackathon timeframe; the P0 core must be polished before anything else |
| Data availability | Official flood and river data can be delayed, patchy or hard to parse; the demo uses real APIs where possible plus clearly labelled simulated or historical data |
| OSM coverage | Truck-specific services are thinly covered in India; the demo corridor's service points are manually curated |
| Model limits | No in-house weather model; any trained risk model is limited by available historical data and described honestly |
| Connectivity | Network failure is a design assumption; LoRa range depends on terrain and foliage (typically a few km in real conditions) |
| Radio regulations | LoRa operation must follow Indian licence-exempt band and power rules (verify current rules) |
| Infrastructure dependency | Police and rescue gateways need partnership and installation; simulated in the demo |
| Legal and regulatory | Goods-carriage permits, e-way bills, liability for cargo during transfer and platform terms need legal review. The platform is a communication and matching tool, not a payment platform, but this does not assume that removes responsibility |
| Privacy | Passive sensing and location sharing require explicit consent; the repository is public, so no secrets or personal data |
| Network effect | Load Relay needs enough participating trucks; the product must deliver value standalone |
| Mocked integrations (labelled in the demo) | Cold-store availability, police gateway, relief-camp matching, relay user base, live river-gauge feeds where unavailable |

---

## 12. Expected Outcome

**What the solution should achieve**
- Shift operators from reactive to **proactive** decision-making, with warnings before a vehicle commits to a risky stretch.
- Reduce losses by checking every route and option against the cargo's shelf life.
- Keep drivers connected and visible during network failures through the signalling ladder.
- Give stranded cargo a recovery path through safe-harbor storage and Load Relay.
- Build trust through explainable risk scores, honest confidence levels and clear data ages.
- Give dispatchers and receivers automatically updated ETAs and evidence records.

**Targets to validate in a pilot (hypotheses, not claims)**
- Fewer trips turned back after departure
- Lower perishable spoilage on disrupted trips
- Earlier detection than official or informal alerts on test events (checked via 2018/2019 replay)
- An SOS acknowledged end to end with no internet in the hardware demo

**Demo success criteria**
1. Route, risk overlay, risk-aware reroute, ETA range and cargo-window check work flawlessly.
2. Flipping the flood simulation visibly changes the risk, route options, ETA and the "nearest reachable hospital".
3. A live LoRa SOS from one device appears on the station dashboard with the internet switched off, and is acknowledged.

**Pitch line:** *"We don't just reroute the truck. We protect the cargo, the driver and the community."*
