"""
character.py - Persistent character data.
Supports Fighter and Sorcerer classes with full stat sets.
"""

from __future__ import annotations
import json
import os
import random
from dataclasses import dataclass, field
from typing import Optional

CHARACTERS_DIR = "characters"

# ── Classes ───────────────────────────────────────────────────────────────────

class CharClass:
    FIGHTER  = "Fighter"
    SORCERER = "Sorcerer"

# ── Available spells ──────────────────────────────────────────────────────────

SPELL_DEFS = {
    "heal":     {"name": "Heal",     "cost": 4, "desc": "Restore HP (1d6 + INT bonus)"},
    "fireball": {"name": "Fireball", "cost": 6, "desc": "Damage one enemy (2d6 + INT bonus)"},
    "shield":   {"name": "Shield",   "cost": 3, "desc": "Gain +3 armor for 3 combat rounds"},
    "light":    {"name": "Light",    "cost": 2, "desc": "Illuminate dark rooms"},
}

def roll3d6() -> int:
    return sum(random.randint(1, 6) for _ in range(3))


@dataclass
class Character:
    name: str
    char_class: str = CharClass.FIGHTER

    # ── Core stats ────────────────────────────────────────────────────────────
    hardiness:    int = 10
    agility:      int = 10
    charisma:     int = 10
    intelligence: int = 10
    strength:     int = 10   # rolled but only fully used by fighters

    # ── Runtime ───────────────────────────────────────────────────────────────
    hp:   int = 0
    mana: int = 0
    gold: int = 100

    # ── Spells (sorcerer only) ────────────────────────────────────────────────
    spells: list[str] = field(default_factory=list)

    # ── Progression ───────────────────────────────────────────────────────────
    is_beginner: bool = True
    adventures_completed: list[str] = field(default_factory=list)

    # ── Computed ─────────────────────────────────────────────────────────────

    @property
    def hp_max(self) -> int:
        return self.hardiness * 2

    @property
    def mana_max(self) -> int:
        return self.intelligence * 2

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
        # Fighters get full STR bonus; sorcerers get none
        if self.char_class == CharClass.FIGHTER:
            return (self.strength - 10) // 2
        return 0

    @property
    def spell_bonus(self) -> int:
        # Sorcerers get INT bonus to spells; fighters get none
        if self.char_class == CharClass.SORCERER:
            return self.intelligence_bonus
        return 0

    def stat_summary(self) -> str:
        lines = [
            f"  Name         : {self.name}  [{self.char_class}]",
            f"  Hardiness    : {self.hardiness:<3}  HP: {self.hp}/{self.hp_max}  "
            f"Carry: {self.carry_capacity} gronds",
            f"  Agility      : {self.agility:<3}  (combat bonus: {self.agility_bonus:+d})",
            f"  Strength     : {self.strength:<3}  (damage bonus: {self.strength_bonus:+d})",
            f"  Intelligence : {self.intelligence:<3}  (spell bonus: {self.spell_bonus:+d})",
            f"  Charisma     : {self.charisma:<3}  (reaction: {self.charisma_bonus:+d})",
            f"  Gold         : {self.gold}",
        ]
        if self.char_class == CharClass.SORCERER:
            lines.append(f"  Mana         : {self.mana}/{self.mana_max}")
            if self.spells:
                spell_names = ", ".join(SPELL_DEFS[s]["name"] for s in self.spells
                                        if s in SPELL_DEFS)
                lines.append(f"  Spells       : {spell_names}")
        lines.append(f"  Status       : {'Beginner' if self.is_beginner else 'Veteran'}")
        if self.adventures_completed:
            lines.append(f"  Completed    : {', '.join(self.adventures_completed)}")
        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        with open(self._path(self.name), "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "char_class": self.char_class,
            "hardiness": self.hardiness,
            "agility": self.agility,
            "charisma": self.charisma,
            "intelligence": self.intelligence,
            "strength": self.strength,
            "hp": self.hp,
            "mana": self.mana,
            "gold": self.gold,
            "spells": self.spells,
            "is_beginner": self.is_beginner,
            "adventures_completed": self.adventures_completed,
        }

    @staticmethod
    def from_dict(d: dict) -> "Character":
        ch = Character(
            name=d["name"],
            char_class=d.get("char_class", CharClass.FIGHTER),
            hardiness=d.get("hardiness", 10),
            agility=d.get("agility", 10),
            charisma=d.get("charisma", 10),
            intelligence=d.get("intelligence", 10),
            strength=d.get("strength", 10),
            hp=d.get("hp", 0),
            mana=d.get("mana", 0),
            gold=d.get("gold", 100),
            spells=d.get("spells", []),
            is_beginner=d.get("is_beginner", True),
            adventures_completed=d.get("adventures_completed", []),
        )
        if ch.hp <= 0:
            ch.hp = ch.hp_max
        if ch.mana <= 0:
            ch.mana = ch.mana_max
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
                if f.endswith(".json")]

    @staticmethod
    def _path(name: str) -> str:
        safe = name.lower().replace(" ", "_")
        return os.path.join(CHARACTERS_DIR, f"{safe}.json")

    # ── Interactive creation ──────────────────────────────────────────────────

    @staticmethod
    def create_interactive() -> "Character":
        from tavern import tc

        print(tc("  Enter your character's name: ", "prompt"), end="")
        name = input().strip()
        if not name:
            name = "Adventurer"

        existing = Character.load(name)
        if existing:
            print(tc(f"\n  A character named '{name}' already exists.", "error"))
            print(tc("  Load them instead, or choose a different name.", "warn"))
            return existing

        # ── Class selection ───────────────────────────────────────────────────
        print()
        print(tc("  ┌─────────────────────────────────────────────────┐", "border"))
        print(tc("  │  Choose your class:                             │", "title"))
        print(tc("  ├─────────────────────────────────────────────────┤", "border"))
        print(tc("  │  1. Fighter  — Melee combat, STR damage bonus   │", "stat"))
        print(tc("  │               Can use all weapons and armor     │", "desc"))
        print(tc("  │                                                 │", "border"))
        print(tc("  │  2. Sorcerer — Spells and magic, INT mana pool  │", "stat"))
        print(tc("  │               Starts with one spell of choice   │", "desc"))
        print(tc("  └─────────────────────────────────────────────────┘", "border"))
        print()

        while True:
            choice = input(tc("  Choose class (1/2): ", "prompt")).strip()
            if choice == "1":
                char_class = CharClass.FIGHTER
                break
            elif choice == "2":
                char_class = CharClass.SORCERER
                break
            print(tc("  Please enter 1 or 2.", "error"))

        # ── Stat rolling loop ─────────────────────────────────────────────────
        roll_number = 1
        while True:
            hardiness    = roll3d6()
            agility      = roll3d6()
            charisma     = roll3d6()
            intelligence = roll3d6()
            strength     = roll3d6()

            ch = Character(
                name=name, char_class=char_class,
                hardiness=hardiness, agility=agility, charisma=charisma,
                intelligence=intelligence, strength=strength,
            )
            ch.hp   = ch.hp_max
            ch.mana = ch.mana_max

            str_note = f"(dmg bonus: {ch.strength_bonus:+d})" if char_class == CharClass.FIGHTER else "(capped for Sorcerer)"
            int_note = f"(spell bonus: {ch.spell_bonus:+d})" if char_class == CharClass.SORCERER else "(capped for Fighter)"

            print()
            print(tc(f"  ┌─────────────────────────────────────────────────┐", "border"))
            print(tc(f"  │  {name} [{char_class}]{'':<{33 - len(name) - len(char_class)}}│", "title"))
            print(tc(f"  │  Roll #{roll_number:<42}│", "desc"))
            print(tc(f"  ├─────────────────────────────────────────────────┤", "border"))
            print(tc(f"  │  Hardiness    : {hardiness:<3}  HP: {ch.hp_max:<18}│", "stat"))
            print(tc(f"  │  Agility      : {agility:<3}  (combat bonus: {ch.agility_bonus:+d}){'':<10}│", "stat"))
            print(tc(f"  │  Strength     : {strength:<3}  {str_note:<29}│", "stat"))
            print(tc(f"  │  Intelligence : {intelligence:<3}  {int_note:<29}│", "stat"))
            print(tc(f"  │  Charisma     : {charisma:<3}  (reaction: {ch.charisma_bonus:+d}){'':<13}│", "stat"))
            if char_class == CharClass.SORCERER:
                print(tc(f"  │  Mana         : {ch.mana_max:<34}│", "stat"))
            print(tc(f"  │  Gold         : {ch.gold:<34}│", "stat"))
            print(tc(f"  └─────────────────────────────────────────────────┘", "border"))
            print()

            answer = input(tc("  Keep these stats? (y/n): ", "prompt")).strip().lower()
            if answer == "y":
                break
            roll_number += 1
            print(tc("  Re-rolling...", "sys"))

        # ── Spell selection for sorcerers ─────────────────────────────────────
        if char_class == CharClass.SORCERER:
            print()
            print(tc("  ┌─────────────────────────────────────────────────┐", "border"))
            print(tc("  │  Choose your starting spell:                    │", "title"))
            print(tc("  ├─────────────────────────────────────────────────┤", "border"))
            spell_keys = list(SPELL_DEFS.keys())
            for i, key in enumerate(spell_keys, 1):
                s = SPELL_DEFS[key]
                cost_str = f"({s['cost']} mana)"
                print(tc(f"  │  {i}. {s['name']:<12} {cost_str:<10} {s['desc']:<17}│", "stat"))
            print(tc(f"  └─────────────────────────────────────────────────┘", "border"))
            print()

            while True:
                raw = input(tc("  Choose spell (1-4): ", "prompt")).strip()
                try:
                    idx = int(raw) - 1
                    if 0 <= idx < len(spell_keys):
                        ch.spells = [spell_keys[idx]]
                        chosen = SPELL_DEFS[spell_keys[idx]]["name"]
                        print(tc(f"\n  You have chosen: {chosen}", "sys"))
                        break
                except ValueError:
                    pass
                print(tc("  Please enter a number from the list.", "error"))

        ch.save()
        print(tc(f"\n  Character '{name}' saved. Good luck out there.", "sys"))
        return ch
