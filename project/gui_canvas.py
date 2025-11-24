from tkinter import *

def draw_scene(nodes, canvas, aircraft_positions, current_aircraft):
    # Clear canvas
    canvas.delete("overlay")

# Global toggle for blinking
blink_state = True

def draw_scene(nodes, canvas, aircraft_positions, current_aircraft):
    global blink_state
    canvas.delete("overlay")
    # Draw runway (simple rectangle)

    canvas.create_rectangle(150, 250, 650, 350, fill="dim gray", outline="white", tags="overlay")


    # Threshold markings (white bars at each end)
    for x in [150, 630]:
        canvas.create_rectangle(x, 250, x+20, 350, fill="white", outline="white", tags="overlay")

    # Centerline markings (dashed white line down the middle)
    for cx in range(180, 630, 60):
        canvas.create_rectangle(cx, 295, cx+30, 305, fill="white", outline="white", tags="overlay")

    # Runway label above
    canvas.create_text(400, 230, text="RWY_A", fill="white", font=("Arial", 16, "bold"), tags="overlay")

    # Optional: edge lights (blue dots along sides)
    for lx in range(160, 640, 40):
        canvas.create_oval(lx, 245, lx+5, 250, fill="blue", outline="blue", tags="overlay")   # top edge
        canvas.create_oval(lx, 350, lx+5, 355, fill="blue", outline="blue", tags="overlay")   # bottom edge

    # Draw aircraft with labels and different colors
    colors = ["red", "blue", "purple", "orange"]  # cycle through colors
    node_colors = {}  # map node_id -> color

    for idx, (node_id, aircraft_list) in enumerate(aircraft_positions.items()):
        for a in aircraft_list:
            x, y = a["pos"]
            color = colors[idx % len(colors)]  # pick a color based on node index
            node_colors[node_id] = color
            # Draw plane symbol
            canvas.create_text(
                x, y,
                text="✈",
                font=("Arial", 20),
                fill=color, tags="overlay"
            )

            # Add label (node ID or aircraft ID) just above the plane
            label = f"Node {node_id}"
            canvas.create_text(
                x, y - 25,
                text=label,
                font=("Arial", 12, "bold"),
                fill=color, tags="overlay"
            )

        # --- Status text ---
    active_nodes = [nid for nid, info in nodes.items()
                    if info["state"] == "CRITICAL_SECTION"]
    status_text = f"Active: {', '.join(map(str, active_nodes))}"
    queued = current_aircraft.get("queue", [])
    if queued:
        status_text += f" | Queued: {', '.join(map(str, queued))}"
    canvas.create_text(300, 20, text=status_text,
                       font=("Arial", 14), fill="black", tags="overlay")

    # --- Tower label + active node underneath ---
    canvas.create_text(750, 370, text="Tower",
                       font=("Arial", 14, "bold"), fill="black", tags="overlay")

    if active_nodes:
        active_node = active_nodes[0]  # show the first active node
        color = node_colors.get(active_node, "black")
        canvas.create_text(750, 390, text=f"Node {active_node}",
                           font=("Arial", 12, "bold"), fill=color, tags="overlay")
    # --- Tower blinking light ---
    if active_nodes:
        active_node = active_nodes[0]
        color = node_colors.get(active_node, "black")

        # Toggle blink state
        if blink_state:
            canvas.create_oval(740, 200, 760, 210,
                               fill=color, outline=color, tags="overlay")
        # Flip state for next frame
        blink_state = not blink_state

    # Schedule next blink update
    canvas.after(500, lambda: draw_scene(nodes, canvas, aircraft_positions, current_aircraft))

    # Highlight active nodes
    active_nodes = [nid for nid, info in nodes.items() if info["state"] == "CRITICAL_SECTION"]
    status_text = f"Active: {', '.join(map(str, active_nodes))}"

    # Show queued nodes (from coordinator status if passed in current_aircraft)
    queued = current_aircraft.get("queue", [])
    if queued:
        status_text += f" | Queued: {', '.join(map(str, queued))}"

    # Draw status text at top
    canvas.create_text(
        300, 20,
        text=status_text,
        font=("Arial", 14),
        fill="black", tags="overlay"
    )
