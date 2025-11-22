import threading
import heapq
import time

class LamportMulticast:
    def __init__(self, controller_id, peers):
        self.controller_id = controller_id
        self.peers = peers  # list of peer controller IDs
        self.clock = 0
        self.queue = []  # priority queue of (timestamp, sender_id, message)
        self.acks = {}   # message_id → set of ACKs received
        self.delivered = set()
        self.lock = threading.Lock()

    def increment_clock(self):
        self.clock += 1
        return self.clock

    def receive_message(self, msg):
        with self.lock:
            self.clock = max(self.clock, msg["timestamp"]) + 1
            msg_id = (msg["timestamp"], msg["sender_id"])
            heapq.heappush(self.queue, (msg["timestamp"], msg["sender_id"], msg["content"]))
            self.acks.setdefault(msg_id, set()).add(msg["sender_id"])
            self.try_deliver()

    def receive_ack(self, msg_id, sender_id):
        with self.lock:
            self.acks.setdefault(msg_id, set()).add(sender_id)
            self.try_deliver()

    def multicast(self, content):
        ts = self.increment_clock()
        msg_id = (ts, self.controller_id)
        message = {
            "timestamp": ts,
            "sender_id": self.controller_id,
            "content": content
        }
        with self.lock:
            heapq.heappush(self.queue, (ts, self.controller_id, content))
            self.acks[msg_id] = {self.controller_id}
        self.broadcast_message(message)

    def broadcast_message(self, message):
        # Replace this with actual network send logic
        print(f"[{self.controller_id}] Broadcasting: {message}")
        for peer in self.peers:
            # Simulate network send
            threading.Thread(target=self.simulate_receive, args=(peer, message)).start()

    def simulate_receive(self, peer_id, message):
        # Simulate delay and ACK
        time.sleep(0.1)
        print(f"[{peer_id}] Received: {message}")
        self.receive_message(message)
        self.receive_ack((message["timestamp"], message["sender_id"]), peer_id)

    def try_deliver(self):
        while self.queue:
            ts, sender_id, content = self.queue[0]
            msg_id = (ts, sender_id)
            if msg_id in self.delivered:
                heapq.heappop(self.queue)
                continue
            if self.acks.get(msg_id) and self.acks[msg_id] >= set(self.peers + [self.controller_id]):
                print(f"[{self.controller_id}] Delivered: {content}")
                self.delivered.add(msg_id)
                heapq.heappop(self.queue)
            else:
                break
