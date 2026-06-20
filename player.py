"""
player.py - Runtime player state (REWRITTEN).
Mirrors character proficiencies. Adds fatigue tracking for spells and weapons.
Adds speed spell state tracking.
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
    gold: int = 200

    # Spell proficiencies (None = not learned, int = proficiency %)
    spell_proficiencies: dict[str, Optional[int]] = field(
        default_factory=lambda: {
            "blast": None,
            "heal": None,
            "speed": None,
            "power": None,
        }
    )

    # Weapon proficiencies
    weapon_proficiencies: dict[str, int] = field(
        default_factory=lambda: {
            "unarmed": 0,
            "axe": 5,
            "bow": -10,
            "club": 20,
            "spear": 10,
            "sword": 0,
        }
    )

    # ── Fatigue Tracking (for spell proficiency reduction) ─────────────────────
    # spell_fatigue_multiplier tracks current effective proficiency multiplier
    # 1.0 = 100%, 0.5 = 50%, 0.25 = 25%, etc.
    spell_fatigue_multiplier: dict[str, float] = field(
        default_factory=lambda: {
            "blast": 1.0,
            "heal": 1.0,
            "speed": 1.0,
            "power": 1.0,
        }
    )

    # Spells locked due to critical failure (1% overload chance)
    spell_locked: dict[str, bool] = field(
        default_factory=lambda: {
            "blast": False,
            "heal": False,
            "speed": False,
            "power": False,
        }
    )

    # ── Speed Spell State ─────────────────────────────────────────────────────
    speed_active: bool = False
    speed_rounds_remaining: int = 0

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

    # Quest and follower tracking
    quest_flags: dict = field(default_factory=dict)
    followers: list = field(default_factory=list)
    alignment: str = "neutral"
    combat_kills: int = 0

    # Combat tracking
    took_damage_this_fight: bool = False

    # Base unarmed attack
    damage_dice:  int = 1
    damage_sides: int = 4

    max_carry_weight: int = 100

    def __post_init__(self):
        if self.hp <= 0:
            self.hp = self.hp_max
        if self.mana <= 0:
            self.mana = self.mana_max
        # Ensure all slots exist
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
    def agility_effective(self) -> int:
        """Current agility including speed spell bonus."""
        base = self.agility
        if self.speed_active:
            base *= 2
        return base

    @property
    def agility_effective_bonus(self) -> int:
        """Combat agility bonus, doubled while speed spell is active."""
        return (self.agility_effective - 10) // 2

    @property
    def strength_bonus(self) -> int:
        return (self.strength - 10) // 2

    @property
    def intelligence_bonus(self) -> int:
        return (self.intelligence - 10) // 2

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    # ── Spell Fatigue Methods ─────────────────────────────────────────────────

    def get_effective_spell_proficiency(self, spell_key: str) -> int:
        """Get current effective proficiency including fatigue."""
        base_prof = self.spell_proficiencies.get(spell_key)
        if base_prof is None:
            return 0
        
        multiplier = self.spell_fatigue_multiplier.get(spell_key, 1.0)
        effective = int(base_prof * multiplier)
        
        # Hard minimum 5%
        if effective < 5:
            effective = 5
        
        return effective

    def apply_spell_fatigue(self, spell_key: str) -> None:
        """Halve spell fatigue multiplier after a cast (50%, 25%, 12.5%, etc.)."""
        current = self.spell_fatigue_multiplier.get(spell_key, 1.0)
        self.spell_fatigue_multiplier[spell_key] = current * 0.5

    def recover_spell_fatigue(self, spell_key: str, recovery_pct: int) -> None:
        """Recover spell fatigue by recovery_pct (5-10% random per action)."""
        current = self.spell_fatigue_multiplier.get(spell_key, 1.0)
        # Don't go above 1.0
        self.spell_fatigue_multiplier[spell_key] = min(1.0, current + (recovery_pct / 100.0))

    def recover_all_spell_fatigue(self, recovery_pct: int) -> None:
        """Recover fatigue for all spells."""
        for spell_key in self.spell_proficiencies:
            self.recover_spell_fatigue(spell_key, recovery_pct)

    def lock_spell(self, spell_key: str) -> None:
        """Lock a spell due to 1% critical failure (overload)."""
        self.spell_locked[spell_key] = True

    def is_spell_locked(self, spell_key: str) -> bool:
        """Check if spell is locked for rest of adventure."""
        return self.spell_locked.get(spell_key, False)

    # ── Speed Spell Methods ───────────────────────────────────────────────────

    def activate_speed(self, duration: int) -> None:
        """Activate speed spell for N rounds."""
        self.speed_active = True
        self.speed_rounds_remaining = duration

    def deactivate_speed(self) -> None:
        """Deactivate speed spell."""
        self.speed_active = False
        self.speed_rounds_remaining = 0

    def tick_speed_duration(self) -> None:
        """Decrement speed duration (call at end of combat round)."""
        if self.speed_active:
            self.speed_rounds_remaining -= 1
            if self.speed_rounds_remaining <= 0:
                self.deactivate_speed()

    # ── Equipment helpers ─────────────────────────────────────────────────────

    def equipped_weapon(self, world) -> Optional[object]:
        """Return the equipped weapon Artifact or None."""
        wid = self.equipped.get("weapon")
        if wid is None:
            return None
        return world.artifacts.get(wid)

    def armor_class(self, world) -> int:
        """Sum AC from equipped armor and shield."""
        ac = 0
        for slot in ("armor", "shield"):
            aid = self.equipped.get(slot)
            if aid is not None:
                a = world.artifacts.get(aid)
                if a:
                    ac += a.armor_class
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
        if self.hp_max <= 0:
            return "HP [░░░░░░░░░░░░░░░░░░░░] 0/0"
        pct = max(0, self.hp) / self.hp_max
        filled = int(pct * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return f"HP [{bar}] {self.hp}/{self.hp_max}"
