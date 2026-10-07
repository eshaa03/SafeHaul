# hardware/firmware/sim/config.py
# All tunable constants for the simulation.
# Do NOT hard-code any of these values in truck_sim.py or gateway_sim.py.

# --- Device identity ---
VEHICLE_ID = 17        # u16: unique per simulated truck
STATION_ID = 1         # u8: station that will ACK

# --- Demo coordinates (Chalakudy river crossing, illustrative) ---
LAT_DEG = 10.30660     # degrees, positive = N
LON_DEG = 76.33180     # degrees, positive = E

# --- Retry behaviour ---
RETRY_INTERVAL_S = 3   # seconds between retransmissions
RETRY_LIMIT = 10       # give up after this many attempts with no ACK

# --- Pipe / IPC ---
# truck_sim writes SOS JSON to stdout; gateway_sim reads from stdin.
# gateway_sim writes ACK lines to stdout; truck_sim reads ACK lines from stdin.
# The bridge reads gateway_sim's stdout and writes ACK commands back to its stdin.
# This means the full pipe is:
#   truck_sim.py  <─┐           (ack lines on stdin)
#                   │
#   gateway_sim.py ─┘           (sos json on stdin, ack commands on stdin from bridge)
#
# In practice run them with named pipes or subprocess; see sim/README.md.
