# SafeHaul Kerala — Hardware (Member D)

> **Owner:** Member D  
> **Branch:** `d/hardware`  
> All tunable constants (retry counts, intervals, LoRa settings) are defined in
> `hardware/firmware/truck/config.h` (hardware path) or `hardware/firmware/sim/config.py`
> (simulation path). Do not hard-code them in source files.

---

## 1. Hardware on Hand

| Item | Qty needed | Status | Notes |
|---|---|---|---|
| Heltec WiFi LoRa 32 V2 boards | 2 | **Not yet confirmed** | ESP32 + SX1276 + 128×64 OLED; see §3 for alternatives |
| LoRa antennas (SMA, 868 MHz) | 2 | **Not yet confirmed** | Must match 865–867 MHz India band |
| GPS module (u-blox NEO-6M or similar) | 1 | **Not yet confirmed** | For the "truck" board only; gateway uses fixed demo coords |
| Micro-USB cables | 2 | **Not yet confirmed** | One per board for flashing and serial |
| Laptop with USB-A or USB-C adapter | 1 | Use demo laptop | Runs Django server + gateway bridge |

> **If boards cannot be sourced:** see §5 (Software Simulation Fallback). The demo can run
> entirely on one laptop with no hardware at all. Tell E immediately via `docs/QUESTIONS.md`
> so sourcing can begin in parallel.

### Acceptable alternative boards (same SX127x radio, same Arduino library)

| Board | MCU | OLED | GPS on-board | Notes |
|---|---|---|---|---|
| Heltec WiFi LoRa 32 **V3** | ESP32-S3 | 128×64 | No | Different pin mapping — needs config.h change |
| TTGO LoRa32 V2.1 | ESP32 | 128×64 | No | Very similar to Heltec V2 pins |
| TTGO T-Beam | ESP32 | Optional | **Yes** | Ideal for the "truck" board (built-in GPS + battery) |
| RAK WisBlock | nRF52840 | No | Optional | MicroPython/Arduino both work; different library |

---

## 2. LoRa Radio Settings for India

India's Wireless Planning and Coordination (WPC) Wing designates **865–867 MHz** as the
license-exempt ISM band for short-range devices (comparable to EU 868 MHz).

| Parameter | Value | Why |
|---|---|---|
| Frequency | **865.2 MHz** | Centre of the 865–867 MHz window |
| Bandwidth | **125 kHz** | Standard; good range/speed balance |
| Spreading Factor | **SF 7** | Shortest airtime; ACK round-trip < 1 s at demo range |
| Coding Rate | 4/5 | Default |
| TX Power | **14 dBm** | Well under the 1 W (30 dBm) EIRP limit |
| Sync word | `0x12` | LoRaWAN private network default |
| Preamble | 8 symbols | Default |

> **Verify before the demo:** WPC rules can change. Keep TX power at or below 14 dBm.
> Source: WPC Office, India, "Short Range Devices" exemption list (check current version at
> wpc.gov.in before the event).

---

## 3. Heltec WiFi LoRa 32 V2 — Pin Mapping Reference

Used in `config.h` for both boards.

| Function | GPIO | Notes |
|---|---|---|
| LoRa SCK | 5 | SPI clock |
| LoRa MISO | 19 | |
| LoRa MOSI | 27 | |
| LoRa NSS (CS) | 18 | Chip select |
| LoRa RST | 14 | Radio reset |
| LoRa DIO0 | 26 | TX/RX done interrupt |
| OLED SDA | 4 | I²C data |
| OLED SCL | 15 | I²C clock |
| OLED RST | 16 | OLED reset |
| Button (PRG) | 0 | Active LOW, boot button; use for SOS trigger |
| LED (built-in) | 25 | Blink on TX/RX |

> For V3 or TTGO boards the pin numbers differ — update `config.h` only; no other file changes.

---

## 4. Packet Formats

All fields are **big-endian**.

### 4.1 SOS Packet (14 bytes) — truck → gateway

| Byte(s) | Field | Type | Notes |
|---|---|---|---|
| 0 | `code` | u8 | `01`–`07`; see emergency_codes below |
| 1–2 | `vehicle_id` | u16 | Unique per truck |
| 3 | `seq` | u8 | Sequence number; wraps at 255 |
| 4–7 | `lat` | i32 | Degrees × 1 × 10⁵ (e.g. 10.30660 → 1030660) |
| 8–11 | `lon` | i32 | Degrees × 1 × 10⁵ (e.g. 76.33180 → 7633180) |
| 12–13 | `minutes_of_day` | u16 | UTC minutes since midnight (0–1439) |

### 4.2 ACK Packet (5 bytes) — gateway → truck

| Byte(s) | Field | Type | Notes |
|---|---|---|---|
| 0 | `0x41` | u8 | ASCII `'A'` — ACK marker |
| 1 | `station_id` | u8 | Station that acknowledged |
| 2–3 | `vehicle_id` | u16 | Echo of the SOS vehicle_id |
| 4 | `seq` | u8 | Echo of the SOS seq |

### 4.3 Serial JSON Line (gateway → laptop, one line per received SOS)

```json
{"code":"03","vehicle_id":17,"seq":4,"lat":10.30660,"lng":76.33180,"device_ts":"2026-10-07T08:30:00Z","via":"lora","station_id":1}
```

- `device_ts` is reconstructed from `minutes_of_day` plus the current date (UTC).
- `via` is always `"lora"` for real hardware; `"sim"` for the simulation path.
- One JSON object per line; no trailing comma; terminated with `\n`.

### 4.4 Emergency Code Table

Defined in `data/emergency_codes.json`. Short reference:

| Code | Meaning (English) |
|---|---|
| `01` | SOS — driver needs help |
| `02` | Landslide ahead |
| `03` | Flood ahead |
| `04` | Rescue needed |
| `05` | Need load transfer |
| `06` | Spare capacity offered |
| `07` | All clear |

---

## 5. Software Simulation Fallback

**Use this path until physical boards are confirmed.** The bridge and Django layers are
identical whether the source is real hardware or simulation.

```
truck_sim.py  ──pipe──▶  gateway_sim.py  ──pipe──▶  bridge.py  ──HTTP──▶  Django
```

Scripts live in `hardware/firmware/sim/`. See `hardware/firmware/sim/README.md` for
the run command. All simulation log lines are prefixed with `[SIM]`.

The bridge (`hardware/gateway/bridge.py`) accepts `--sim` to read from stdin instead of
a serial port. No other flag or code change needed to switch between hardware and simulation.

---

## 6. Arduino Library Dependencies (hardware path)

Install these via the Arduino IDE Library Manager or `arduino-cli lib install` before
flashing.

| Library | Version tested | Purpose |
|---|---|---|
| `LoRa` by Sandeep Mistry | ≥ 0.8.0 | SX127x radio driver |
| `U8g2` by olikraus | ≥ 2.34.0 | OLED display |
| `Heltec ESP32 Dev-Boards` | ≥ 1.1.1 | Board package (board manager URL) |

Board Manager URL for Heltec:
```
https://resource.heltec.cn/download/package_heltec_esp32_index.json
```

---

## 7. Flash & Run Instructions

> **To be filled in after D2 firmware is complete.**

### 7.1 Flashing the truck board
_Placeholder — see D2 firmware task._

### 7.2 Flashing the gateway board
_Placeholder — see D2 firmware task._

### 7.3 Running the gateway bridge
```bash
cd hardware/gateway
pip install -r requirements.txt
# Hardware mode (replace /dev/ttyUSB0 with your port):
python bridge.py --port /dev/ttyUSB0
# Simulation mode (no boards needed):
python bridge.py --sim
```

---

## 8. Demo Runbook

> **To be filled in during D9 (demo hardening).**

Short checklist (expand later):

1. Start the Django server: `cd backend && python manage.py runserver`
2. Start the bridge: `python hardware/gateway/bridge.py --port <PORT>` (or `--sim`)
3. Open `/station/` in a browser on the same laptop.
4. **Turn off Wi-Fi** — confirm `localhost:8000` still loads.
5. Press the SOS button on the truck board (or run `truck_sim.py`).
6. Verify the event appears on the station dashboard within ~3 seconds.
7. Click **Acknowledge** — verify the truck board (or sim) shows "RECEIVED by Station 1".

**If the radio link fails mid-demo:** switch to `--sim` mode immediately. The audience
sees identical behaviour. Label it "software simulation" and continue.

---

## 9. Known Limitations & Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Boards not sourced in time | Medium | Simulation fallback (§5) is the demo default |
| LoRa link unreliable in the demo room | Low–Medium | Reduce SF (try SF9 or SF10 for more range); rehearse in the venue |
| GPS cold-start takes > 60 s | Medium | Use fixed demo coordinates in firmware config; GPS is optional for the demo |
| WPC rule change on band | Very low | Demo uses 14 dBm; well within any foreseeable limit |
| Serial port not detected on demo laptop | Low | Test with both Mac and Linux; note correct `/dev/tty*` path |
