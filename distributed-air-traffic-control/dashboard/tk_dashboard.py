import tkinter as tk
import requests
import threading, time

CONTROLLERS = {
    1: "http://127.0.0.1:5001",
    2: "http://127.0.0.1:5002"
}

root = tk.Tk()
root.title("ATC Tkinter Radar")

canvas = tk.Canvas(root, width=600, height=400, bg="black")
canvas.pack()

nodes_label = tk.Label(root, text="", justify="left", font=("Arial", 12), fg="white", bg="black")
nodes_label.pack(fill="x")

logs_label = tk.Label(root, text="", justify="left", font=("Arial", 10), fg="white", bg="black")
logs_label.pack(fill="x")

def fetch_aircraft():
    all_aircraft = []
    for cid, url in CONTROLLERS.items():
        try:
            resp = requests.get(url + "/aircraft", timeout=1)
            data = resp.json()
            all_aircraft.extend(data)
        except:
            pass
    return all_aircraft

def fetch_nodes():
    merged = {}
    for cid, url in CONTROLLERS.items():
        try:
            resp = requests.get(url + "/nodes", timeout=1)
            data = resp.json()
            merged.update(data)
        except:
            pass
    return merged

def fetch_logs():
    merged = []
    for cid, url in CONTROLLERS.items():
        try:
            resp = requests.get(url + "/logs", timeout=1)
            data = resp.json()
            merged.extend(data)
        except:
            pass
    return merged[-10:]

def update_gui():
    canvas.delete("all")

    # Draw aircraft + trails
    aircraft = fetch_aircraft()
    for a in aircraft:
        x, y = a["pos"]
        color = "blue" if a["controller"] == 1 else "red"
        # trail
        for tx, ty in a.get("trail", []):
            canvas.create_oval(tx, ty, tx+4, ty+4, fill=color)
        # current position
        canvas.create_oval(x, y, x+10, y+10, fill=color)
        canvas.create_text(x, y-15, text=a["id"], fill="white")

    # Draw controller nodes as fixed squares
    # Node 1 at top-left, Node 2 at top-right
    canvas.create_rectangle(40, 40, 70, 70, fill="blue")
    canvas.create_text(55, 30, text="Node 1", fill="white")
    canvas.create_rectangle(530, 40, 560, 70, fill="red")
    canvas.create_text(545, 30, text="Node 2", fill="white")

    # Update node states
    nodes = fetch_nodes()
    nodes_text = "\n".join([f"Node {nid}: {info}" for nid, info in nodes.items()])
    nodes_label.config(text=nodes_text)

    # Update logs
    logs = fetch_logs()
    logs_text = "\n".join([f"{log['event']} Node {log['node']} Aircraft {log['aircraft']}" for log in logs])
    logs_label.config(text=logs_text)

    root.after(1000, update_gui)

update_gui()
root.mainloop()
