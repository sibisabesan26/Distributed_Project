# Distributed Air Traffic Control Simulation (Tkinter GUI)

This project is a **bird’s‑eye view airport simulation** built with Python’s Tkinter.  
It visualizes a runway, aircraft nodes, and a control tower with blinking lights, while also maintaining a **scrollable message log** of communications between the coordinator and controllers.

---

## ✈ Features

- **Runway visualization**  
  - Asphalt background, threshold bars, centerline markings, and edge lights.
  - Labelled runway (`RWY_A`) drawn in the canvas.

- **Aircraft nodes**  
  - Each node is assigned a distinct color (red, blue, purple, orange).
  - Aircraft symbols (`✈`) are drawn at their positions with labels above them.

- **Tower light**  
  - Blinks in the color of the active node when in the critical section.
  - Blinks black with an “Idle” label when no node is active.

- **Animated background (GIF)**  
  - A looping GIF provides a cartoonish/professional airport backdrop.
  - Frames are cycled using `after()` for smooth animation.

- **Message log**  
  - Scrollable text box below the canvas.
  - Logs coordinator ↔ node communications (e.g., grants, releases, idle states).
  - Auto‑scrolls to the latest entry.

---

## 🛠 Requirements

- Python 3.9+  
- Tkinter (bundled with Python)  
- Pillow (`pip install pillow`) for GIF frame handling

---

## 🚀 Running the Simulation

1. Clone or download this repository.
2. Place your background GIF in the project folder and name it `background.gif`.
3. Run the GUI:

   ```bash
   python gui_main.py
