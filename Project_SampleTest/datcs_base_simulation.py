import threading
import time
from queue import Queue

# Lamport Clock
class LamportClock:
    def __init__(self):
        self.time = 0

    def tick(self):
        self.time += 1

    def update(self, received_time):
        self.time = max(self.time, received_time) + 1

    def get_time(self):
        return self.time

# Message structure
class Message:
    def __init__(self, sender, content, timestamp):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.acks = set()

# Message Broker for multicast
class MessageBroker:
    def __init__(self):
        self.queues = {}

    def register_node(self, node_id):
        self.queues[node_id] = Queue()

    def multicast(self, sender_id, message):
        for node_id, q in self.queues.items():
            q.put((sender_id, message))

    def receive(self, node_id):
        try:
            return self.queues[node_id].get(timeout=1)
        except:
            return None

# Control Node
class ControlNode(threading.Thread):
    def __init__(self, node_id, broker, all_nodes):
        super().__init__()
        self.node_id = node_id
        self.broker = broker
        self.clock = LamportClock()
        self.all_nodes = all_nodes
        self.queue = []
        self.alive = True
        self.running = True

    def run(self):
        while self.running:
            if self.alive:
                msg_data = self.broker.receive(self.node_id)
                if msg_data:
                    sender, msg = msg_data
                    self.clock.update(msg.timestamp)
                    msg.acks.add(self.node_id)
                    self.queue.append(msg)
                    self.check_delivery()
            else:
                time.sleep(1)

    def send(self, content):
        self.clock.tick()
        msg = Message(self.node_id, content, self.clock.get_time())
        self.broker.multicast(self.node_id, msg)

    def check_delivery(self):
        for msg in list(self.queue):
            if len(msg.acks) == len(self.all_nodes):
                print(f"[{self.node_id}] Delivered: {msg.content} @ {msg.timestamp}")
                self.queue.remove(msg)

    def fail(self):
        print(f"[{self.node_id}] Simulating failure...")
        self.alive = False

    def recover(self):
        print(f"[{self.node_id}] Recovering node...")
        self.alive = True

    def stop(self):
        self.running = False
# Aircraft simulation
class Aircraft:
    def __init__(self, aircraft_id):
        self.id = aircraft_id
        self.position = 0

    def move(self):
        self.position += 1
        return f"Aircraft {self.id} at position {self.position}"

# Heartbeat monitor
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

            time.sleep(5)

# Main simulation
if __name__ == "__main__":
    broker = MessageBroker()
    node_ids = ["Zone-A", "Zone-B", "Zone-C"]
    nodes = [ControlNode(node_id, broker, node_ids) for node_id in node_ids]

    for node in nodes:
        broker.register_node(node.node_id)
        node.start()

    aircraft = Aircraft("AC101")
    for _ in range(5):
        status = aircraft.move()
        nodes[0].send(status)
        time.sleep(2)

    monitor = HeartbeatMonitor(nodes)
    monitor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        for node in nodes:
            node.stop()
