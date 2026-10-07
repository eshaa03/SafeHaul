# SafeHaul Kerala — LoRa Simulation (`hardware/firmware/sim/`)

> **This directory replaces the physical ESP32 boards when hardware is not available.**
> The bridge (`hardware/gateway/bridge.py`) and the Django emergency app cannot
> distinguish simulation output from real hardware output.
> All simulation log lines are prefixed with `[SIM]`.

---

## What is in this directory

| File | Role |
|---|---|
| `config.py` | All tunable constants (vehicle ID, coordinates, retry limits). Edit here only. |
| `truck_sim.py` | Simulates the truck-side LoRa board. Sends SOS JSON, waits for ACK. |
| `gateway_sim.py` | Simulates the gateway board. Relays SOS to bridge; forwards ACK back to truck. |
| `run_demo.sh` | Convenience script: starts all processes in one command (requires `tmux`). |

---

## Quickstart — single terminal, no ACK loop (simplest)

This pipes `truck_sim → gateway_sim → bridge`. The bridge POSTs to Django.
No ACK is returned to truck_sim in this mode (truck will retry until exhausted).
Useful for testing that events appear on the station dashboard.

```bash
# From the repo root — start Django first:
cd backend && python manage.py runserver &
cd ..

# Then run the pipe:
cd hardware/firmware/sim
python truck_sim.py --code 03 | python gateway_sim.py | \
    python ../../gateway/bridge.py --sim
```

You should see `[SIM] TX attempt 1/10 code=03` on stderr from truck_sim,
and `POST /api/emergency/ → 201` from bridge.  Open `http://localhost:8000/station/`
to see the event.

---

## Full demo — named pipes with ACK loop (mirrors real hardware)

This mode fully simulates the two-board loop: truck sends → gateway relays to
bridge → Django stores → bridge polls ack → gateway forwards ACK → truck shows
"RECEIVED".

### Step 1 — create named pipes

```bash
mkfifo /tmp/sos_pipe /tmp/ack_pipe /tmp/bridge_cmd_pipe
```

### Step 2 — start each component in a separate terminal

**Terminal A — Django server**
```bash
cd backend
python manage.py runserver
```

**Terminal B — truck side**
```bash
cd hardware/firmware/sim
python truck_sim.py --code 03 \
    --sos-pipe /tmp/sos_pipe \
    --ack-pipe /tmp/ack_pipe
```

**Terminal C — gateway side**
```bash
cd hardware/firmware/sim
python gateway_sim.py \
    --sos-pipe /tmp/sos_pipe \
    --bridge-ack-pipe /tmp/bridge_cmd_pipe \
    --truck-ack-pipe /tmp/ack_pipe
```

**Terminal D — bridge**
```bash
cd hardware/gateway
python bridge.py --sim --ack-out /tmp/bridge_cmd_pipe
```

### Expected output

```
# Terminal B (truck):
[SIM] truck_sim starting: code=03 vehicle_id=17
[SIM] TX attempt 1/10 code=03 vehicle_id=17 seq=0
[SIM] RECEIVED ACK from Station 1 (attempt 1)

# Terminal C (gateway):
[SIM] gateway: gateway_sim starting (ACK relay enabled)
[SIM] gateway: Relayed SOS code=03 vehicle_id=17 seq=0
[SIM] gateway: ACK forwarded to truck: vehicle_id=17 seq=0

# Terminal D (bridge):
[bridge] RX: {"code":"03","vehicle_id":17,...,"via":"sim"}
[bridge] POST /api/emergency/ → 201
[bridge] Poll: event 1 acked → sending ACK 17 0
```

---

## Changing the emergency code

Pass `--code NN` to truck_sim.  Valid codes:

| Code | Meaning |
|---|---|
| `01` | SOS — driver needs help |
| `02` | Landslide ahead |
| `03` | Flood ahead |
| `04` | Rescue needed |
| `05` | Need load transfer |
| `06` | Spare capacity offered |
| `07` | All clear |

---

## Changing the simulated vehicle or location

Edit `config.py`.  Never hard-code values in `truck_sim.py` or `gateway_sim.py`.

---

## Continuous mode (sustained demo)

```bash
python truck_sim.py --code 01 --auto-interval 20
```

Sends a new SOS every 20 seconds.  Useful for showing the station dashboard
updating live during a presentation.

---

## Cleanup

```bash
rm -f /tmp/sos_pipe /tmp/ack_pipe /tmp/bridge_cmd_pipe
```

Kill background processes with `Ctrl-C` in each terminal, or `kill %1` if
backgrounded.
