"""
Messaging package for Distributed Air Traffic Control System (DATCS).

This package provides:
- LamportMulticast: total order multicast using Lamport timestamps.
- MutualExclusion: Ricart–Agrawala distributed mutual exclusion for runway/aircraft resources.
- SnapshotManager: Chandy–Lamport global snapshot protocol for consistent state capture.
"""

from .lamport_multicast import LamportMulticast
from .mutual_exclusion import MutualExclusion, NetworkAdapter
from .snapshot_manager import SnapshotManager

__all__ = [
    "LamportMulticast",
    "MutualExclusion",
    "NetworkAdapter",
    "SnapshotManager",
]
