import subprocess
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

services = [
    ("Controller 1", ["python", os.path.join(BASE_DIR, "main_controller1.py")]),
    ("Controller 2", ["python", os.path.join(BASE_DIR, "main_controller2.py")]),
    ("Dashboard",    ["python", os.path.join(BASE_DIR, "dashboard.py")]),
]

processes = []

try:
    for name, cmd in services:
        print(f"Starting {name}...")
        p = subprocess.Popen(cmd)
        processes.append(p)
        time.sleep(1)  # small stagger so ports bind cleanly

    print("✅ All services started. Controller1=5001, Controller2=5002, Dashboard=8050")

    while True:
        time.sleep(5)

except KeyboardInterrupt:
    print("\nStopping all services...")
    for p in processes:
        p.terminate()
    print("All stopped.")
