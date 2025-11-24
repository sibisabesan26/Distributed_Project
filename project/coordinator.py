from flask import Flask, request, jsonify

app = Flask("Coordinator")

# Current token holder and waiting queue
token_holder = None
queue = []
queued_set = set()   # track nodes already in queue

@app.route("/request", methods=["POST"])
def handle_request():
    global token_holder, queue, queued_set
    data = request.get_json()
    node = data["node"]

    # If no token holder, grant immediately
    if token_holder is None:
        token_holder = node
        print(f"[Coordinator] Granted token to Node {node}")
        return jsonify({"granted": True})

    # If node already queued, ignore duplicate
    if node in queued_set or node == token_holder:
        print(f"[Coordinator] Node {node} already waiting or holding token. Ignoring duplicate request.")
        return jsonify({"granted": False})

    # Otherwise, add to queue
    queue.append(node)
    queued_set.add(node)
    print(f"[Coordinator] Node {node} queued. Current queue: {queue}")
    return jsonify({"granted": False})

@app.route("/release", methods=["POST"])
def handle_release():
    global token_holder, queue, queued_set
    data = request.get_json()
    node = data["node"]

    if token_holder == node:
        if queue:
            # Pass token to next node in queue
            token_holder = queue.pop(0)
            queued_set.discard(token_holder)
            print(f"[Coordinator] Token passed to Node {token_holder}")
        else:
            # No waiting nodes
            token_holder = None
            print(f"[Coordinator] Token released, no waiting nodes")
    else:
        print(f"[Coordinator] Node {node} tried to release but is not the holder.")
    return jsonify({"status": "ok"})

@app.route("/status")
def status():
    """Expose current token holder and queue for controllers/GUI polling."""
    return jsonify({
        "token_holder": token_holder,
        "queue": queue
    })

if __name__ == "__main__":
    print("[Coordinator] Starting on port 6000")
    app.run(port=6000, debug=False, use_reloader=False, threaded=True)
