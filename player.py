"""
player.py - Player state.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Player:
    name: str = "Adventurer"
    room_id: int = 1
    max_carry_weight: int = 20
    # future: stats, hp, etc.

    def carried_weight(self, world) -> int:
        return sum(a.weight for a in world.artifacts_carried())

    def can_carry(self, artifact, world) -> bool:
        return self.carried_weight(world) + artifact.weight <= self.max_carry_weight
