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
    "blast":  {"name": "Blast",  "cost": 3000, "mana_cost": 3, "desc": "1D6 damage, bypasses armor"},
    "heal":   {"name": "Heal",   "cost": 1000, "mana_cost": 2, "desc": "1D10 HP restore"},
    "speed":  {"name": "Speed",  "cost": 5000, "mana_cost": 5, "desc": "Double Agility for 11-20 rounds"},
    "power":  {"name": "Power",  "cost": 100,  "mana_cost": 1, "desc": "Adventure-specific effect"},
}

FIGHTER_ALLOWED_SPELLS = {"heal"}

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
    character_class: str = "fighter"  # "fighter" or "sorcerer"

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
        """Return a clean, fully-bordered character sheet."""
        W = 54  # inner width between ║ chars

        def top():      return f"  ╔{'═'*W}╗"
        def bot():      return f"  ╚{'═'*W}╝"
        def sep():      return f"  ╠{'═'*W}╣"
        def row(s=""):  return f"  ║  {s:<{W-2}}║"
        def hdr(s):     return f"  ║  {s.upper():<{W-2}}║"

        # ── Header ───────────────────────────────────────────────────────────
        class_tag = f"[ {self.character_class.capitalize()} ]"
        name_col  = W - 2 - len(class_tag) - 1
        lines = [
            "",
            top(),
            f"  ║  {self.name:<{name_col}}{class_tag} ║",
            sep(),
        ]

        # ── Core Stats ───────────────────────────────────────────────────────
        lines.append(hdr("Core Stats"))
        lines.append(sep())

        def stat(label, val, right=""):
            left = f"{label:<13}: {val:<3}"
            return row(f"{left}   {right}" if right else left)

        lines += [
            stat("Hardiness",    self.hardiness,    f"HP:  {self.hp}/{self.hp_max}   Carry: {self.carry_capacity} gronds"),
            stat("Agility",      self.agility,      f"Combat bonus: {self.agility_bonus:+d}"),
            stat("Strength",     self.strength,     f"Damage bonus: {self.strength_bonus:+d}"),
            stat("Intelligence", self.intelligence,  f"Mana: {self.mana_max}"),
            stat("Charisma",     self.charisma,     f"Reaction:    {self.charisma_bonus:+d}"),
        ]

        # ── Weapon Skills ─────────────────────────────────────────────────────
        lines.append(sep())
        lines.append(hdr("Weapon Skills"))
        lines.append(sep())

        def fmt_wpn(name, prof):
            return f"{name:<5}: {prof:>4}%"

        weapons = [(WEAPON_TYPES[k]["name"], v)
                   for k, v in self.weapon_proficiencies.items()
                   if k in WEAPON_TYPES]
        for i in range(0, len(weapons), 3):
            group = weapons[i:i+3]
            lines.append(row("   ".join(fmt_wpn(n, p) for n, p in group)))

        # ── Spells ───────────────────────────────────────────────────────────
        lines.append(sep())
        lines.append(hdr("Spells"))
        lines.append(sep())

        def fmt_spell(name, prof):
            val = f"{prof:>3}%" if prof is not None else " --"
            return f"{name:<5}: {val}"

        spells = [(SPELL_DEFS[k]["name"], v)
                  for k, v in self.spell_proficiencies.items()]
        for i in range(0, len(spells), 3):
            group = spells[i:i+3]
            lines.append(row("   ".join(fmt_spell(n, p) for n, p in group)))

        # ── Progression ───────────────────────────────────────────────────────
        lines.append(sep())
        lines.append(hdr("Progression"))
        lines.append(sep())
        status = "Beginner" if self.is_beginner else "Veteran"
        lines.append(row(f"Level: {self.level}   XP: {self.xp}   Gold: {self.gold}g   {status}"))
        if self.adventures_completed:
            lines.append(row(f"Completed: {', '.join(self.adventures_completed)}"))

        # ── Equipped ─────────────────────────────────────────────────────────
        lines.append(sep())
        lines.append(hdr("Equipped"))
        lines.append(sep())

        active = {s: n for s, n in self.equipped.items() if n}
        if active:
            items = list(active.items())
            for i in range(0, len(items), 2):
                s1, n1 = items[i]
                left = f"{s1.capitalize():<8}: {n1}"
                if i + 1 < len(items):
                    s2, n2 = items[i + 1]
                    right = f"{s2.capitalize():<8}: {n2}"
                    lines.append(row(f"{left:<26}{right}"))
                else:
                    lines.append(row(left))
        else:
            lines.append(row("(nothing equipped)"))

        lines += [bot(), ""]
        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> None:
        os.makedirs(CHARACTERS_DIR, exist_ok=True)
        with open(self._path(self.name), "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "character_class": self.character_class,
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
            character_class=d.get("character_class", "fighter"),
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

        # ── Class selection ───────────────────────────────────────────────────
        print()
        print(tc("  ┌─────────────────────────────────────────────────┐", "border"))
        print(tc("  │  Choose your class:                             │", "title"))
        print(tc("  ├─────────────────────────────────────────────────┤", "border"))
        print(tc("  │  F) Fighter  — strength, weapons, armor         │", "stat"))
        print(tc("  │               Strength bonus to melee damage    │", "desc"))
        print(tc("  │               Cannot learn most spells          │", "desc"))
        print(tc("  │                                                 │", "border"))
        print(tc("  │  S) Sorcerer — magic, intelligence, spells      │", "stat"))
        print(tc("  │               Intelligence bonus to spells      │", "desc"))
        print(tc("  │               Mana pool for casting             │", "desc"))
        print(tc("  │               Starts with one chosen spell      │", "desc"))
        print(tc("  └─────────────────────────────────────────────────┘", "border"))
        print()
        while True:
            cls_input = input(tc("  Class (F/S): ", "prompt")).strip().lower()
            if cls_input in ("f", "fighter"):
                character_class = "fighter"
                break
            elif cls_input in ("s", "sorcerer"):
                character_class = "sorcerer"
                break
            print(tc("  Enter F for Fighter or S for Sorcerer.", "warn"))

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
                character_class=character_class,
                hardiness=hardiness, agility=agility, charisma=charisma,
                intelligence=intelligence, strength=strength,
            )
            ch.hp = ch.hp_max

            print()
            print(tc(f"  ┌─────────────────────────────────────────────────┐", "border"))
            print(tc(f"  │  {name}{'':<{49 - len(name)}}│", "title"))
            print(tc(f"  │  Class: {character_class.capitalize():<41}│", "stat"))
            print(tc(f"  │  Roll #{roll_number:<42}│", "desc"))
            print(tc(f"  ├─────────────────────────────────────────────────┤", "border"))
            print(tc(f"  │  Hardiness    : {hardiness:<3}  HP: {ch.hp_max:<18}│", "stat"))
            print(tc(f"  │  Agility      : {agility:<3}  (combat bonus: {ch.agility_bonus:+d}){'':<10}│", "stat"))
            print(tc(f"  │  Strength     : {strength:<3}  (damage bonus: {ch.strength_bonus:+d}){'':<11}│", "stat"))
            print(tc(f"  │  Intelligence : {intelligence:<3}  (spell bonus: {ch.intelligence_bonus:+d}){'':<11}│", "stat"))
            print(tc(f"  │  Charisma     : {charisma:<3}  (reaction: {ch.charisma_bonus:+d}){'':<13}│", "stat"))
            if character_class == "sorcerer":
                mana = ch.mana_max
                print(tc(f"  │  Mana         : {mana:<3}  (Intelligence × 2){'':<14}│", "stat"))
            print(tc(f"  │  Gold         : 200 (starting capital){'':<20}│", "stat"))
            print(tc(f"  └─────────────────────────────────────────────────┘", "border"))
            print()

            answer = input(tc("  Keep these stats? (y/n): ", "prompt")).strip().lower()
            if answer == "y":
                break
            roll_number += 1
            print(tc("  Re-rolling...", "sys"))

        # ── Sorcerer starting spell ───────────────────────────────────────────
        if character_class == "sorcerer":
            print()
            print(tc("  Choose your starting spell:", "title"))
            spell_options = list(SPELL_DEFS.items())
            for i, (key, sp) in enumerate(spell_options, 1):
                print(tc(f"  {i}) {sp['name']:<12} — {sp['desc']}", "stat"))
            print()
            while True:
                try:
                    choice = int(input(tc("  Starting spell (1-4): ", "prompt")).strip())
                    if 1 <= choice <= len(spell_options):
                        spell_key = spell_options[choice - 1][0]
                        starting_prof = random.randint(25, 75)
                        ch.spell_proficiencies[spell_key] = starting_prof
                        print(tc(f"  You begin with {SPELL_DEFS[spell_key]['name']} at {starting_prof}% proficiency.", "sys"))
                        break
                except ValueError:
                    pass
                print(tc(f"  Enter a number from 1 to {len(spell_options)}.", "warn"))

        ch.save()
        print(tc(f"\n  Character '{name}' saved. Starting with 200 gold.", "sys"))
        if character_class == "sorcerer":
            print(tc(f"  Visit Aldric in the tavern to learn more spells!", "sys"))
        else:
            print(tc(f"  Visit Horace in the tavern to buy weapons and armor!", "sys"))
        return ch
