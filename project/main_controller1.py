from flask import Flask, request, jsonify
import threading, time, random, requests

app = Flask("Controller1")

CONTROLLER_ID = 1
COORDINATOR = "http://127.0.0.1:6000"

state = "IDLE"
next_request_at = time.time()

aircraft = [{
    "id": f"A{CONTROLLER_ID}",
    "pos": [50, random.randint(50, 450)],
    "controller": CONTROLLER_ID,
    "trail": []
}]

def backoff(seconds=2, jitter=2):
    """Schedule the next time we’ll ask for the token."""
    global next_request_at
    next_request_at = time.time() + seconds + random.random() * jitter

def request_token():
    global state
    try:
        r = requests.post(f"{COORDINATOR}/request", json={"node": CONTROLLER_ID}, timeout=2)
        data = r.json()
        if data.get("granted", False):
            state = "CRITICAL_SECTION"
            print(f"[Node {CONTROLLER_ID}] Token granted → ENTER CS")
        else:
            print(f"[Node {CONTROLLER_ID}] Token request queued at coordinator")
            backoff(2, 3)
    except Exception as e:
        print(f"[Node {CONTROLLER_ID}] Error requesting token: {e}")
        backoff(3, 3)

def release_token():
    global state
    try:
        requests.post(f"{COORDINATOR}/release", json={"node": CONTROLLER_ID}, timeout=2)
        state = "IDLE"
        print(f"[Node {CONTROLLER_ID}] Released token → back to IDLE")
        backoff(1, 2)
    except Exception as e:
        print(f"[Node {CONTROLLER_ID}] Error releasing token: {e}")
        backoff(3, 3)

def poll_coordinator():
    """Check coordinator status to see if this node is the current token holder."""
    global state
    try:
        r = requests.get(f"{COORDINATOR}/status", timeout=2)
        data = r.json()
        holder = data.get("token_holder")
        if holder == CONTROLLER_ID and state == "IDLE":
            state = "CRITICAL_SECTION"
            print(f"[Node {CONTROLLER_ID}] Coordinator shows me as holder → ENTER CS")
    except Exception as e:
        print(f"[Node {CONTROLLER_ID}] Error polling coordinator: {e}")

def simulate():
    global state
    while True:
        if state == "IDLE" and time.time() >= next_request_at:
            print(f"[Node {CONTROLLER_ID}] IDLE → requesting token")
            request_token()

        poll_coordinator()  # check if coordinator has assigned me the token

        for a in aircraft:
            if state == "CRITICAL_SECTION":
                target_x, target_y = 400, 300
                dx = target_x - a["pos"][0]
                dy = target_y - a["pos"][1]

                step_x = 5 if dx > 0 else -5 if dx < 0 else 0
                step_y = 3 if dy > 0 else -3 if dy < 0 else 0

                a["pos"][0] += step_x
                a["pos"][1] += step_y

                if abs(dx) <= 5 and abs(dy) <= 5:
                    print(f"[Node {CONTROLLER_ID}] Aircraft ✈ landed → releasing token")
                    release_token()
                    a["pos"] = [50, random.randint(50, 450)]
            else:
                a["pos"][0] = (a["pos"][0] + 1) % 600

        time.sleep(1)

@app.route("/aircraft")
def get_aircraft():
    return jsonify(aircraft)

@app.route("/nodes")
def get_nodes():
    # Return only the node ID → state mapping (GUI expects this format)
    return jsonify({CONTROLLER_ID: {"state": state}})

if __name__ == "__main__":
    backoff(0, 1)  # allow immediate first request with slight jitter
    threading.Thread(target=simulate, daemon=True).start()
    print(f"[Node {CONTROLLER_ID}] Starting controller on port {5000+CONTROLLER_ID}")
    app.run(port=5000+CONTROLLER_ID, debug=False, use_reloader=False, threaded=True)
