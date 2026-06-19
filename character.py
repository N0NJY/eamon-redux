"""
character.py - Persistent character data (REWRITTEN).
Universal system: any character can learn any spell and use any weapon.
No classes. Proficiency-based magic (not mana). Separate weapon proficiencies.
"""

from __future__ import annotations
import json
import os
import random
from dataclasses import dataclass, field
from typing import Optional

CHARACTERS_DIR = "characters"

# ── Spell Definitions ─────────────────────────────────────────────────────────

SPELL_DEFS = {
    "blast":  {"name": "Blast",  "cost": 3000, "desc": "1D6 damage, bypasses armor"},
    "heal":   {"name": "Heal",   "cost": 1000, "desc": "1D10 HP restore"},
    "speed":  {"name": "Speed",  "cost": 5000, "desc": "Double Agility for 11-20 rounds"},
    "power":  {"name": "Power",  "cost": 100,  "desc": "Adventure-specific effect"},
}

# ── Weapon Types ──────────────────────────────────────────────────────────────

WEAPON_TYPES = {
    "axe":    {"name": "Axe",    "start_prof": 5},
    "bow":    {"name": "Bow",    "start_prof": -10},
    "club":   {"name": "Club",   "start_prof": 20},
    "spear":  {"name": "Spear",  "start_prof": 10},
    "sword":  {"name": "Sword",  "start_prof": 0},
}

def roll3d6() -> int:
    return sum(random.randint(1, 6) for _ in range(3))


@dataclass
class Character:
    name: str

    # ── Core stats ────────────────────────────────────────────────────────────
    hardiness:    int = 10
    agility:      int = 10
    charisma:     int = 10
    intelligence: int = 10
    strength:     int = 10

    # ── Runtime ───────────────────────────────────────────────────────────────
    hp:   int = 0
    gold: int = 200  # Starting gold (changed from 100 to allow spell learning)

    # ── Spell proficiencies (None = not learned yet, int = proficiency %)
    spell_proficiencies: dict[str, Optional[int]] = field(
        default_factory=lambda: {
            "blast": None,
            "heal": None,
            "speed": None,
            "power": None,
        }
    )

    # ── Weapon proficiencies (separate for each weapon type)
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

    # ── Progression ───────────────────────────────────────────────────────────
    xp: int = 0
    level: int = 1
    is_beginner: bool = True
    adventures_completed: list[str] = field(default_factory=list)
    equipped: dict = field(default_factory=dict)  # slot → artifact_name

    # ── Computed ──────────────────────────────────────────────────────────────

    @property
    def hp_max(self) -> int:
        return self.hardiness * 2

    @property
    def carry_capacity(self) -> int:
        return self.hardiness * 10

    @property
    def agility_bonus(self) -> int:
        return (self.agility - 10) // 2

    @property
    def charisma_bonus(self) -> int:
        return (self.charisma - 10) // 2

    @property
    def intelligence_bonus(self) -> int:
        return (self.intelligence - 10) // 2

    @property
    def strength_bonus(self) -> int:
        return (self.strength - 10) // 2

    # ── Spell Learning ────────────────────────────────────────────────────────

    def learn_spell(self, spell_key: str) -> tuple[bool, str]:
        """Learn a spell (if not already learned and have enough gold)."""
        if spell_key not in SPELL_DEFS:
            return False, f"Unknown spell: {spell_key}"
        
        if self.spell_proficiencies.get(spell_key) is not None:
            return False, f"You already know {SPELL_DEFS[spell_key]['name']}."
        
        cost = SPELL_DEFS[spell_key]["cost"]
        if self.gold < cost:
            return False, f"You need {cost} gold to learn {SPELL_DEFS[spell_key]['name']} (you have {self.gold})."
        
        # Learn spell with random starting proficiency (25-75%)
        starting_prof = random.randint(25, 75)
        self.spell_proficiencies[spell_key] = starting_prof
        self.gold -= cost
        
        return True, f"You learn {SPELL_DEFS[spell_key]['name']}! Starting proficiency: {starting_prof}%"

    # ── Display ───────────────────────────────────────────────────────────────

    def stat_summary(self) -> str:
        """Return complete character sheet with ALL stats."""
        lines = [
            f"",
            f"  ╔════════════════════════════════════════════════════╗",
            f"  ║  {self.name:<50}║",
            f"  ╠════════════════════════════════════════════════════╣",
            f"  ║  CORE STATS                                        ║",
            f"  ├────────────────────────────────────────────────────┤",
            f"  │  Hardiness    : {self.hardiness:<3}  HP: {self.hp}/{self.hp_max:<3}  Carry: {self.carry_capacity:<3} gronds",
            f"  │  Agility      : {self.agility:<3}  (combat bonus: {self.agility_bonus:+d})",
            f"  │  Strength     : {self.strength:<3}  (damage bonus: {self.strength_bonus:+d})",
            f"  │  Intelligence : {self.intelligence:<3}  (spell bonus: {self.intelligence_bonus:+d})",
            f"  │  Charisma     : {self.charisma:<3}  (reaction: {self.charisma_bonus:+d})",
            f"  ║                                                    ║",
            f"  ║  SPELL PROFICIENCIES                               ║",
            f"  ├────────────────────────────────────────────────────┤",
        ]
        
        for spell_key, prof in self.spell_proficiencies.items():
            spell_name = SPELL_DEFS[spell_key]["name"]
            if prof is None:
                lines.append(f"  │  {spell_name:<12} : Not learned")
            else:
                lines.append(f"  │  {spell_name:<12} : {prof:>3}%")
        
        lines.extend([
            f"  ║                                                    ║",
            f"  ║  WEAPON PROFICIENCIES                              ║",
            f"  ├────────────────────────────────────────────────────┤",
        ])
        
        for weapon_key, prof in self.weapon_proficiencies.items():
            if weapon_key not in WEAPON_TYPES:
                continue
            weapon_name = WEAPON_TYPES[weapon_key]["name"]
            lines.append(f"  │  {weapon_name:<12} : {prof:>3}%")
        
        lines.extend([
            f"  ║                                                    ║",
            f"  ║  PROGRESSION & STATUS                              ║",
            f"  ├────────────────────────────────────────────────────┤",
            f"  │  Gold         : {self.gold}",
            f"  │  Level        : {self.level}  (XP: {self.xp})",
            f"  │  Status       : {'Beginner' if self.is_beginner else 'Veteran'}",
        ])
        
        if self.adventures_completed:
            lines.append(f"  │  Completed    : {', '.join(self.adventures_completed)}")

        active = {s: n for s, n in self.equipped.items() if n}
        lines.extend([
            f"  ║                                                    ║",
            f"  ║  EQUIPPED ITEMS                                    ║",
            f"  ├────────────────────────────────────────────────────┤",
        ])
        if active:
            for slot, name in active.items():
                lines.append(f"  │  {slot.upper():<12} : {name}")
        else:
            lines.append(f"  │  (nothing equipped)")

        lines.extend([
            f"  ╚════════════════════════════════════════════════════╝",
            f"",
        ])
        
        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        with open(self._path(self.name), "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hardiness": self.hardiness,
            "agility": self.agility,
            "charisma": self.charisma,
            "intelligence": self.intelligence,
            "strength": self.strength,
            "hp": self.hp,
            "gold": self.gold,
            "spell_proficiencies": self.spell_proficiencies,
            "weapon_proficiencies": self.weapon_proficiencies,
            "xp": self.xp,
            "level": self.level,
            "is_beginner": self.is_beginner,
            "adventures_completed": self.adventures_completed,
            "equipped": self.equipped,
        }

    @staticmethod
    def from_dict(d: dict) -> "Character":
        ch = Character(
            name=d["name"],
            hardiness=d.get("hardiness", 10),
            agility=d.get("agility", 10),
            charisma=d.get("charisma", 10),
            intelligence=d.get("intelligence", 10),
            strength=d.get("strength", 10),
            hp=d.get("hp", 0),
            gold=d.get("gold", 200),
            spell_proficiencies=d.get("spell_proficiencies", {
                "blast": None, "heal": None, "speed": None, "power": None
            }),
            weapon_proficiencies=d.get("weapon_proficiencies", {
                "unarmed": 0, "axe": 5, "bow": -10, "club": 20, "spear": 10, "sword": 0
            }),
            xp=d.get("xp", 0),
            level=d.get("level", 1),
            is_beginner=d.get("is_beginner", True),
            adventures_completed=d.get("adventures_completed", []),
            equipped=d.get("equipped", {}),
        )
        if ch.hp <= 0:
            ch.hp = ch.hp_max
        return ch

    @staticmethod
    def load(name: str) -> Optional["Character"]:
        path = Character._path(name)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return Character.from_dict(json.load(f))

    @staticmethod
    def delete(name: str) -> bool:
        path = Character._path(name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    @staticmethod
    def list_all() -> list[str]:
        if not os.path.isdir(CHARACTERS_DIR):
            return []
        return [f[:-5] for f in sorted(os.listdir(CHARACTERS_DIR))
                if f.endswith(".json") and not f.endswith("_items.json")]

    @staticmethod
    def _path(name: str) -> str:
        safe = name.lower().replace(" ", "_")
        return os.path.join(CHARACTERS_DIR, f"{safe}.json")

    # ── Interactive creation ──────────────────────────────────────────────────

    @staticmethod
    def create_interactive() -> "Character":
        from tavern import tc

        print(tc("\n  Enter your character's name: ", "prompt"), end="")
        name = input().strip()
        if not name:
            name = "Adventurer"

        existing = Character.load(name)
        if existing:
            print(tc(f"\n  A character named '{name}' already exists.", "error"))
            print(tc("  Load them instead, or choose a different name.", "warn"))
            return existing

        # ── Stat rolling loop ─────────────────────────────────────────────────
        roll_number = 1
        while True:
            hardiness    = roll3d6()
            agility      = roll3d6()
            charisma     = roll3d6()
            intelligence = roll3d6()
            strength     = roll3d6()

            ch = Character(
                name=name,
                hardiness=hardiness, agility=agility, charisma=charisma,
                intelligence=intelligence, strength=strength,
            )
            ch.hp = ch.hp_max

            print()
            print(tc(f"  ┌─────────────────────────────────────────────────┐", "border"))
            print(tc(f"  │  {name}{'':<{49 - len(name)}}│", "title"))
            print(tc(f"  │  Roll #{roll_number:<42}│", "desc"))
            print(tc(f"  ├─────────────────────────────────────────────────┤", "border"))
            print(tc(f"  │  Hardiness    : {hardiness:<3}  HP: {ch.hp_max:<18}│", "stat"))
            print(tc(f"  │  Agility      : {agility:<3}  (combat bonus: {ch.agility_bonus:+d}){'':<10}│", "stat"))
            print(tc(f"  │  Strength     : {strength:<3}  (damage bonus: {ch.strength_bonus:+d}){'':<11}│", "stat"))
            print(tc(f"  │  Intelligence : {intelligence:<3}  (spell bonus: {ch.intelligence_bonus:+d}){'':<11}│", "stat"))
            print(tc(f"  │  Charisma     : {charisma:<3}  (reaction: {ch.charisma_bonus:+d}){'':<13}│", "stat"))
            print(tc(f"  │  Gold         : 200 (starting capital){'':<20}│", "stat"))
            print(tc(f"  └─────────────────────────────────────────────────┘", "border"))
            print()

            answer = input(tc("  Keep these stats? (y/n): ", "prompt")).strip().lower()
            if answer == "y":
                break
            roll_number += 1
            print(tc("  Re-rolling...", "sys"))

        ch.save()
        print(tc(f"\n  Character '{name}' saved. Starting with 200 gold.", "sys"))
        print(tc(f"  Visit Aldric in the tavern to learn spells!", "sys"))
        return ch
