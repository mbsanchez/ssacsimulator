"""SSAC headless simulation core.

Python port of the detection half of SSACSimulator (Sánchez, Exposito,
Aguilar — Computers in Industry 121, 103247, 2020), extracted from the Qt
application so that experiments can run in batch.

The original implements Monitor and Analyze. Plan, Execute and the MAPE-K
Knowledge base are not present in the published code; this package keeps that
boundary explicit rather than papering over it.
"""

from .engine import (
    DEFAULT_SPEED,
    DEFAULT_TIME_DELAY,
    Detection,
    FailType,
    Piece,
    RunStats,
    SimulationEngine,
)
from .events import SimulationData, SimulationEvent
from .model import Actor, BusinessProcessModel, Edge, NodeType

__all__ = [
    "Actor",
    "BusinessProcessModel",
    "DEFAULT_SPEED",
    "DEFAULT_TIME_DELAY",
    "Detection",
    "Edge",
    "FailType",
    "NodeType",
    "Piece",
    "RunStats",
    "SimulationData",
    "SimulationEngine",
    "SimulationEvent",
]
