from tkinter import *
import threading
from gui_update import start_update_loop
import tkinter as tk
from tkinter import scrolledtext   # <-- this line is missing

from PIL import Image, ImageTk   # <-- this is the correct import
from gui_canvas import draw_scene

# Canvas size
WIDTH, HEIGHT = 600, 500

def main():
    root = Tk()
    root.title("Distributed Air Traffic Control")

    # --- Canvas for simulation ---
    canvas_frame = tk.Frame(root)
    canvas_frame.pack(side="top", fill="x")

    # Create canvas
    canvas = Canvas(root, width=800, height=600)
    canvas.pack()

    # --- Load background image once ---
    bg_image = Image.open("background.png")   # replace with your file
    bg_image = bg_image.resize((800, 600))
    bg_photo = ImageTk.PhotoImage(bg_image)

    # Draw background image (tag it as "background")
    canvas.create_image(0, 0, image=bg_photo, anchor="nw", tags="background")

    # Keep reference so it's not garbage-collected
    canvas.bg_photo = bg_photo

    # --- Tower image ---
    tower_image = Image.open("tower.png").resize((100, 150))   # adjust size
    tower_photo = ImageTk.PhotoImage(tower_image)

    # Place tower on top (e.g., near runway)
    canvas.create_image(700, 200, image=tower_photo, anchor="nw")
    canvas.create_text(750, 370, text="Tower", font=("Arial", 14, "bold"), fill="black")

    # Keep reference
    canvas.tower_photo = tower_photo

    # --- Message Log below ---
    log_frame = tk.Frame(root)
    log_frame.pack(side="bottom", fill="both", expand=True)

    log_widget = scrolledtext.ScrolledText(
        log_frame,
        wrap=tk.WORD,
        height=10,
        font=("Consolas", 10)
    )
    log_widget.pack(fill="both", expand=True)

    # Keep reference for later appends
    root.log_widget = log_widget

    # Global speed factor
    speed = 1.0

    def update_speed(val):
        global speed
        speed = float(val)
        print(f"[GUI] Simulation speed set to {speed}x")

    # Create slider ONCE here
    speed_slider = tk.Scale(root,
                            from_=0.5, to=5.0,
                            resolution=0.1,
                            orient="horizontal",
                            label="Simulation Speed",
                            command=update_speed)
    speed_slider.set(1.0)
    speed_slider.pack(pady=10)
    
    # Parameters
    node_count = 3
    speed_multiplier = 1.0
    aircraft_positions = {}

    # Start update loop in background thread
    threading.Thread(
        target=start_update_loop,
        args=(root, canvas, node_count, speed_multiplier, aircraft_positions),
        daemon=True
    ).start()

    root.mainloop()

def log_message(root, sender, receiver, content):
    entry = f"[{sender} → {receiver}] {content}\n"
    root.log_widget.insert(tk.END, entry)
    root.log_widget.see(tk.END)  # auto-scroll to latest


if __name__ == "__main__":
    main()
