import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Callable, Optional

# -----------------------------------------------------------------------------
# Message types carried between controllers for a specific resource (e.g., runway)
# -----------------------------------------------------------------------------
# REQUEST(resource_id, ts, requester_id)
# REPLY(resource_id, ts, replier_id)
# RELEASE(resource_id, ts, releaser_id)
#
# Protocol (Ricart–Agrawala):
# - To enter critical section (CS) for resource R, requester broadcasts REQUEST(R, ts).
# - A peer REPLYs unless it is requesting/holding R with a strictly lower (ts, id).
# - Requester enters CS after receiving REPLY from all live peers.
# - On exit, requester broadcasts RELEASE(R); deferred replies (if any) are sent.
# -----------------------------------------------------------------------------

@dataclass(order=True)
class RequestKey:
    ts: int
    node_id: int


@dataclass
class ResourceState:
    # Local state per controlled resource
    requesting: bool = False
    in_cs: bool = False
    request_key: Optional[RequestKey] = None
    deferred: Set[int] = field(default_factory=set)  # peers we owe a reply to
    replies: Set[int] = field(default_factory=set)   # peers that have replied for current request


class Clock:
    """Simple Lamport clock for the mutex layer."""
    def __init__(self, initial: int = 0):
        self._lock = threading.Lock()
        self.value = initial

    def tick(self) -> int:
        with self._lock:
            self.value += 1
            return self.value

    def update_on_receive(self, incoming_ts: int) -> int:
        with self._lock:
            self.value = max(self.value, incoming_ts) + 1
            return self.value

    def read(self) -> int:
        with self._lock:
            return self.value


class NetworkAdapter:
    """
    Abstract adapter for sending messages to peers.
    Provide concrete implementations that deliver to remote controllers.
    """

    def __init__(self,
                 send_request: Callable[[str, int, int, int], None],
                 send_reply: Callable[[str, int, int, int], None],
                 send_release: Callable[[str, int, int, int], None]):
        """
        Args:
            send_request(resource_id, ts, from_id, to_id)
            send_reply(resource_id, ts, from_id, to_id)
            send_release(resource_id, ts, from_id, to_id)
        """
        self.send_request = send_request
        self.send_reply = send_reply
        self.send_release = send_release


class MutualExclusion:
    """
    Ricart–Agrawala distributed mutual exclusion per resource.

    Usage:
        mutex = MutualExclusion(controller_id=1, peers=[2,3], on_enter=lambda r: ..., on_exit=lambda r: ..., net=adapter)
        mutex.request("RWY_A")   # begin entry protocol
        ...
        mutex.handle_request(...) # when a REQUEST from peer arrives
        ...
        mutex.release("RWY_A")   # exit protocol
    """

    def __init__(self,
                 controller_id: int,
                 peers: List[int],
                 net: NetworkAdapter,
                 on_enter: Optional[Callable[[str], None]] = None,
                 on_exit: Optional[Callable[[str], None]] = None,
                 reply_timeout_s: float = 5.0):
        self.controller_id = controller_id
        self._peers = set(peers)  # current membership
        self._clock = Clock()
        self._net = net
        self._on_enter = on_enter or (lambda r: None)
        self._on_exit = on_exit or (lambda r: None)
        self._reply_timeout_s = reply_timeout_s

        self._resources: Dict[str, ResourceState] = {}
        self._lock = threading.RLock()

    # -------------------------------------------------------------------------
    # Membership management
    # -------------------------------------------------------------------------
    def set_membership(self, peers: List[int]) -> None:
        """Update current live peers."""
        with self._lock:
            self._peers = set(peers)

    def peers(self) -> Set[int]:
        with self._lock:
            return set(self._peers)

    # -------------------------------------------------------------------------
    # Entry protocol (request critical section)
    # -------------------------------------------------------------------------
    def request(self, resource_id: str) -> None:
        """
        Begin the entry protocol for resource_id.
        Broadcast REQUEST with Lamport timestamp, then wait for all REPLYs.
        """
        with self._lock:
            rs = self._resources.setdefault(resource_id, ResourceState())
            if rs.in_cs:
                # Already in CS; nothing to do.
                return
            if rs.requesting:
                # Already requesting; no duplicate broadcast.
                return

            ts = self._clock.tick()
            rs.requesting = True
            rs.request_key = RequestKey(ts=ts, node_id=self.controller_id)
            rs.replies.clear()  # reset replies for new request

            # Broadcast REQUEST to all peers
            for peer in self._peers:
                self._net.send_request(resource_id, ts, self.controller_id, peer)

            # Start waiter thread to complete entry when all replies are received
            threading.Thread(
                target=self._await_replies_and_enter,
                args=(resource_id, rs.request_key, ts, self._reply_timeout_s),
                daemon=True
            ).start()

    def _await_replies_and_enter(self, resource_id: str, key: RequestKey, ts: int, timeout_s: float) -> None:
        deadline = time.time() + timeout_s
        while True:
            with self._lock:
                rs = self._resources[resource_id]
                have = rs.replies
                need = self._peers
                # If membership shrank (failures), we only require current peers
                all_replied = need.issubset(have)
                if all_replied and rs.requesting and rs.request_key == key:
                    rs.in_cs = True
                    rs.requesting = False
                    # Enter critical section
                    self._on_enter(resource_id)
                    return

            if time.time() > deadline:
                # Timeout resilience: re-broadcast REQUEST to missing peers
                missing = list(need - have)
                if missing:
                    with self._lock:
                        # bump clock and resend
                        ts2 = self._clock.tick()
                        for peer in missing:
                            self._net.send_request(resource_id, ts2, self.controller_id, peer)
                        # Extend deadline
                        deadline = time.time() + timeout_s
                else:
                    # No missing, race lost; loop will pick up on next tick
                    deadline = time.time() + timeout_s
            time.sleep(0.05)

    # -------------------------------------------------------------------------
    # Exit protocol (release critical section)
    # -------------------------------------------------------------------------
    def release(self, resource_id: str) -> None:
        """
        Exit critical section and broadcast RELEASE.
        Also flush any deferred replies.
        """
        with self._lock:
            rs = self._resources.setdefault(resource_id, ResourceState())
            if not rs.in_cs:
                return

            rs.in_cs = False
            self._on_exit(resource_id)

            ts = self._clock.tick()
            # Broadcast RELEASE to all peers
            for peer in self._peers:
                self._net.send_release(resource_id, ts, self.controller_id, peer)

            # Send deferred replies (if we owed any during our request/CS)
            for peer in list(rs.deferred):
                ts2 = self._clock.tick()
                self._net.send_reply(resource_id, ts2, self.controller_id, peer)
                rs.deferred.remove(peer)

            # Clear request state
            rs.requesting = False
            rs.request_key = None
            rs.replies.clear()

    # -------------------------------------------------------------------------
    # Handlers for incoming messages
    # -------------------------------------------------------------------------
    def handle_request(self, resource_id: str, ts: int, from_id: int) -> None:
        """
        Called when a REQUEST message is received from peer 'from_id' for 'resource_id'.
        Decide whether to REPLY immediately or defer based on RA priority rule.
        """
        with self._lock:
            self._clock.update_on_receive(ts)

            rs = self._resources.setdefault(resource_id, ResourceState())
            incoming_key = RequestKey(ts=ts, node_id=from_id)

            # Priority rule:
            # - If we are in CS for R, defer.
            # - Else if we are requesting R and our key has higher priority (lower ts, or tie-breaker lower id), defer.
            # - Else, reply immediately.
            should_defer = False
            if rs.in_cs:
                should_defer = True
            elif rs.requesting and rs.request_key is not None:
                my = rs.request_key
                # Compare lexicographically: lower ts wins; on tie, lower node_id wins
                if my < incoming_key:
                    should_defer = True

            if should_defer:
                rs.deferred.add(from_id)
            else:
                ts2 = self._clock.tick()
                self._net.send_reply(resource_id, ts2, self.controller_id, from_id)

    def handle_reply(self, resource_id: str, ts: int, from_id: int) -> None:
        """
        Called when a REPLY is received from peer 'from_id' for 'resource_id'.
        """
        with self._lock:
            self._clock.update_on_receive(ts)
            rs = self._resources.setdefault(resource_id, ResourceState())
            if rs.requesting:
                rs.replies.add(from_id)

    def handle_release(self, resource_id: str, ts: int, from_id: int) -> None:
        """
        Called when a RELEASE is received from peer 'from_id' for 'resource_id'.
        On RELEASE, if we had deferred to that peer, we may now send our reply if still owed.
        """
        with self._lock:
            self._clock.update_on_receive(ts)
            rs = self._resources.setdefault(resource_id, ResourceState())

            # If we deferred to 'from_id', and still owe a reply, send it.
            if from_id in rs.deferred:
                ts2 = self._clock.tick()
                self._net.send_reply(resource_id, ts2, self.controller_id, from_id)
                rs.deferred.discard(from_id)

    # -------------------------------------------------------------------------
    # Introspection helpers (useful for GUI/diagnostics)
    # -------------------------------------------------------------------------
    def is_in_cs(self, resource_id: str) -> bool:
        with self._lock:
            return self._resources.get(resource_id, ResourceState()).in_cs

    def is_requesting(self, resource_id: str) -> bool:
        with self._lock:
            return self._resources.get(resource_id, ResourceState()).requesting

    def status(self, resource_id: str) -> Dict[str, object]:
        with self._lock:
            rs = self._resources.get(resource_id, ResourceState())
            return {
                "requesting": rs.requesting,
                "in_cs": rs.in_cs,
                "request_key": (rs.request_key.ts, rs.request_key.node_id) if rs.request_key else None,
                "deferred": sorted(list(rs.deferred)),
                "replies": sorted(list(rs.replies)),
                "clock": self._clock.read(),
                "peers": sorted(list(self._peers)),
            }
