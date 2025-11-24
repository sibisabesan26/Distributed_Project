import subprocess
import time
import sys

# Paths to your scripts
COORDINATOR = "coordinator.py"
NODE1 = "main_controller1.py"
NODE2 = "main_controller2.py"
NODE3 = "main_controller3.py"

processes = []

def launch(script, label):
    try:
        p = subprocess.Popen([sys.executable, script])
        processes.append(p)
        print(f"[Launcher] Started {label} ({script})")
    except Exception as e:
        print(f"[Launcher] Error starting {label}: {e}")

def main():
    print("[Launcher] Starting distributed air traffic control demo...")

    # Start coordinator first
    launch(COORDINATOR, "Coordinator")
    time.sleep(1)  # small delay so coordinator is ready

    # Start controllers
    launch(NODE1, "Controller 1")
    launch(NODE2, "Controller 2")
    launch(NODE3, "Controller 3")

    print("[Launcher] All processes started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Launcher] Stopping all processes...")
        for p in processes:
            p.terminate()
        print("[Launcher] Done.")

if __name__ == "__main__":
    main()
