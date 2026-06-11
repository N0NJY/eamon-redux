"""
player.py - Runtime player state derived from Character stats.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# Valid equipment slots and which artifact types go in them
EQUIP_SLOTS = {
    "weapon": ["weapon"],
    "armor":  ["armor"],
    "shield": ["shield"],
    "ring":   ["ring"],
    "cloak":  ["cloak"],
}

def slot_for_type(artifact_type: str) -> Optional[str]:
    """Return the equipment slot name for a given artifact type, or None."""
    for slot, types in EQUIP_SLOTS.items():
        if artifact_type in types:
            return slot
    return None


@dataclass
class Player:
    name: str = "Adventurer"
    char_class: str = "Fighter"
    room_id: int = 1

    # Stats
    hardiness:    int = 10
    agility:      int = 10
    charisma:     int = 10
    intelligence: int = 10
    strength:     int = 10

    # Runtime pools
    hp:   int = 0
    mana: int = 0
    gold: int = 100

    # Spells known
    spells: list[str] = field(default_factory=list)

    # Equipment slots: slot_name -> artifact_id (or None)
    equipped: dict[str, Optional[int]] = field(default_factory=lambda: {
        "weapon": None,
        "armor":  None,
        "shield": None,
        "ring":   None,
        "cloak":  None,
    })

    # XP and level (mirrors character.json, updated on exit)
    xp: int = 0
    level: int = 1
    xp_gained: int = 0   # XP earned this adventure session

    # Combat tracking for stat advancement
    took_damage_this_fight: bool = False

    # Shield spell rounds remaining
    shield_rounds: int = 0

    # Base unarmed attack
    damage_dice:  int = 1
    damage_sides: int = 4

    max_carry_weight: int = 100

    def __post_init__(self):
        if self.hp <= 0:
            self.hp = self.hp_max
        if self.mana <= 0:
            self.mana = self.mana_max
        # Ensure all slots exist (handles old saves missing new slots)
        for slot in EQUIP_SLOTS:
            if slot not in self.equipped:
                self.equipped[slot] = None

    # ── Derived stats ─────────────────────────────────────────────────────────

    @property
    def hp_max(self) -> int:
        return self.hardiness * 2

    @property
    def mana_max(self) -> int:
        return self.intelligence * 2

    @property
    def agility_bonus(self) -> int:
        return (self.agility - 10) // 2

    @property
    def strength_bonus(self) -> int:
        return (self.strength - 10) // 2 if self.char_class == "Fighter" else 0

    @property
    def spell_bonus(self) -> int:
        return (self.intelligence - 10) // 2 if self.char_class == "Sorcerer" else 0

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    # ── Equipment helpers ─────────────────────────────────────────────────────

    def equipped_weapon(self, world) -> Optional[object]:
        """Return the equipped weapon Artifact or None."""
        wid = self.equipped.get("weapon")
        if wid is None:
            return None
        return world.artifacts.get(wid)

    def armor_class(self, world) -> int:
        """Sum AC from equipped armor and shield, plus shield spell."""
        ac = 0
        for slot in ("armor", "shield"):
            aid = self.equipped.get(slot)
            if aid is not None:
                a = world.artifacts.get(aid)
                if a:
                    ac += a.armor_class
        if self.shield_rounds > 0:
            ac += 3
        return ac

    def is_equipped(self, artifact_id: int) -> bool:
        return artifact_id in self.equipped.values()

    def equip(self, artifact, world) -> tuple[bool, str]:
        """
        Attempt to equip an artifact. Returns (success, message).
        Artifact must be in carried inventory.
        """
        slot = slot_for_type(artifact.artifact_type)
        if slot is None:
            return False, f"The {artifact.name} can't be equipped."

        # Check it's carried
        if artifact.room_id is not None:
            return False, f"You need to pick up the {artifact.name} first."

        # Unequip whatever's in the slot
        current_id = self.equipped.get(slot)
        if current_id is not None:
            current = world.artifacts.get(current_id)
            if current:
                msg = f"You remove the {current.name} and equip the {artifact.name}."
            else:
                msg = f"You equip the {artifact.name}."
        else:
            msg = f"You equip the {artifact.name}."

        self.equipped[slot] = artifact.id
        return True, msg

    def unequip_slot(self, slot: str, world) -> tuple[bool, str]:
        """Unequip whatever is in a slot."""
        aid = self.equipped.get(slot)
        if aid is None:
            return False, f"Nothing equipped in {slot} slot."
        a = world.artifacts.get(aid)
        self.equipped[slot] = None
        name = a.name if a else f"item #{aid}"
        return True, f"You remove the {name}."

    def unequip_artifact(self, artifact, world) -> tuple[bool, str]:
        """Unequip a specific artifact."""
        for slot, aid in self.equipped.items():
            if aid == artifact.id:
                self.equipped[slot] = None
                return True, f"You remove the {artifact.name}."
        return False, f"The {artifact.name} is not equipped."

    # ── Inventory helpers ─────────────────────────────────────────────────────

    def carried_weight(self, world) -> int:
        return sum(a.weight for a in world.artifacts_carried())

    def can_carry(self, artifact, world) -> bool:
        return self.carried_weight(world) + artifact.weight <= self.max_carry_weight

    # ── Display ───────────────────────────────────────────────────────────────

    def health_bar(self) -> str:
        pct = max(0, self.hp) / self.hp_max
        filled = int(pct * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return f"HP [{bar}] {self.hp}/{self.hp_max}"

    def mana_bar(self) -> str:
        if self.char_class != "Sorcerer":
            return ""
        pct = max(0, self.mana) / self.mana_max if self.mana_max > 0 else 0
        filled = int(pct * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return f"MP [{bar}] {self.mana}/{self.mana_max}"
