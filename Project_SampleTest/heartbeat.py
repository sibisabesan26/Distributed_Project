import threading
import time

class HeartbeatMonitor(threading.Thread):
    def __init__(self, nodes):
        super().__init__()
        self.nodes = nodes
        self.start_time = time.time()
        self.failure_triggered = False
        self.recovery_triggered = False

    def run(self):
        while True:
            for node in self.nodes:
                status = "alive" if node.alive else "dead"
                print(f"[Heartbeat] {node.node_id} is {status}")

            elapsed = time.time() - self.start_time

            # Simulate failure of Zone-B after 10 seconds
            if not self.failure_triggered and elapsed > 10:
                for node in self.nodes:
                    if node.node_id == "Zone-B":
                        node.fail()
                        self.failure_triggered = True

            # Recover Zone-B after 20 seconds
            if self.failure_triggered and not self.recovery_triggered and elapsed > 20:
                for node in self.nodes:
                    if node.node_id == "Zone-B":
                        node.recover()
                        self.recovery_triggered = True

            time.sleep(1)
