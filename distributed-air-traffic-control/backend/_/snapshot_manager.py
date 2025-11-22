import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Callable, Optional, Any

# -----------------------------------------------------------------------------
# Chandy–Lamport Snapshot Manager
# -----------------------------------------------------------------------------
# Assumptions:
# - Each controller has directed communication channels to peers.
# - You can send/receive MARKER messages out-of-band via your network layer.
# - The manager is notified on every local send/receive (data messages) so it
#   can record per-channel in-flight messages between local-state record and
#   MARKER arrival on that channel.
#
# Integration points you must provide:
# - send_marker(to_id: int, snapshot_id: str) -> None
# - emit_snapshot(snapshot_id: str, payload: dict) -> None (collector callback)
# - get_local_state() -> dict   (reads your controller's current state)
#
# Usage:
#   sm = SnapshotManager(controller_id=1, peers=[2,3], send_marker=..., emit_snapshot=..., get_local_state=...)
#   sm.start_snapshot(snapshot_id="snap-001")  # initiator
#   ...
#   # On network receive:
#   if msg.type == "MARKER":
#       sm.handle_marker(snapshot_id=msg.snapshot_id, from_id=msg.from_id)
#   else:
#       sm.on_receive(from_id=msg.from_id, message=msg.payload)
#
#   # On network send:
#   sm.on_send(to_id=peer_id, message=payload)
# -----------------------------------------------------------------------------

@dataclass
class ChannelRecord:
    # Whether we've received the first MARKER on this inbound channel
    marker_received: bool = False
    # Messages recorded on this channel after local state capture and before MARKER arrival
    in_flight_messages: List[Any] = field(default_factory=list)


@dataclass
class SnapshotState:
    # Whether local state is recorded
    local_recorded: bool = False
    # Local state at the time of snapshot
    local_state: Dict[str, Any] = field(default_factory=dict)
    # Per inbound channel recording
    inbound_channels: Dict[int, ChannelRecord] = field(default_factory=dict)
    # Completion flag
    complete: bool = False
    # Timestamp for metadata
    started_at: float = field(default_factory=time.time)
    # Who initiated the snapshot
    initiator_id: Optional[int] = None


class SnapshotManager:
    def __init__(self,
                 controller_id: int,
                 peers: List[int],
                 send_marker: Callable[[int, str], None],
                 emit_snapshot: Callable[[str, Dict[str, Any]], None],
                 get_local_state: Callable[[], Dict[str, Any]]):
        """
        Args:
            controller_id: This node's ID.
            peers: List of peer IDs (inbound/outbound channels defined by membership).
            send_marker: Function to send MARKER(to_id, snapshot_id).
            emit_snapshot: Callback to emit the finalized snapshot payload.
            get_local_state: Function returning the node's local state dict.
        """
        self.controller_id = controller_id
        self._peers = set(peers)
        self._send_marker = send_marker
        self._emit_snapshot = emit_snapshot
        self._get_local_state = get_local_state

        self._lock = threading.RLock()
        # Active snapshots keyed by snapshot_id
        self._snapshots: Dict[str, SnapshotState] = {}

    # -------------------------------------------------------------------------
    # Membership updates (optional)
    # -------------------------------------------------------------------------
    def set_membership(self, peers: List[int]) -> None:
        with self._lock:
            self._peers = set(peers)
            # Ensure any active snapshot tracks inbound channels for current peers
            for snap in self._snapshots.values():
                for p in self._peers:
                    snap.inbound_channels.setdefault(p, ChannelRecord())

    # -------------------------------------------------------------------------
    # Initiating a snapshot (local node is the initiator)
    # -------------------------------------------------------------------------
    def start_snapshot(self, snapshot_id: str) -> None:
        """
        Start a Chandy–Lamport snapshot from this controller.
        Records local state and sends MARKER to all peers.
        """
        with self._lock:
            if snapshot_id in self._snapshots and self._snapshots[snapshot_id].local_recorded:
                # Already initiated locally
                return

            st = self._snapshots.setdefault(snapshot_id, SnapshotState())
            st.initiator_id = self.controller_id

            # 1) Record local state
            st.local_state = self._safe_get_local_state()
            st.local_recorded = True

            # 2) Initialize inbound channel recording
            st.inbound_channels = {peer: ChannelRecord(marker_received=False) for peer in self._peers}

            # 3) Send MARKER on all outbound channels
            for peer in self._peers:
                try:
                    self._send_marker(peer, snapshot_id)
                except Exception as e:
                    # Non-fatal: snapshot continues; mark channel and proceed
                    # You may want to log this error in your system logs
                    pass

            # If we have no peers, we can finalize immediately
            if not self._peers:
                self._finalize(snapshot_id)

    # -------------------------------------------------------------------------
    # Handling incoming MARKER messages
    # -------------------------------------------------------------------------
    def handle_marker(self, snapshot_id: str, from_id: int) -> None:
        """
        Handle MARKER received from peer 'from_id' for 'snapshot_id'.
        If first MARKER for this snapshot locally, record local state.
        For the inbound channel from 'from_id', stop recording and mark marker_received=True.
        When all inbound channels have received MARKER, finalize.
        """
        with self._lock:
            st = self._snapshots.setdefault(snapshot_id, SnapshotState())

            # First time we see MARKER for this snapshot?
            if not st.local_recorded:
                # Record local state
                st.local_state = self._safe_get_local_state()
                st.local_recorded = True
                # Initialize inbound channel recording
                st.inbound_channels = {peer: ChannelRecord(marker_received=False) for peer in self._peers}
                # Send MARKER on all outbound channels
                for peer in self._peers:
                    try:
                        self._send_marker(peer, snapshot_id)
                    except Exception:
                        pass

            # Mark the inbound channel from 'from_id' as received
            ch = st.inbound_channels.setdefault(from_id, ChannelRecord())
            ch.marker_received = True

            # Completion check
            if self._all_inbound_marked(st):
                self._finalize(snapshot_id)

    # -------------------------------------------------------------------------
    # Recording per-channel messages (data plane)
    # -------------------------------------------------------------------------
    def on_receive(self, from_id: int, message: Any) -> None:
        """
        Notify manager that a data message was received from 'from_id'.
        For each active snapshot where local state is recorded but MARKER not yet
        received on this channel, record message in the channel buffer.
        """
        with self._lock:
            for sid, st in self._snapshots.items():
                if not st.local_recorded or st.complete:
                    continue
                ch = st.inbound_channels.setdefault(from_id, ChannelRecord())
                if not ch.marker_received:
                    ch.in_flight_messages.append(self._sanitize_message(message))

    def on_send(self, to_id: int, message: Any) -> None:
        """
        Optional hook if you want to track outbound messages; not required by
        Chandy–Lamport. Kept for symmetry and debugging. No-op by default.
        """
        # You can extend this to record outbound if needed for diagnostics.
        pass

    # -------------------------------------------------------------------------
    # Finalization and emission
    # -------------------------------------------------------------------------
    def _finalize(self, snapshot_id: str) -> None:
        st = self._snapshots.get(snapshot_id)
        if not st or st.complete:
            return

        st.complete = True
        payload = {
            "snapshot_id": snapshot_id,
            "initiator_id": st.initiator_id,
            "controller_id": self.controller_id,
            "timestamp": time.time(),
            "started_at": st.started_at,
            "membership": sorted(list(self._peers)),
            "local_state": st.local_state,
            "channels": {
                str(peer): {
                    "marker_received": ch.marker_received,
                    "in_flight_messages": ch.in_flight_messages
                }
                for peer, ch in st.inbound_channels.items()
            }
        }
        # Emit to collector
        try:
            self._emit_snapshot(snapshot_id, payload)
        except Exception:
            # Non-fatal; consider logging
            pass

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _safe_get_local_state(self) -> Dict[str, Any]:
        try:
            state = self._get_local_state()
            return self._sanitize_state(state)
        except Exception:
            # Fallback: return minimal state
            return {
                "error": "get_local_state failed",
                "clock": None,
                "status": "unknown"
            }

    @staticmethod
    def _sanitize_state(state: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure state is JSON-serializable (convert non-serializable items as needed)
        def convert(v):
            if isinstance(v, (str, int, float, bool)) or v is None:
                return v
            if isinstance(v, (list, tuple)):
                return [convert(x) for x in v]
            if isinstance(v, dict):
                return {str(k): convert(vv) for k, vv in v.items()}
            # Fallback to string
            return str(v)

        return {str(k): convert(v) for k, v in state.items()}

    @staticmethod
    def _sanitize_message(msg: Any) -> Any:
        # Similar sanitization for messages
        if isinstance(msg, (str, int, float, bool)) or msg is None:
            return msg
        if isinstance(msg, (list, tuple)):
            return [SnapshotManager._sanitize_message(x) for x in msg]
        if isinstance(msg, dict):
            return {str(k): SnapshotManager._sanitize_message(v) for k, v in msg.items()}
        return str(msg)

    @staticmethod
    def _all_inbound_marked(st: SnapshotState) -> bool:
        if not st.inbound_channels:
            # No inbound channels; snapshot complete
            return True
        return all(ch.marker_received for ch in st.inbound_channels.values())

    # -------------------------------------------------------------------------
    # Introspection
    # -------------------------------------------------------------------------
    def list_active(self) -> List[str]:
        with self._lock:
            return [sid for sid, st in self._snapshots.items() if not st.complete]

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            st = self._snapshots.get(snapshot_id)
            if not st:
                return None
            return {
                "snapshot_id": snapshot_id,
                "local_recorded": st.local_recorded,
                "complete": st.complete,
                "initiator_id": st.initiator_id,
                "inbound": {
                    peer: {
                        "marker_received": ch.marker_received,
                        "buffer_len": len(ch.in_flight_messages)
                    }
                    for peer, ch in st.inbound_channels.items()
                }
            }

    # -------------------------------------------------------------------------
    # Convenience: simulated marker sending for local testing
    # -------------------------------------------------------------------------
    def simulate_network_marker(self, snapshot_id: str) -> None:
        """
        For local tests without a network, immediately call handle_marker on
        a synthetic inbound channel per peer. Not for production use.
        """
        for peer in list(self._peers):
            self.handle_marker(snapshot_id, from_id=peer)
