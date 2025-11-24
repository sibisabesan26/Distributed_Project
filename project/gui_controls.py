import tkinter as tk

def build_controls(root, node_count, speed_multiplier):
    """
    Build control panel with node count selector and speed multiplier slider.
    """

    frame = tk.Frame(root, bg="gray20")
    frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Node count selector
    tk.Label(frame, text="Nodes:", fg="white", bg="gray20").pack(side=tk.LEFT, padx=5)
    node_spin = tk.Spinbox(frame, from_=1, to=3, textvariable=node_count, width=5)
    node_spin.pack(side=tk.LEFT, padx=5)

    # Speed multiplier slider
    tk.Label(frame, text="Speed:", fg="white", bg="gray20").pack(side=tk.LEFT, padx=5)
    speed_slider = tk.Scale(frame, from_=0.5, to=3.0, resolution=0.1,
                            orient=tk.HORIZONTAL, variable=speed_multiplier,
                            length=150, bg="gray20", fg="white")
    speed_slider.pack(side=tk.LEFT, padx=5)

    # Quit button
    quit_btn = tk.Button(frame, text="Quit", command=root.destroy, bg="red", fg="white")
    quit_btn.pack(side=tk.RIGHT, padx=10)
