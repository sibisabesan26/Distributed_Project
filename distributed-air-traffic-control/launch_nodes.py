import subprocess
import sys
import time

# Paths to your node controller files
nodes = [
    ("maincontroller1.py", 5001),
    ("maincontroller2.py", 5002),
    ("maincontroller3.py", 5003),
]

processes = []

try:
    for script, port in nodes:
        print(f"Starting {script} on port {port}...")
        # Launch each node as a separate process
        p = subprocess.Popen([sys.executable, script])
        processes.append(p)
        time.sleep(1)  # small delay so ports bind cleanly

    print("✅ All nodes launched. Press Ctrl+C to stop.")

    # Keep the launcher running until interrupted
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping all nodes...")
    for p in processes:
        p.terminate()
    print("✅ All nodes stopped.")
