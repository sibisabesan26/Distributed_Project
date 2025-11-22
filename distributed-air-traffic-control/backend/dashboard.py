from flask import Flask, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder="static")

CONTROLLERS = {
    1: "http://127.0.0.1:5001",
    2: "http://127.0.0.1:5002"
}

def fetch_data(controller_id, endpoint):
    try:
        resp = requests.get(f"{CONTROLLERS[controller_id]}{endpoint}", timeout=1)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@app.route("/aircraft")
def get_aircraft():
    all_aircraft = []
    for cid in CONTROLLERS:
        data = fetch_data(cid, "/aircraft")
        if isinstance(data, list):
            all_aircraft.extend(data)
    return jsonify(all_aircraft)

@app.route("/nodes")
def get_nodes():
    merged_nodes = {}
    for cid in CONTROLLERS:
        data = fetch_data(cid, "/nodes")
        if isinstance(data, dict):
            merged_nodes.update(data)
    return jsonify(merged_nodes)

@app.route("/logs")
def get_logs():
    merged_logs = []
    for cid in CONTROLLERS:
        data = fetch_data(cid, "/logs")
        if isinstance(data, list):
            merged_logs.extend(data)
    return jsonify(merged_logs[-20:])

@app.route("/")
def radar_page():
    return send_from_directory(app.static_folder, "radar.html")

if __name__ == "__main__":
    app.run(port=8050, debug=True)
