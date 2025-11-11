from queue import Queue

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
            return self.queues[node_id].get(timeout=0.1)
        except:
            return None
