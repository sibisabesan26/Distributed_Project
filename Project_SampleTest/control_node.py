import threading
import time
from lamport_clock import LamportClock
from message import Message

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
