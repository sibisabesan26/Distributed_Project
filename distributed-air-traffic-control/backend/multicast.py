import socket
import threading
import json

class MulticastManager:
    def __init__(self, group_addr="224.1.1.1", port=5007):
        self.group_addr = group_addr
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", port))
        mreq = socket.inet_aton(group_addr) + socket.inet_aton("0.0.0.0")
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def send(self, message):
        data = json.dumps(message).encode("utf-8")
        self.sock.sendto(data, (self.group_addr, self.port))

    def listen(self, handler):
        def loop():
            while True:
                data, _ = self.sock.recvfrom(1024)
                msg = json.loads(data.decode("utf-8"))
                handler(msg)
        threading.Thread(target=loop, daemon=True).start()
