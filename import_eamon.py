"""
import_eamon.py — Import an Eamon Deluxe (EDX) JSON fixture into Eamon Redux.

Usage:
    python3 import_eamon.py <source.json> [adventure_slug]

The source file is a Django fixture dump from the EDX web app.
Creates adventures/<slug>/ with adventure.json, rooms.json,
artifacts.json, and monsters.json.

Items needing manual follow-up are reported at the end.
"""

import json
import os
import re
import sys
from collections import defaultdict

# ── Type mappings ─────────────────────────────────────────────────────────────

# EDX numeric artifact type → Eamon Redux artifact_type string
ARTIFACT_TYPE_MAP = {
    0:  "generic",    # treasure / gold
    1:  "generic",    # misc item (key, tool, fixture)
    2:  "weapon",     # melee weapon
    3:  "weapon",     # magic weapon (same combat mechanics)
    4:  "container",  # container / sack
    5:  "light",      # light source
    6:  "potion",     # drinkable
    7:  "readable",   # book / scroll / leaflet
    8:  "generic",    # door / grate (adventure-specific logic)
    9:  "food",       # edible
    10: "generic",    # bound captive (complex — flag for manual review)
    11: "armor",      # wearable armour
    12: "generic",    # dead body shell
    13: "generic",    # dead body / loot placeholder
}

# EDX types that are always immovable scenery — never carriable
_IMMOVABLE_TYPES = {8, 10, 12, 13}

# EDX weapon_type integer → Eamon Redux weapon type string
WEAPON_TYPE_MAP = {
    1: "axe",
    2: "bow",
    3: "club",
    4: "spear",
    5: "sword",
}

# EDX direction abbreviation → full word
DIR_MAP = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "u": "up",    "d": "down",
    "ne": "northeast", "nw": "northwest",
    "se": "southeast", "sw": "southwest",
}

# EDX monster friendliness → Eamon Redux attitude
ATTITUDE_MAP = {
    "hostile": "hostile",
    "friend":  "friendly",
    "random":  "neutral",
    "neutral": "neutral",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def _by_model(data: list) -> dict:
    groups = defaultdict(list)
    for rec in data:
        groups[rec["model"]].append(rec)
    return groups

# ── Converters ────────────────────────────────────────────────────────────────

def convert_adventure(rec: dict) -> dict:
    f = rec["fields"]
    return {
        "title":       f["name"],
        "author":      "",          # resolved separately from adventure.author
        "intro_text":  f.get("intro_text", "").replace("\r\n", "\n"),
        "is_beginner_adventure": False,
    }

def convert_rooms(room_recs: list, exit_recs: list) -> list:
    # Build pk → room_id lookup
    pk_to_rid = {r["pk"]: r["fields"]["room_id"] for r in room_recs}

    # Group exits by source room_id
    exits_by_rid = defaultdict(dict)
    for ex in exit_recs:
        f = ex["fields"]
        src_rid = pk_to_rid.get(f["room_from"])
        if src_rid is None:
            continue
        direction = DIR_MAP.get(f["direction"], f["direction"])
        dest_rid  = f["room_to"]
        exits_by_rid[src_rid][direction] = dest_rid

    rooms = []
    for rec in sorted(room_recs, key=lambda r: r["fields"]["room_id"]):
        f   = rec["fields"]
        rid = f["room_id"]
        rooms.append({
            "id":               rid,
            "name":             f"You are {f['name']}",
            "description":      f["description"],
            "brief_description": "",
            "exits":            exits_by_rid.get(rid, {}),
            "is_dark":          f.get("is_dark", False),
        })
    return rooms

def convert_artifacts(artifact_recs: list) -> tuple[list, list, dict]:
    """Returns (artifacts, warnings, monster_loot_map).

    monster_loot_map: {monster_id: artifact_id} for artifacts whose
    monster_id field is set — consumed by convert_monsters to wire loot.
    """
    artifacts        = []
    warnings         = []
    monster_loot_map = {}   # monster_id → artifact_id

    for rec in sorted(artifact_recs, key=lambda r: r["fields"]["artifact_id"]):
        f   = rec["fields"]
        aid = f["artifact_id"]
        edx_type = f.get("type", 1)
        atype    = ARTIFACT_TYPE_MAP.get(edx_type, "generic")

        # Determine weapon sub-type for weapons
        weapon_type = None
        if atype == "weapon":
            wt_code = f.get("weapon_type")
            weapon_type = WEAPON_TYPE_MAP.get(wt_code, "sword")

        # Placement — auto-wire monster loot; only warn for containers/captives
        room_id    = f.get("room_id")
        monster_id = f.get("monster_id")
        if monster_id and not room_id:
            monster_loot_map[monster_id] = aid
        if f.get("container_id") and not room_id:
            warnings.append(
                f"  Artifact #{aid} '{f['name']}' is inside container #{f['container_id']} "
                f"— place manually."
            )
        if edx_type == 10:
            warnings.append(
                f"  Artifact #{aid} '{f['name']}' is a bound captive (type 10) "
                f"— convert to NPC/monster manually."
            )

        # Damage / heal fields
        dice  = f.get("dice")  or 1
        sides = f.get("sides") or 4
        hp    = 0
        if edx_type == 6:   # drinkable → heal amount (sides field used as qty)
            hp = max(1, (f.get("quantity") or 0))
        elif edx_type == 9:  # edible food
            hp = sides or 4

        # Armor class
        ac = f.get("armor_class") or 0

        raw_weight = max(0, f.get("weight") or 0)
        raw_value  = f.get("value") or 0

        # Immovable if: always-scenery EDX type, OR weightless/valueless generic
        # (doors, dead bodies, bound captives, fixtures that shouldn't be carried)
        immovable = (
            edx_type in _IMMOVABLE_TYPES
            or (edx_type in (0, 1) and raw_weight == 0 and raw_value == 0)
        )

        artifact = {
            "id":            aid,
            "name":          f["name"],
            "description":   f["description"],
            "artifact_type": atype,
            "room_id":       room_id,
            "weight":        999 if immovable else raw_weight,
            "value":         raw_value,
            "is_quest_item": immovable,
            "heal_amount":   hp,
            "armor_class":   ac,
            "damage_dice":   int(dice)  if dice  is not None else 1,
            "damage_sides":  int(sides) if sides is not None else 4,
        }
        if weapon_type:
            artifact["weapon_type"] = weapon_type
        if f.get("synonyms"):
            artifact["synonyms"] = [s.strip() for s in f["synonyms"].split(",")]

        artifacts.append(artifact)

    return artifacts, warnings, monster_loot_map

def convert_monsters(monster_recs: list, monster_loot_map: dict) -> tuple[list, list]:
    """Returns (monsters, warnings)."""
    monsters = []
    warnings = []

    for rec in sorted(monster_recs, key=lambda r: r["fields"]["monster_id"]):
        f   = rec["fields"]
        mid = f["monster_id"]

        room_id = f.get("room_id")
        if not room_id:
            warnings.append(
                f"  Monster #{mid} '{f['name']}' has no room — "
                f"place manually (may be in a container or triggered by script)."
            )

        attitude = ATTITUDE_MAP.get(f.get("friendliness", "hostile"), "hostile")

        entry = {
            "id":           mid,
            "name":         f["name"],
            "description":  f["description"],
            "room_id":      room_id,
            "attitude":     attitude,
            "hp":           f.get("hardiness", 10),
            "agility":      f.get("agility", 10),
            "armor_class":  f.get("armor_class", 0),
            "damage_dice":  f.get("weapon_dice", 1),
            "damage_sides": f.get("weapon_sides", 4),
            "xp":           f.get("hardiness", 10),
            "dialogue":     "",
            "death_message": "",
        }
        if mid in monster_loot_map:
            entry["loot_id"] = monster_loot_map[mid]
        monsters.append(entry)

    return monsters, warnings

# ── Main ──────────────────────────────────────────────────────────────────────

def import_adventure(src_path: str, slug: str | None = None,
                     dest_dir: str = "adventures") -> str:
    """
    Parse src_path and write adventure files to dest_dir/<slug>/.
    Returns the adventure directory path.
    """
    with open(src_path, encoding="utf-8") as f:
        data = json.load(f)

    groups = _by_model(data)

    # ── Metadata ──────────────────────────────────────────────────────────────
    adv_rec  = groups["adventure.adventure"][0]
    adv_meta = convert_adventure(adv_rec)

    # Resolve author name
    author_recs = groups.get("adventure.author", [])
    if author_recs:
        adv_meta["author"] = author_recs[0]["fields"]["name"]

    if not slug:
        slug = adv_rec["fields"].get("slug") or _slug(adv_meta["title"])

    adv_dir = os.path.join(dest_dir, slug)
    os.makedirs(adv_dir, exist_ok=True)

    # ── Rooms ─────────────────────────────────────────────────────────────────
    rooms = convert_rooms(
        groups.get("adventure.room",     []),
        groups.get("adventure.roomexit", []),
    )
    # Set start_room to first room
    if rooms:
        adv_meta["start_room"] = rooms[0]["id"]

    # ── Artifacts ─────────────────────────────────────────────────────────────
    artifacts, art_warnings, monster_loot_map = convert_artifacts(
        groups.get("adventure.artifact", [])
    )

    # ── Monsters ──────────────────────────────────────────────────────────────
    monsters, mon_warnings = convert_monsters(
        groups.get("adventure.monster", []), monster_loot_map
    )

    # ── Write files ───────────────────────────────────────────────────────────
    def _write(filename, obj):
        path = os.path.join(adv_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        return path

    _write("adventure.json", adv_meta)
    _write("rooms.json",     rooms)
    _write("artifacts.json", artifacts)
    _write("monsters.json",  monsters)

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n  Imported: {adv_meta['title']}")
    print(f"  Output  : {adv_dir}/")
    print(f"  Rooms   : {len(rooms)}")
    print(f"  Artifacts: {len(artifacts)}")
    print(f"  Monsters : {len(monsters)}")

    all_warnings = art_warnings + mon_warnings
    if all_warnings:
        print(f"\n  {len(all_warnings)} item(s) need manual attention:")
        for w in all_warnings:
            print(w)
    else:
        print("\n  No manual follow-up needed.")

    print()
    return adv_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 import_eamon.py <source.json> [adventure_slug]")
        sys.exit(1)
    src  = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else None
    import_adventure(src, slug)
