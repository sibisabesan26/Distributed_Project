from flask import Flask, jsonify
import threading, time
from backend.messaging import SnapshotManager, NetworkAdapter, MessageLogger
from backend.multicast import MulticastManager
from backend.heartbeat import HeartbeatManager
from backend.scalability import NodeRegistry

app = Flask(__name__)

# -----------------------------
# Global state
# -----------------------------
aircraft = [{"id": "A1", "pos": [100, 200], "controller": 1, "trail": []}]
nodes = {1: {"state": "IDLE"}}
message_log = MessageLogger()
MAX_TRAIL = 20

# -----------------------------
# Queue helpers
# -----------------------------
def get_queue():
    try:
        with open("runway_queue.txt", "r") as f:
            return [int(x) for x in f.read().strip().split(",") if x]
    except:
        return []

def set_queue(q):
    with open("runway_queue.txt", "w") as f:
        f.write(",".join(str(x) for x in q))

def enqueue(node_id):
    q = get_queue()
    if node_id not in q:
        q.append(node_id)
        set_queue(q)

def dequeue(node_id):
    q = get_queue()
    if node_id in q:
        q.remove(node_id)
        set_queue(q)

# -----------------------------
# Logging and state
# -----------------------------
def log_event(event, node, aircraft_id):
    message_log.add(event, node, aircraft_id)

def set_node_state(node_id, state):
    nodes[node_id]["state"] = state
    log_event(state, node_id, "RWY_A")
    # Broadcast state change via multicast
    multicast.send({"node": node_id, "state": state, "timestamp": time.time()})

# -----------------------------
# Networking stubs
# -----------------------------
net_adapter = NetworkAdapter(
    send_request=lambda *args: None,
    send_reply=lambda *args: None,
    send_release=lambda *args: None
)

# -----------------------------
# Snapshot Manager
# -----------------------------
snapshot_mgr = SnapshotManager(
    controller_id=1,
    peers=[2],
    send_marker=lambda to, sid: multicast.send({"type": "MARKER", "to": to, "sid": sid}),
    emit_snapshot=lambda sid, payload: print(f"[SNAPSHOT] {sid} from controller 1:\n{payload}"),
    get_local_state=lambda: {"aircraft": aircraft, "nodes": nodes, "log": message_log.get()}
)

# -----------------------------
# Multicast, Heartbeat, Registry
# -----------------------------
multicast = MulticastManager()
registry = NodeRegistry()
heartbeat = HeartbeatManager(peers=["http://127.0.0.1:5002"], timeout=5)

def handle_multicast(msg):
    print(f"[MULTICAST RECEIVED] {msg}")
    # TODO: integrate with queue/CS logic for total order

multicast.listen(handle_multicast)
heartbeat.monitor(lambda peer: print(f"[FAILURE DETECTED] {peer}"))

# Register self
registry.add_node(1, "http://127.0.0.1:5001")

# -----------------------------
# Simulation loop
# -----------------------------
def simulate():
    while True:
        # Move aircraft trails (background animation)
        for a in aircraft:
            a["pos"][0] = (a["pos"][0] + 5) % 600
            a["pos"][1] = (a["pos"][1] + 3) % 400
            a["trail"].append(tuple(a["pos"]))
            if len(a["trail"]) > MAX_TRAIL:
                a["trail"].pop(0)

        # Queue-based runway access
        if nodes[1]["state"] == "IDLE":
            enqueue(1)
            q = get_queue()
            if q and q[0] == 1:
                set_node_state(1, "CRITICAL_SECTION")
                # stays in CS until GUI calls /release

        # Periodic snapshot
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
    return jsonify(message_log.get())

@app.route("/release")
def release():
    # Called by GUI when aircraft reaches runway
    dequeue(1)
    set_node_state(1, "IDLE")
    return jsonify({"status": "released", "queue": get_queue()})

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=simulate, daemon=True).start()
    app.run(port=5001, debug=True)
