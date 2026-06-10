"""
character.py - Persistent character data.

A Character lives in characters/<name>.json and carries over between adventures.
The Player object in player.py is the runtime game state; Character is what persists.
"""

from __future__ import annotations
import json
import os
import random
from dataclasses import dataclass, field
from typing import Optional


CHARACTERS_DIR = "characters"


def roll3d6() -> int:
    return sum(random.randint(1, 6) for _ in range(3))


@dataclass
class Character:
    name: str

    # ── Core stats (rolled 3d6 each at creation) ──────────────────────────────
    hardiness: int = 10     # HP pool = hardiness*2; carry = hardiness*10 gronds
    agility: int = 10       # hit chance and dodge modifier
    charisma: int = 10      # NPC reactions (stubbed for now)

    # ── Derived / runtime ─────────────────────────────────────────────────────
    hp: int = 0             # current HP (0 = use max on first load)
    gold: int = 100         # starting gold

    # ── Progression ───────────────────────────────────────────────────────────
    is_beginner: bool = True
    adventures_completed: list[str] = field(default_factory=list)

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def hp_max(self) -> int:
        return self.hardiness * 2

    @property
    def carry_capacity(self) -> int:
        """Max carry weight in gronds."""
        return self.hardiness * 10

    @property
    def agility_bonus(self) -> int:
        """Combat modifier: positive above 10, negative below."""
        return (self.agility - 10) // 2

    @property
    def charisma_bonus(self) -> int:
        return (self.charisma - 10) // 2

    def stat_summary(self) -> str:
        lines = [
            f"  Name      : {self.name}",
            f"  Hardiness : {self.hardiness}  (HP: {self.hp}/{self.hp_max}, "
            f"Carry: {self.carry_capacity} gronds)",
            f"  Agility   : {self.agility}  (combat bonus: {self.agility_bonus:+d})",
            f"  Charisma  : {self.charisma}  (reaction bonus: {self.charisma_bonus:+d})",
            f"  Gold      : {self.gold}",
            f"  Status    : {'Beginner' if self.is_beginner else 'Veteran'}",
        ]
        if self.adventures_completed:
            lines.append(f"  Completed : {', '.join(self.adventures_completed)}")
        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        path = self._path(self.name)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hardiness": self.hardiness,
            "agility": self.agility,
            "charisma": self.charisma,
            "hp": self.hp,
            "gold": self.gold,
            "is_beginner": self.is_beginner,
            "adventures_completed": self.adventures_completed,
        }

    @staticmethod
    def from_dict(d: dict) -> "Character":
        ch = Character(
            name=d["name"],
            hardiness=d.get("hardiness", 10),
            agility=d.get("agility", 10),
            charisma=d.get("charisma", 10),
            hp=d.get("hp", 0),
            gold=d.get("gold", 100),
            is_beginner=d.get("is_beginner", True),
            adventures_completed=d.get("adventures_completed", []),
        )
        # Heal to full if hp not set
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
        """Return sorted list of character names from the characters/ folder."""
        if not os.path.isdir(CHARACTERS_DIR):
            return []
        names = []
        for fname in sorted(os.listdir(CHARACTERS_DIR)):
            if fname.endswith(".json"):
                names.append(fname[:-5])
        return names

    @staticmethod
    def _path(name: str) -> str:
        safe = name.lower().replace(" ", "_")
        return os.path.join(CHARACTERS_DIR, f"{safe}.json")

    # ── Creation ──────────────────────────────────────────────────────────────

    @staticmethod
    def create_interactive() -> "Character":
        """Walk the user through rolling a new character, with free rerolls."""
        from tavern import tc   # import here to avoid circular import

        print(tc("  Enter your character's name: ", "prompt"), end="")
        name = input().strip()
        if not name:
            name = "Adventurer"

        # Check for duplicate
        existing = Character.load(name)
        if existing:
            print(tc(f"\n  A character named '{name}' already exists.", "error"))
            print(tc("  Load them instead, or choose a different name.", "warn"))
            return existing

        roll_number = 1
        while True:
            hardiness = roll3d6()
            agility   = roll3d6()
            charisma  = roll3d6()

            ch = Character(name=name, hardiness=hardiness,
                           agility=agility, charisma=charisma)
            ch.hp = ch.hp_max

            print()
            print(tc(f"  ┌─────────────────────────────────────┐", "border"))
            print(tc(f"  │  {name:<35}│", "title"))
            print(tc(f"  │  Roll #{roll_number:<31}│", "desc"))
            print(tc(f"  ├─────────────────────────────────────┤", "border"))
            print(tc(f"  │  Hardiness : {hardiness:<3}  HP: {ch.hp_max:<5}           │", "stat"))
            print(tc(f"  │  Agility   : {agility:<3}  (combat bonus: {ch.agility_bonus:+d})       │", "stat"))
            print(tc(f"  │  Charisma  : {charisma:<3}  (reaction:    {ch.charisma_bonus:+d})       │", "stat"))
            print(tc(f"  │  Gold      : {ch.gold:<3}                     │", "stat"))
            print(tc(f"  └─────────────────────────────────────┘", "border"))
            print()

            answer = input(tc("  Keep these stats? (y/n): ", "prompt")).strip().lower()
            if answer == "y":
                break

            roll_number += 1
            print(tc("  Re-rolling...", "sys"))

        ch.save()
        print(tc(f"\n  Character '{name}' saved. Good luck out there.", "sys"))
        return ch
