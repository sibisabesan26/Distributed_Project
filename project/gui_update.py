import requests
import time
from gui_canvas import draw_scene

def start_update_loop(root, canvas, node_count, speed_multiplier, aircraft_positions):
    def update():
        nodes = {}
        current_aircraft = {}

        # Collect node states
        for i in range(1, node_count + 1):
            try:
                r = requests.get(f"http://127.0.0.1:{5000+i}/nodes", timeout=2)
                data = r.json()
                nodes.update(data)
            except Exception as e:
                print(f"[GUI] Error fetching node {i} state:", e)

            try:
                r = requests.get(f"http://127.0.0.1:{5000+i}/aircraft", timeout=2)
                data = r.json()
                aircraft_positions[i] = data
            except Exception as e:
                print(f"[GUI] Error fetching aircraft from node {i}:", e)

        # Poll coordinator for active/queued info
        try:
            r = requests.get("http://127.0.0.1:6000/status", timeout=2)
            data = r.json()
            current_aircraft["token_holder"] = data.get("token_holder")
            current_aircraft["queue"] = data.get("queue", [])
        except Exception as e:
            print("[GUI] Error fetching coordinator status:", e)

        # Draw everything
        draw_scene(nodes, canvas, aircraft_positions, current_aircraft)

        # Schedule next update
        root.after(int(1000 / speed_multiplier), update)

    # Kick off the loop
    update()
