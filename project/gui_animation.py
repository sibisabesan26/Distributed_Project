def animate_aircraft(nodes, aircraft_positions, aircraft_list, speed_multiplier):
    """
    Animate aircraft on the canvas.
    - nodes: dict of node states
    - aircraft_positions: dict mapping aircraft IDs to canvas object IDs
    - aircraft_list: list of aircraft dicts from controllers
    - speed_multiplier: Tkinter DoubleVar controlling animation speed
    """

    speed = speed_multiplier.get()

    for a in aircraft_list:
        obj_id = aircraft_positions.get(a["id"])
        if not obj_id:
            continue

        # Current position
        x, y = a["pos"]

        # If node is in CS, move toward runway center
        if nodes.get(a["controller"], {}).get("state") == "CRITICAL_SECTION":
            target_x, target_y = 400, 300
            dx = target_x - x
            dy = target_y - y

            step_x = (5 * speed) if dx > 0 else (-5 * speed) if dx < 0 else 0
            step_y = (3 * speed) if dy > 0 else (-3 * speed) if dy < 0 else 0

            new_x = x + step_x
            new_y = y + step_y
        else:
            # Idle drift (slow horizontal movement)
            new_x = (x + 1 * speed) % 800
            new_y = y

        # Update canvas position
        dx_canvas = new_x - x
        dy_canvas = new_y - y
        canvas = aircraft_positions.get("canvas")
        if canvas:
            canvas.move(obj_id, dx_canvas, dy_canvas)

        # Update aircraft dict position
        a["pos"][0] = new_x
        a["pos"][1] = new_y
