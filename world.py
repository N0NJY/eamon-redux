"""
world.py - Data classes for the adventure world (UPDATED).
Added weapon type constants for the proficiency system.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional


# ── Weapon Types ──────────────────────────────────────────────────────────────

class WeaponType:
    AXE    = "axe"
    BOW    = "bow"
    CLUB   = "club"
    SPEAR  = "spear"
    SWORD  = "sword"


# ── Artifact Types ────────────────────────────────────────────────────────────

class ArtifactType:
    WEAPON    = "weapon"
    ARMOR     = "armor"
    CONTAINER = "container"
    READABLE  = "readable"
    GENERIC   = "generic"
    LIGHT     = "light"
    KEY       = "key"
    FOOD      = "food"      # EAT to restore heal_amount HP
    POTION    = "potion"    # DRINK to restore heal_amount HP
    SPELLBOOK = "spellbook" # READ to learn a spell
    SHIELD    = "shield"    # equippable in shield slot
    RING      = "ring"      # equippable in ring slot
    CLOAK     = "cloak"     # equippable in cloak slot


class Attitude:
    HOSTILE  = "hostile"
    NEUTRAL  = "neutral"
    FRIENDLY = "friendly"


# ── Artifact ──────────────────────────────────────────────────────────────────

@dataclass
class Artifact:
    id: int
    name: str
    description: str
    room_id: Optional[int]
    artifact_type: str = ArtifactType.GENERIC
    weight: int = 1
    is_container: bool = False
    is_open: bool = False
    contents: list[int] = field(default_factory=list)
    read_text: Optional[str] = None
    damage_dice: int = 1
    damage_sides: int = 4
    armor_class: int = 0
    heal_amount: int = 0    # for FOOD and POTION
    value: int = -1         # sell price (-1 = use type default)
    is_quest_item: bool = False  # quest items and keys cannot be sold
    synonyms: list[str] = field(default_factory=list)
    weapon_type: Optional[str] = None  # for weapons: axe, bow, club, spear, sword
    stat_bonuses: dict = field(default_factory=dict)  # e.g. {"intelligence": 2}
    flags: dict = field(default_factory=dict)

    def matches(self, word: str) -> bool:
        word = word.lower()
        if word in self.name.lower():
            return True
        return any(word in s.lower() for s in self.synonyms)

    def to_dict(self) -> dict:
        d = {
            "id": self.id, "name": self.name, "description": self.description,
            "room_id": self.room_id, "artifact_type": self.artifact_type,
            "weight": self.weight, "is_container": self.is_container,
            "is_open": self.is_open, "contents": self.contents,
            "read_text": self.read_text, "damage_dice": self.damage_dice,
            "damage_sides": self.damage_sides, "armor_class": self.armor_class,
            "heal_amount": self.heal_amount, "value": self.value,
            "is_quest_item": self.is_quest_item, "synonyms": self.synonyms,
            "flags": self.flags,
        }
        if self.weapon_type:
            d["weapon_type"] = self.weapon_type
        if self.stat_bonuses:
            d["stat_bonuses"] = self.stat_bonuses
        return d

    @staticmethod
    def from_dict(d: dict) -> "Artifact":
        return Artifact(
            id=d["id"], name=d["name"], description=d["description"],
            room_id=d.get("room_id"),
            artifact_type=d.get("artifact_type", ArtifactType.GENERIC),
            weight=d.get("weight", 1), is_container=d.get("is_container", False),
            is_open=d.get("is_open", False), contents=d.get("contents", []),
            read_text=d.get("read_text"), damage_dice=d.get("damage_dice", 1),
            damage_sides=d.get("damage_sides", 4),
            armor_class=d.get("armor_class", 0),
            heal_amount=d.get("heal_amount", 0),
            value=d.get("value", -1),
            is_quest_item=d.get("is_quest_item", False),
            synonyms=d.get("synonyms", []),
            weapon_type=d.get("weapon_type"),
            stat_bonuses=d.get("stat_bonuses", {}),
            flags=d.get("flags", {}),
        )


# ── Monster ───────────────────────────────────────────────────────────────────

@dataclass
class Monster:
    id: int
    name: str
    description: str
    room_id: int
    attitude: str = Attitude.HOSTILE
    hp: int = 10
    hp_max: int = 10
    damage_dice: int = 1
    damage_sides: int = 6
    armor_class: int = 0
    loot_id: int = 0
    xp_value: int = 0       # XP awarded on kill (0 = auto-calculated)
    death_message: str = ""
    dialogue: str = ""       # spoken when player talks to NPC
    heal_amount: int = 0     # HP the NPC can restore per use (0 = no healing)
    heal_cost: int = 0       # gold cost per HP healed
    synonyms: list[str] = field(default_factory=list)
    flags: dict = field(default_factory=dict)

    is_alive: bool = field(default=True, init=False)
    aggro: bool = field(default=False, init=False)

    def __post_init__(self):
        self.is_alive = self.hp > 0
        self.aggro = self.attitude == Attitude.HOSTILE

    def matches(self, word: str) -> bool:
        word = word.lower()
        if word in self.name.lower():
            return True
        return any(word in s.lower() for s in self.synonyms)

    def health_desc(self) -> str:
        pct = self.hp / self.hp_max
        if pct >= 0.75: return "looks healthy"
        elif pct >= 0.50: return "is wounded"
        elif pct >= 0.25: return "is badly hurt"
        else: return "is near death"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "room_id": self.room_id, "attitude": self.attitude, "hp": self.hp_max,
            "damage_dice": self.damage_dice, "damage_sides": self.damage_sides,
            "armor_class": self.armor_class, "loot_id": self.loot_id,
            "death_message": self.death_message, "dialogue": self.dialogue,
            "heal_amount": self.heal_amount, "heal_cost": self.heal_cost,
            "synonyms": self.synonyms, "xp_value": self.xp_value,
            "flags": self.flags,
        }

    @staticmethod
    def from_dict(d: dict) -> "Monster":
        hp = d.get("hp", 10)
        return Monster(
            id=d["id"], name=d["name"], description=d["description"],
            room_id=d["room_id"], attitude=d.get("attitude", Attitude.HOSTILE),
            hp=hp, hp_max=hp, damage_dice=d.get("damage_dice", 1),
            damage_sides=d.get("damage_sides", 6),
            armor_class=d.get("armor_class", 0), loot_id=d.get("loot_id", 0),
            death_message=d.get("death_message", ""),
            dialogue=d.get("dialogue", ""),
            heal_amount=d.get("heal_amount", 0),
            heal_cost=d.get("heal_cost", 0),
            synonyms=d.get("synonyms", []),
            xp_value=d.get("xp_value", 0),
            flags=d.get("flags", {}),
        )


# ── Room ──────────────────────────────────────────────────────────────────────

DIRECTIONS = ["north", "south", "east", "west", "up", "down",
              "northeast", "northwest", "southeast", "southwest"]
DIR_ABBREV = {"n": "north",     "s": "south",     "e": "east",
              "w": "west",      "u": "up",         "d": "down",
              "ne": "northeast", "nw": "northwest",
              "se": "southeast", "sw": "southwest"}

@dataclass
class Room:
    id: int
    name: str
    description: str
    brief_description: str = ""
    exits: dict[str, int] = field(default_factory=dict)
    locked_exits: dict[str, int] = field(default_factory=dict)
    is_dark: bool = False
    first_visit: bool = True
    flags: dict = field(default_factory=dict)

    def exit_list(self) -> str:
        if not self.exits:
            return "none"
        return ", ".join(self.exits.keys())

    def to_dict(self) -> dict:
        d = {
            "id": self.id, "name": self.name, "description": self.description,
            "brief_description": self.brief_description,
            "exits": self.exits, "is_dark": self.is_dark,
            "first_visit": self.first_visit,
        }
        if self.locked_exits:
            d["locked_exits"] = self.locked_exits
        if self.flags:
            d["flags"] = self.flags
        return d

    @staticmethod
    def from_dict(d: dict) -> "Room":
        return Room(
            id=d["id"], name=d["name"], description=d["description"],
            brief_description=d.get("brief_description", ""),
            exits=d.get("exits", {}),
            locked_exits=d.get("locked_exits", {}),
            is_dark=d.get("is_dark", False),
            first_visit=d.get("first_visit", True),
            flags=d.get("flags", {}),
        )


# ── World ─────────────────────────────────────────────────────────────────────

class World:
    def __init__(self):
        self.title: str = "Untitled Adventure"
        self.intro: str = ""
        self.author: str = "Unknown"
        self.start_room: int = 1
        self.rooms: dict[int, Room] = {}
        self.artifacts: dict[int, Artifact] = {}
        self.monsters: dict[int, Monster] = {}
        self.win_condition: dict = {}

    def get_room(self, room_id: int) -> Optional[Room]:
        return self.rooms.get(room_id)

    def artifacts_in_room(self, room_id: int) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.room_id == room_id]

    def artifacts_carried(self) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.room_id is None]

    def find_artifact_by_name(self, word: str, candidates=None) -> Optional[Artifact]:
        pool = candidates if candidates is not None else list(self.artifacts.values())
        for a in pool:
            if a.matches(word):
                return a
        return None

    def monsters_in_room(self, room_id: int) -> list[Monster]:
        return [m for m in self.monsters.values()
                if m.room_id == room_id and m.is_alive]

    def find_monster_by_name(self, word: str, candidates=None) -> Optional[Monster]:
        pool = candidates if candidates is not None else list(self.monsters.values())
        for m in pool:
            if m.is_alive and m.matches(word):
                return m
        return None

    def next_room_id(self) -> int:
        return max(self.rooms.keys(), default=0) + 1

    def next_artifact_id(self) -> int:
        return max(self.artifacts.keys(), default=0) + 1

    def next_monster_id(self) -> int:
        return max(self.monsters.keys(), default=0) + 1

    def save(self, path: str) -> None:
        import os
        os.makedirs(path, exist_ok=True)
        meta = {
            "title": self.title, "intro": self.intro,
            "author": self.author, "start_room": self.start_room,
        }
        if self.win_condition:
            meta["win_condition"] = self.win_condition
        with open(os.path.join(path, "adventure.json"), "w") as f:
            json.dump(meta, f, indent=2)
        with open(os.path.join(path, "rooms.json"), "w") as f:
            json.dump([r.to_dict() for r in self.rooms.values()], f, indent=2)
        with open(os.path.join(path, "artifacts.json"), "w") as f:
            json.dump([a.to_dict() for a in self.artifacts.values()], f, indent=2)
        with open(os.path.join(path, "monsters.json"), "w") as f:
            json.dump([m.to_dict() for m in self.monsters.values()], f, indent=2)

    @staticmethod
    def load(path: str) -> "World":
        import os
        w = World()
        meta_path = os.path.join(path, "adventure.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            w.title      = meta.get("title", "Untitled")
            w.intro      = meta.get("intro", "")
            w.author     = meta.get("author", "Unknown")
            w.start_room = meta.get("start_room", 1)
            w.win_condition = meta.get("win_condition", {})
        for fname, loader, store in [
            ("rooms.json",     Room.from_dict,     w.rooms),
            ("artifacts.json", Artifact.from_dict, w.artifacts),
            ("monsters.json",  Monster.from_dict,  w.monsters),
        ]:
            fpath = os.path.join(path, fname)
            if os.path.exists(fpath):
                with open(fpath) as f:
                    for d in json.load(f):
                        obj = loader(d)
                        store[obj.id] = obj
        return w
