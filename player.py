"""
player.py - Player state.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Player:
    name: str = "Adventurer"
    room_id: int = 1

    hp: int = 30
    hp_max: int = 30

    # Base attack: rolls damage_dice d damage_sides
    damage_dice: int = 1
    damage_sides: int = 6

    max_carry_weight: int = 20

    def carried_weight(self, world) -> int:
        return sum(a.weight for a in world.artifacts_carried())

    def can_carry(self, artifact, world) -> bool:
        return self.carried_weight(world) + artifact.weight <= self.max_carry_weight

    def armor_class(self, world) -> int:
        """Sum armor_class of all worn/carried armor artifacts."""
        return sum(a.armor_class for a in world.artifacts_carried()
                   if a.artifact_type == "armor")

    def best_weapon(self, world):
        """Return the highest-damage weapon in inventory, or None."""
        weapons = [a for a in world.artifacts_carried() if a.artifact_type == "weapon"]
        if not weapons:
            return None
        return max(weapons, key=lambda w: w.damage_dice * w.damage_sides)

    def health_bar(self) -> str:
        filled = int((self.hp / self.hp_max) * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return f"HP [{bar}] {self.hp}/{self.hp_max}"

    @property
    def is_alive(self) -> bool:
        return self.hp > 0
