"""
world.py - Data classes for the adventure world.
Rooms, Artifacts, and the World loader.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional


# ── Artifact types ────────────────────────────────────────────────────────────

class ArtifactType:
    WEAPON      = "weapon"
    ARMOR       = "armor"
    CONTAINER   = "container"
    READABLE    = "readable"
    GENERIC     = "generic"
    LIGHT       = "light"


# ── Artifact ──────────────────────────────────────────────────────────────────

@dataclass
class Artifact:
    id: int
    name: str
    description: str
    room_id: Optional[int]          # None = in player inventory
    artifact_type: str = ArtifactType.GENERIC
    weight: int = 1                 # affects carrying
    is_container: bool = False
    is_open: bool = False
    contents: list[int] = field(default_factory=list)   # artifact ids inside
    read_text: Optional[str] = None # for READABLE type
    # weapon stats
    damage_dice: int = 1
    damage_sides: int = 4
    # armor stats
    armor_class: int = 0

    # Synonyms the parser can match
    synonyms: list[str] = field(default_factory=list)

    def matches(self, word: str) -> bool:
        word = word.lower()
        if word in self.name.lower():
            return True
        return any(word in s.lower() for s in self.synonyms)

    def short_desc(self) -> str:
        return f"  {self.name}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "room_id": self.room_id,
            "artifact_type": self.artifact_type,
            "weight": self.weight,
            "is_container": self.is_container,
            "is_open": self.is_open,
            "contents": self.contents,
            "read_text": self.read_text,
            "damage_dice": self.damage_dice,
            "damage_sides": self.damage_sides,
            "armor_class": self.armor_class,
            "synonyms": self.synonyms,
        }

    @staticmethod
    def from_dict(d: dict) -> "Artifact":
        return Artifact(
            id=d["id"],
            name=d["name"],
            description=d["description"],
            room_id=d.get("room_id"),
            artifact_type=d.get("artifact_type", ArtifactType.GENERIC),
            weight=d.get("weight", 1),
            is_container=d.get("is_container", False),
            is_open=d.get("is_open", False),
            contents=d.get("contents", []),
            read_text=d.get("read_text"),
            damage_dice=d.get("damage_dice", 1),
            damage_sides=d.get("damage_sides", 4),
            armor_class=d.get("armor_class", 0),
            synonyms=d.get("synonyms", []),
        )


# ── Room ──────────────────────────────────────────────────────────────────────

DIRECTIONS = ["north", "south", "east", "west", "up", "down"]
DIR_ABBREV = {"n": "north", "s": "south", "e": "east",
              "w": "west", "u": "up", "d": "down"}

@dataclass
class Room:
    id: int
    name: str
    description: str
    exits: dict[str, int] = field(default_factory=dict)  # dir -> room_id
    is_dark: bool = False
    first_visit: bool = True   # track if player has been here

    def exit_list(self) -> str:
        if not self.exits:
            return "none"
        return ", ".join(self.exits.keys())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "exits": self.exits,
            "is_dark": self.is_dark,
        }

    @staticmethod
    def from_dict(d: dict) -> "Room":
        return Room(
            id=d["id"],
            name=d["name"],
            description=d["description"],
            exits=d.get("exits", {}),
            is_dark=d.get("is_dark", False),
        )


# ── World ─────────────────────────────────────────────────────────────────────

class World:
    """Holds all rooms and artifacts for one adventure."""

    def __init__(self):
        self.title: str = "Untitled Adventure"
        self.intro: str = ""
        self.author: str = "Unknown"
        self.start_room: int = 1
        self.rooms: dict[int, Room] = {}
        self.artifacts: dict[int, Artifact] = {}

    # ── Lookup helpers ────────────────────────────────────────────────────────

    def get_room(self, room_id: int) -> Optional[Room]:
        return self.rooms.get(room_id)

    def artifacts_in_room(self, room_id: int) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.room_id == room_id]

    def artifacts_carried(self) -> list[Artifact]:
        return [a for a in self.artifacts.values() if a.room_id is None]

    def find_artifact_by_name(self, word: str,
                               candidates: Optional[list[Artifact]] = None) -> Optional[Artifact]:
        pool = candidates if candidates is not None else list(self.artifacts.values())
        for a in pool:
            if a.matches(word):
                return a
        return None

    def next_room_id(self) -> int:
        return max(self.rooms.keys(), default=0) + 1

    def next_artifact_id(self) -> int:
        return max(self.artifacts.keys(), default=0) + 1

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        """Save world to a directory of JSON files."""
        import os
        os.makedirs(path, exist_ok=True)

        adventure_meta = {
            "title": self.title,
            "intro": self.intro,
            "author": self.author,
            "start_room": self.start_room,
        }
        with open(os.path.join(path, "adventure.json"), "w") as f:
            json.dump(adventure_meta, f, indent=2)

        with open(os.path.join(path, "rooms.json"), "w") as f:
            json.dump([r.to_dict() for r in self.rooms.values()], f, indent=2)

        with open(os.path.join(path, "artifacts.json"), "w") as f:
            json.dump([a.to_dict() for a in self.artifacts.values()], f, indent=2)

    @staticmethod
    def load(path: str) -> "World":
        """Load world from a directory of JSON files."""
        import os
        w = World()

        meta_path = os.path.join(path, "adventure.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            w.title = meta.get("title", "Untitled")
            w.intro = meta.get("intro", "")
            w.author = meta.get("author", "Unknown")
            w.start_room = meta.get("start_room", 1)

        rooms_path = os.path.join(path, "rooms.json")
        if os.path.exists(rooms_path):
            with open(rooms_path) as f:
                for rd in json.load(f):
                    r = Room.from_dict(rd)
                    w.rooms[r.id] = r

        artifacts_path = os.path.join(path, "artifacts.json")
        if os.path.exists(artifacts_path):
            with open(artifacts_path) as f:
                for ad in json.load(f):
                    a = Artifact.from_dict(ad)
                    w.artifacts[a.id] = a

        return w
