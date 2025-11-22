from flask import Flask, jsonify
import threading, time
from backend.messaging import LamportMulticast, MutualExclusion, SnapshotManager, NetworkAdapter

app = Flask(__name__)

# -----------------------------
# Global simulation state
# -----------------------------
aircraft = [
    {"id": "A1", "pos": [100, 200], "controller": 1, "trail": []},
    {"id": "A2", "pos": [300, 150], "controller": 2, "trail": []}
]

nodes = {1: {"state": "IDLE"}, 2: {"state": "IDLE"}}
message_log = []

MAX_TRAIL = 20

# -----------------------------
# Networking stubs (replace with real gRPC/SocketIO later)
# -----------------------------
def send_request(resource_id, ts, from_id, to_id):
    print(f"[REQ] {from_id} → {to_id} for {resource_id} @ {ts}")

def send_reply(resource_id, ts, from_id, to_id):
    print(f"[REP] {from_id} → {to_id} for {resource_id} @ {ts}")

def send_release(resource_id, ts, from_id, to_id):
    print(f"[REL] {from_id} → {to_id} for {resource_id} @ {ts}")

net_adapter = NetworkAdapter(send_request, send_reply, send_release)

# -----------------------------
# Instantiate modules
# -----------------------------
multicast = LamportMulticast(controller_id=1, peers=[2])
mutex = MutualExclusion(controller_id=1, peers=[2], net=net_adapter,
                        on_enter=lambda r: log_event("ENTER_CS", 1, r),
                        on_exit=lambda r: log_event("EXIT_CS", 1, r))

def send_marker(to_id, snapshot_id):
    print(f"[MARKER] {1} → {to_id} snapshot {snapshot_id}")

def emit_snapshot(snapshot_id, payload):
    print(f"[SNAPSHOT] {snapshot_id} from controller 1:\n{payload}")

def get_local_state():
    return {
        "aircraft": aircraft,
        "nodes": nodes,
        "log_len": len(message_log)
    }

snapshot_mgr = SnapshotManager(controller_id=1, peers=[2],
                               send_marker=send_marker,
                               emit_snapshot=emit_snapshot,
                               get_local_state=get_local_state)

# -----------------------------
# Simulation loop
# -----------------------------
def log_event(event, node, aircraft_id):
    message_log.append({"event": event, "node": node, "aircraft": aircraft_id})
    if len(message_log) > 50:
        message_log.pop(0)

def simulate():
    while True:
        # Move aircraft
        for a in aircraft:
            a["pos"][0] = (a["pos"][0] + 5) % 600
            a["pos"][1] = (a["pos"][1] + 3) % 400
            a["trail"].append(tuple(a["pos"]))
            if len(a["trail"]) > MAX_TRAIL:
                a["trail"].pop(0)

        # Demonstrate mutual exclusion on runway "RWY_A"
        mutex.request("RWY_A")
        time.sleep(1)
        mutex.release("RWY_A")

        # Periodically trigger snapshot
        if int(time.time()) % 10 == 0:
            snapshot_mgr.start_snapshot(snapshot_id=f"snap-{int(time.time())}")

        time.sleep(1)

# -----------------------------
# API endpoints
# -----------------------------
@app.route("/aircraft")
def get_aircraft():
    return jsonify(aircraft)

@app.route("/nodes")
def get_nodes():
    return jsonify(nodes)

@app.route("/logs")
def get_logs():
    return jsonify(message_log)

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=simulate, daemon=True).start()
    app.run(port=5000, debug=True)
