import time
import threading

# -----------------------------
# Network Adapter
# -----------------------------
class NetworkAdapter:
    """
    Stubbed network adapter for sending messages between controllers.
    Replace send_* methods with actual multicast or HTTP calls.
    """
    def __init__(self, send_request, send_reply, send_release):
        self.send_request = send_request
        self.send_reply = send_reply
        self.send_release = send_release

# -----------------------------
# Snapshot Manager
# -----------------------------
class SnapshotManager:
    """
    Implements Chandy-Lamport snapshot logic.
    Each controller can initiate a snapshot and record local + channel state.
    """
    def __init__(self, controller_id, peers, send_marker, emit_snapshot, get_local_state):
        self.controller_id = controller_id
        self.peers = peers
        self.send_marker = send_marker
        self.emit_snapshot = emit_snapshot
        self.get_local_state = get_local_state
        self.active_snapshots = {}
        self.lock = threading.Lock()

    def start_snapshot(self, snapshot_id):
        with self.lock:
            if snapshot_id in self.active_snapshots:
                return
            # Record local state
            local_state = self.get_local_state()
            self.active_snapshots[snapshot_id] = {
                "local_state": local_state,
                "channel_state": {peer: [] for peer in self.peers},
                "markers_received": set()
            }
            # Send markers to peers
            for peer in self.peers:
                self.send_marker(peer, snapshot_id)
            # Emit snapshot immediately for demo purposes
            self.emit_snapshot(snapshot_id, self.active_snapshots[snapshot_id])

    def receive_marker(self, from_peer, snapshot_id):
        with self.lock:
            snap = self.active_snapshots.get(snapshot_id)
            if not snap:
                # If marker arrives before local snapshot started
                self.start_snapshot(snapshot_id)
                snap = self.active_snapshots[snapshot_id]
            snap["markers_received"].add(from_peer)
            # If all markers received, finalize snapshot
            if snap["markers_received"] == set(self.peers):
                self.emit_snapshot(snapshot_id, snap)

    def record_message(self, from_peer, snapshot_id, message):
        with self.lock:
            snap = self.active_snapshots.get(snapshot_id)
            if snap and from_peer in snap["channel_state"]:
                snap["channel_state"][from_peer].append(message)

# -----------------------------
# Message Logger
# -----------------------------
class MessageLogger:
    """
    Simple in-memory log for events/messages.
    """
    def __init__(self, max_len=50):
        self.log = []
        self.max_len = max_len

    def add(self, event, node, aircraft):
        entry = {"event": event, "node": node, "aircraft": aircraft, "time": time.time()}
        self.log.append(entry)
        if len(self.log) > self.max_len:
            self.log.pop(0)

    def get(self):
        return list(self.log)
