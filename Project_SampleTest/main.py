from broker import MessageBroker
from control_node import ControlNode
from aircraft import Aircraft
from heartbeat import HeartbeatMonitor
import time

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
        time.sleep(0.5)

    monitor = HeartbeatMonitor(nodes)
    monitor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        for node in nodes:
            node.stop()
