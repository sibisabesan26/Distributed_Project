import threading, time

class HeartbeatManager:
    def __init__(self, peers, timeout=5):
        self.peers = peers  # list of peer URLs
        self.timeout = timeout
        self.last_seen = {p: time.time() for p in peers}

    def beat(self, peer):
        self.last_seen[peer] = time.time()

    def monitor(self, on_failure):
        def loop():
            while True:
                now = time.time()
                for p, last in self.last_seen.items():
                    if now - last > self.timeout:
                        on_failure(p)
                time.sleep(1)
        threading.Thread(target=loop, daemon=True).start()
