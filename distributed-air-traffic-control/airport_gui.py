import tkinter as tk
import requests
import json
import datetime
from PIL import Image, ImageTk
import random

# Track per-aircraft state (e.g., whether it has been in CS)
aircraft_state = {}  # { aircraft_id: {"in_cs": False} }

# -----------------------------
# Load node registry dynamically
# -----------------------------
with open("nodes.json", "r") as f:
    NODE_REGISTRY = json.load(f)

root = tk.Tk()
root.title("Airport Simulation")

# Speed multiplier variable (must be created after root)
speed_multiplier = tk.DoubleVar(value=1.0)

# Speed slider UI
speed_frame = tk.Frame(root, bg="black")
speed_frame.pack(fill="x")

tk.Label(speed_frame, text="Speed:", font=("Arial", 10), fg="white", bg="black").pack(side="left", padx=10)
tk.Scale(speed_frame, from_=0.5, to=3.0, resolution=0.1, orient="horizontal",
         variable=speed_multiplier, length=200, bg="black", fg="white").pack(side="left")

# -----------------------------
# Background image
# -----------------------------
bg_image = Image.open("images/airport_map.png")   # adjust path if needed
bg_image = bg_image.resize((800, 500))
bg_photo = ImageTk.PhotoImage(bg_image)

canvas = tk.Canvas(root, width=800, height=500)
canvas.pack()
canvas.bg_photo = bg_photo  # prevent garbage collection
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

tk.Label(speed_frame, text="Speed:", font=("Arial", 10), fg="white", bg="black").pack(side="left", padx=10)
tk.Scale(speed_frame, from_=0.5, to=3.0, resolution=0.1, orient="horizontal",
         variable=speed_multiplier, length=200, bg="black", fg="white").pack(side="left")

# -----------------------------
# Status bar
# -----------------------------
status_text = tk.StringVar()
status_label = tk.Label(root, textvariable=status_text, font=("Arial", 12), fg="white", bg="black")
status_label.pack(fill="x")

# -----------------------------
# Log + Queue frame
# -----------------------------
log_frame = tk.Frame(root, bg="black")
log_frame.pack(fill="both", expand=True)

queue_label = tk.Label(log_frame, text="Runway Queue:", font=("Arial", 12, "bold"), fg="yellow", bg="black")
queue_label.pack(anchor="w")

queue_text = tk.StringVar()
queue_display = tk.Label(log_frame, textvariable=queue_text, font=("Arial", 12), fg="white", bg="black")
queue_display.pack(anchor="w")

log_label = tk.Label(log_frame, text="Event Log:", font=("Arial", 12, "bold"), fg="cyan", bg="black")
log_label.pack(anchor="w")

log_listbox = tk.Listbox(log_frame, height=10, width=100, bg="black", fg="white", font=("Courier", 10))
log_listbox.pack(fill="both", expand=True)

# -----------------------------
# Visual settings
# -----------------------------
tower_colors = {"IDLE": "green", "REQUESTING": "yellow", "CRITICAL_SECTION": "orange"}
aircraft_positions = {}
flash_state = {"on": True}
current_aircraft = []

# -----------------------------
# Drawing functions
# -----------------------------
def draw_scene(nodes, aircraft):
    canvas.delete("all")
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")  # redraw background

    # Runway overlay
    canvas.create_rectangle(300, 200, 500, 300, outline="white", width=3)
    canvas.create_text(400, 250, text="RWY_A", fill="white", font=("Arial", 14, "bold"))

    # Single Control Tower on the right side
    tower_x, tower_y = 650, 50   # moved to the right side
    tower_width, tower_height = 120, 200
    canvas.create_rectangle(tower_x, tower_y, tower_x+tower_width, tower_y+tower_height,
                            fill="gray", outline="white", width=2)
    canvas.create_text(tower_x + tower_width/2, tower_y - 15,
                       text="Control Tower", fill="white", font=("Arial", 12, "bold"))

    # Divide tower vertically into sections for each node
    node_count = len(nodes)
    section_height = tower_height / max(1, node_count)
    for idx, (node_id, node_state) in enumerate(nodes.items()):
        y1 = tower_y + idx * section_height
        y2 = y1 + section_height
        canvas.create_rectangle(tower_x, y1, tower_x+tower_width, y2,
                                fill=tower_colors.get(node_state.get("state", "IDLE"), "gray"),
                                outline="black")
        canvas.create_text(tower_x + tower_width/2, (y1+y2)/2,
                           text=f"Node {node_id}", fill="white", font=("Arial", 10, "bold"))

    # Aircraft
    for a in aircraft:
        if a["id"] not in aircraft_positions:
            # Spawn all aircraft on the left side, different vertical offsets
            base_y = 400 if a["controller"] == 1 else 300
            aircraft_positions[a["id"]] = [50, base_y]
        pos = aircraft_positions[a["id"]]
        # Color mapping for each node controller
        color_map = {
            1: "blue",     # Node 1 aircraft
            2: "red",      # Node 2 aircraft
            3: "purple"    # Node 3 aircraft
        }

        # Use mapping with fallback
        color = color_map.get(a["controller"], "gray")


        # Draw aircraft as ✈ symbol
        canvas.create_text(pos[0], pos[1], text="✈", font=("Arial", 20, "bold"), fill=color)
        canvas.create_text(pos[0], pos[1]-25, text=a["id"], fill=color, font=("Arial", 10, "bold"))

    # Runway Busy Indicator
    busy = any(node_state.get("state") == "CRITICAL_SECTION" for node_state in nodes.values())
    if busy and flash_state["on"]:
        canvas.create_text(400, 180, text="RUNWAY OCCUPIED", fill="red", font=("Arial", 16, "bold"))
    flash_state["on"] = not flash_state["on"]


def inside_cs(pos):
    # Critical section rectangle (runway area)
    cs_x1, cs_y1, cs_x2, cs_y2 = 300, 200, 500, 300
    return cs_x1 <= pos[0] <= cs_x2 and cs_y1 <= pos[1] <= cs_y2


def animate_aircraft(nodes):
    for a_id, pos in aircraft_positions.items():
        # Find controller for this aircraft
        controller = None
        for a in current_aircraft:
            if a["id"] == a_id:
                controller = a["controller"]
                break
        if controller is None:
            continue

        node_state = nodes.get(str(controller), {}).get("state")

        # Runway center target
        target_x, target_y = 400, 250
        dx = target_x - pos[0]
        dy = target_y - pos[1]
        mult = speed_multiplier.get()
        step_x = mult * (5 if dx > 0 else -5 if dx < 0 else 0)
        step_y = mult * (3 if dy > 0 else -3 if dy < 0 else 0)

        # Move aircraft only while in CS
        if node_state == "CRITICAL_SECTION":
            pos[0] += step_x
            pos[1] += step_y

            # ✅ Reset once aircraft reaches runway center
            if abs(pos[0] - target_x) <= 5 and abs(pos[1] - target_y) <= 5:
                # Reset aircraft back to left side
                aircraft_positions[a_id] = [50, random.randint(50, 450)]
                # Release CS so next node can go
                try:
                    requests.get(f"{NODE_REGISTRY[str(controller)]}/release")
                except Exception as e:
                    print(f"[ERROR releasing CS for Node {controller}]: {e}")
# -----------------------------
# Update loop
# -----------------------------
def update():
    global current_aircraft
    try:
        nodes = {}
        aircraft = []
        logs = []

        for node_id, base_url in NODE_REGISTRY.items():
            try:
                n = requests.get(f"{base_url}/nodes").json()
                nodes[node_id] = n.get(int(node_id), n.get(node_id, {}))
                aircraft += requests.get(f"{base_url}/aircraft").json()
                logs += requests.get(f"{base_url}/logs").json()
            except Exception:
                nodes[node_id] = {"state": "DOWN"}

        current_aircraft = aircraft
        animate_aircraft(nodes)
        draw_scene(nodes, aircraft)

        # Update queue display
        try:
            with open("runway_queue.txt", "r") as f:
                queue = f.read().strip()
        except:
            queue = "[]"
        queue_text.set(queue)

        # Update log listbox with readable times
        log_listbox.delete(0, tk.END)
        for entry in logs[-10:]:  # show last 10 events
            ts = datetime.datetime.fromtimestamp(entry['time']).strftime("%H:%M:%S")
            log_listbox.insert(tk.END, f"{ts} | Node {entry['node']} | {entry['event']} | {entry['aircraft']}")

        status_text.set(f"Nodes: {nodes}")
    except Exception as e:
        status_text.set(f"Error: {e}")

    root.after(500, update)

update()
root.mainloop()
