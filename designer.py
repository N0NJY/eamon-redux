"""
designer.py - Adventure Designer Tool

Two modes:
  Menu mode  - create/edit rooms, artifacts, and monsters via numbered menus
  Map mode   - display ASCII grid map of room connections
"""

from __future__ import annotations
import json
import os
import sys
from world import World, Room, Artifact, ArtifactType, Monster, Attitude, DIRECTIONS

# ── Utilities ─────────────────────────────────────────────────────────────────

def cls():
    os.system("cls" if os.name == "nt" else "clear")

def hr(char="─", width=72):
    return char * width

def prompt(label: str, default: str = "") -> str:
    if default:
        val = input(f"  {label} [{default}]: ").strip()
        return val if val else default
    else:
        return input(f"  {label}: ").strip()

def prompt_int(label: str, default: int = 0) -> int:
    while True:
        raw = input(f"  {label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print("    Please enter a number.")

def prompt_bool(label: str, default: bool = False) -> bool:
    d = "Y/n" if default else "y/N"
    raw = input(f"  {label} [{d}]: ").strip().lower()
    if not raw:
        return default
    return raw.startswith("y")

def choose(items: list[str], title: str = "Choose") -> int:
    """Present a numbered list; return 1-based index or 0 to cancel."""
    print(f"\n  {title}")
    print(f"  {hr('─', 40)}")
    for i, item in enumerate(items, 1):
        print(f"  {i:>3}. {item}")
    print(f"    0. Cancel")
    while True:
        raw = input("  > ").strip()
        try:
            n = int(raw)
            if 0 <= n <= len(items):
                return n
        except ValueError:
            pass
        print("  Invalid choice.")


# ══════════════════════════════════════════════════════════════════════════════
# ASCII MAP
# ══════════════════════════════════════════════════════════════════════════════

def render_map(world: World) -> None:
    """
    Lay out rooms on a 2D grid by following exits from the start room,
    then draw them with ASCII box-drawing characters.
    """
    if not world.rooms:
        print("  (no rooms to display)")
        return

    DELTAS = {
        "north": (0,  1),
        "south": (0, -1),
        "east":  (1,  0),
        "west":  (-1, 0),
    }
    pos: dict[int, tuple[int, int]] = {}
    start = world.start_room if world.start_room in world.rooms else next(iter(world.rooms))
    pos[start] = (0, 0)
    queue = [start]
    visited = {start}

    while queue:
        rid = queue.pop(0)
        room = world.rooms[rid]
        gx, gy = pos[rid]
        for direction, dest_id in room.exits.items():
            if dest_id not in world.rooms:
                continue
            if direction in DELTAS and dest_id not in visited:
                dx, dy = DELTAS[direction]
                candidate = (gx + dx, gy + dy)
                while candidate in pos.values():
                    candidate = (candidate[0] + dx, candidate[1] + dy)
                pos[dest_id] = candidate
                visited.add(dest_id)
                queue.append(dest_id)

    unreachable = [rid for rid in world.rooms if rid not in pos]
    col = 0
    min_y = min(y for _, y in pos.values()) - 2 if pos else 0
    for rid in unreachable:
        pos[rid] = (col, min_y)
        col += 1

    if not pos:
        print("  (nothing to display)")
        return

    min_gx = min(x for x, _ in pos.values())
    min_gy = min(y for _, y in pos.values())
    pos = {rid: (x - min_gx, y - min_gy) for rid, (x, y) in pos.items()}

    max_gx = max(x for x, _ in pos.values())
    max_gy = max(y for _, y in pos.values())

    CELL_W = 9
    CELL_H = 3

    cols_per_step = CELL_W + 3
    rows_per_step = CELL_H + 2

    grid_w = (max_gx + 1) * cols_per_step + 2
    grid_h = (max_gy + 1) * rows_per_step + 2

    canvas = [[" "] * grid_w for _ in range(grid_h)]

    def screen_xy(gx: int, gy: int) -> tuple[int, int]:
        sx = gx * cols_per_step
        sy = (max_gy - gy) * rows_per_step
        return sx, sy

    def put(x: int, y: int, ch: str) -> None:
        if 0 <= y < grid_h and 0 <= x < grid_w:
            canvas[y][x] = ch

    def put_str(x: int, y: int, s: str) -> None:
        for i, ch in enumerate(s):
            put(x + i, y, ch)

    def draw_box(sx: int, sy: int, label: str, room_id: int, is_start: bool) -> None:
        W = CELL_W + 2
        H = CELL_H + 2
        tl = "╔" if is_start else "┌"
        tr = "╗" if is_start else "┐"
        bl = "╚" if is_start else "└"
        br = "╝" if is_start else "┘"
        hz = "═" if is_start else "─"
        vt = "║" if is_start else "│"

        put(sx,       sy,       tl)
        put(sx + W-1, sy,       tr)
        put(sx,       sy + H-1, bl)
        put(sx + W-1, sy + H-1, br)

        for x in range(1, W-1):
            put(sx + x, sy,       hz)
            put(sx + x, sy + H-1, hz)
        for y in range(1, H-1):
            put(sx,       sy + y, vt)
            put(sx + W-1, sy + y, vt)

        inner_w = CELL_W
        id_str = f"#{room_id}"
        put_str(sx + 1, sy + 1, id_str[:inner_w].ljust(inner_w))
        put_str(sx + 1, sy + 2, label[:inner_w].ljust(inner_w))

    for rid, (gx, gy) in pos.items():
        sx, sy = screen_xy(gx, gy)
        room = world.rooms[rid]
        draw_box(sx, sy, room.name, rid, rid == world.start_room)

    CONN_DELTAS = {
        "north": (0,  1),
        "south": (0, -1),
        "east":  (1,  0),
        "west":  (-1, 0),
    }
    drawn_conns: set[frozenset] = set()

    for rid, (gx, gy) in pos.items():
        room = world.rooms[rid]
        sx, sy = screen_xy(gx, gy)
        BOX_W = CELL_W + 2
        BOX_H = CELL_H + 2

        for direction, dest_id in room.exits.items():
            if direction not in CONN_DELTAS:
                continue
            if dest_id not in pos:
                continue
            key = frozenset([rid, dest_id])
            already = key in drawn_conns
            drawn_conns.add(key)

            dx, dy = CONN_DELTAS[direction]

            if direction == "east":
                cx = sx + BOX_W
                cy = sy + BOX_H // 2
                put(cx, cy, "─")
                if not already:
                    put(cx + 1, cy, "─")
            elif direction == "west":
                cx = sx - 1
                cy = sy + BOX_H // 2
                put(cx, cy, "─")
                if not already:
                    put(cx - 1, cy, "─")
            elif direction == "north":
                cx = sx + BOX_W // 2
                cy = sy - 1
                put(cx, cy, "│")
                if not already:
                    put(cx, cy - 1, "│")
            elif direction == "south":
                cx = sx + BOX_W // 2
                cy = sy + BOX_H
                put(cx, cy, "│")
                if not already:
                    put(cx, cy + 1, "│")

    print()
    for row in canvas:
        line = "".join(row).rstrip()
        if line:
            print("  " + line)

    print()
    print(f"  ╔═ Start room   ┌─ Regular room")
    if unreachable:
        print(f"  Rooms without N/S/E/W connections shown at bottom.")

    ud_lines = []
    for rid, room in world.rooms.items():
        for d in ("up", "down"):
            if d in room.exits:
                dest_id = room.exits[d]
                dest_name = world.rooms[dest_id].name if dest_id in world.rooms else f"#{dest_id}"
                ud_lines.append(f"  Room #{rid} ({room.name})  {d.upper()} → #{dest_id} ({dest_name})")
    if ud_lines:
        print(f"\n  Vertical connections (UP/DOWN):")
        for ln in ud_lines:
            print(ln)
    print()


# ══════════════════════════════════════════════════════════════════════════════
# DESIGNER MENUS
# ══════════════════════════════════════════════════════════════════════════════

# All artifact types the engine supports
ALL_ARTIFACT_TYPES = [
    ArtifactType.GENERIC,
    ArtifactType.WEAPON,
    ArtifactType.ARMOR,
    ArtifactType.SHIELD,
    ArtifactType.RING,
    ArtifactType.CLOAK,
    ArtifactType.CONTAINER,
    ArtifactType.READABLE,
    ArtifactType.SPELLBOOK,
    ArtifactType.FOOD,
    ArtifactType.POTION,
    ArtifactType.LIGHT,
    ArtifactType.KEY,
]

WEAPON_TYPES = ["sword", "axe", "club", "spear", "bow", "(other/none)"]
STATS        = ["hardiness", "agility", "strength", "intelligence", "charisma"]
FOLLOWER_TYPES = ["stat", "chance", "trade", "combat", "alignment", "quest"]


class Designer:

    def __init__(self, adventure_path: str):
        self.path = adventure_path
        if os.path.isdir(adventure_path) and os.path.exists(
                os.path.join(adventure_path, "adventure.json")):
            self.world = World.load(adventure_path)
            print(f"\n  Loaded: {self.world.title}")
        else:
            self.world = World()
            print("\n  Starting new adventure.")

    # ── Top-level menu ────────────────────────────────────────────────────────

    def run(self) -> None:
        while True:
            print(f"\n{'═'*72}")
            print(f"  ADVENTURE DESIGNER  —  {self.world.title}")
            print(f"{'═'*72}")
            print("  1. Adventure settings  (title, intro, win condition)")
            print("  2. Rooms               (add, edit, exits, locked exits)")
            print("  3. Artifacts           (items, weapons, armor, rings, ...)")
            print("  4. Monsters & NPCs     (enemies, followers, captives)")
            print("  5. View map")
            print("  6. Save")
            print("  7. Test play (launch engine)")
            print("  0. Quit")
            choice = input("\n  > ").strip()

            if choice == "1":
                self.menu_settings()
            elif choice == "2":
                self.menu_rooms()
            elif choice == "3":
                self.menu_artifacts()
            elif choice == "4":
                self.menu_monsters()
            elif choice == "5":
                cls()
                print(f"\n  MAP: {self.world.title}")
                render_map(self.world)
                input("  Press Enter to continue...")
            elif choice == "6":
                self.world.save(self.path)
                print(f"\n  Saved to: {self.path}")
            elif choice == "7":
                self.launch_engine()
            elif choice == "0":
                if prompt_bool("Save before quitting?", default=True):
                    self.world.save(self.path)
                print("\n  Goodbye!\n")
                break

    # ── Settings ──────────────────────────────────────────────────────────────

    def menu_settings(self) -> None:
        print(f"\n  ADVENTURE SETTINGS")
        print(f"  {hr('─', 40)}")
        self.world.title  = prompt("Title",       self.world.title)
        self.world.author = prompt("Author",      self.world.author)
        self.world.intro  = prompt("Intro text",  self.world.intro)

        if self.world.rooms:
            ids   = sorted(self.world.rooms.keys())
            names = [f"#{r} {self.world.rooms[r].name}" for r in ids]
            n = choose(names, "Starting room")
            if n:
                self.world.start_room = ids[n - 1]

        if prompt_bool("Edit win condition?", bool(self.world.win_condition)):
            self._edit_win_condition()

        print("  Settings updated.")

    def _edit_win_condition(self) -> None:
        wc = self.world.win_condition or {}
        print(f"\n  WIN CONDITION")
        print(f"  {hr('─', 40)}")
        if wc:
            print(f"  Current: {json.dumps(wc)}")
        else:
            print("  Current: (none)")

        type_labels = [
            "reach_room    — player reaches a specific room",
            "kill_monster  — a specific monster must die",
            "kill_all      — every monster must be dead",
            "carry_artifact — player carries a specific artifact",
            "has_follower  — a specific NPC must be in the party",
            "compound      — ALL of a list of conditions must be true",
            "(remove win condition)",
        ]
        type_keys = ["reach_room", "kill_monster", "kill_all",
                     "carry_artifact", "has_follower", "compound", None]

        n = choose(type_labels, "Win condition type")
        if not n:
            return

        wc_type = type_keys[n - 1]
        if wc_type is None:
            self.world.win_condition = {}
            print("  Win condition removed.")
            return

        new_wc = {"type": wc_type}

        if wc_type == "reach_room":
            print("  Enter a room ID, or 'EXIT_TAVERN' to require the player to escape the cave.")
            raw = prompt("Room ID or EXIT_TAVERN", str(wc.get("room_id", "EXIT_TAVERN")))
            if raw.upper() == "EXIT_TAVERN":
                new_wc["room_id"] = "EXIT_TAVERN"
            else:
                try:
                    new_wc["room_id"] = int(raw)
                except ValueError:
                    new_wc["room_id"] = raw

        elif wc_type == "kill_monster":
            mid = self._pick_monster("Which monster must be killed?")
            if mid is None:
                print("  Cancelled.")
                return
            new_wc["monster_id"] = mid

        elif wc_type == "carry_artifact":
            aid = self._pick_artifact("Which artifact must be carried?")
            if aid is None:
                print("  Cancelled.")
                return
            new_wc["artifact_id"] = aid

        elif wc_type == "has_follower":
            mid = self._pick_monster("Which NPC must be in the party?")
            if mid is None:
                print("  Cancelled.")
                return
            new_wc["monster_id"] = mid

        elif wc_type == "compound":
            print("\n  Add sub-conditions (all must be true). Choose 0 / Done when finished.")
            conditions = list(wc.get("all_of", []))
            if conditions:
                print(f"  Existing conditions: {len(conditions)}")
                for c in conditions:
                    print(f"    • {json.dumps(c)}")
                if prompt_bool("Keep existing conditions?", True):
                    pass
                else:
                    conditions = []

            sub_labels = [
                "reach_room    — player in a specific room",
                "kill_monster  — specific monster dead",
                "carry_artifact — carrying specific artifact",
                "has_follower  — NPC in party",
                "Done — finish compound condition",
            ]
            sub_keys = ["reach_room", "kill_monster", "carry_artifact", "has_follower", None]

            while True:
                print(f"\n  Compound so far: {len(conditions)} condition(s)")
                m = choose(sub_labels, "Add sub-condition")
                if not m:
                    break
                sub_type = sub_keys[m - 1]
                if sub_type is None:
                    break
                sub_cond: dict = {"type": sub_type}
                if sub_type == "reach_room":
                    raw = prompt("Room ID or EXIT_TAVERN", "EXIT_TAVERN")
                    try:
                        sub_cond["room_id"] = int(raw)
                    except ValueError:
                        sub_cond["room_id"] = raw.upper()
                elif sub_type == "kill_monster":
                    mid = self._pick_monster("Which monster?")
                    if mid:
                        sub_cond["monster_id"] = mid
                elif sub_type == "carry_artifact":
                    aid = self._pick_artifact("Which artifact?")
                    if aid:
                        sub_cond["artifact_id"] = aid
                elif sub_type == "has_follower":
                    mid = self._pick_monster("Which NPC?")
                    if mid:
                        sub_cond["monster_id"] = mid
                conditions.append(sub_cond)
                print(f"  Added: {json.dumps(sub_cond)}")

            new_wc["all_of"] = conditions

        new_wc["message"] = prompt("Victory message", wc.get("message", "You have won!"))
        self.world.win_condition = new_wc
        print(f"  Win condition set: {json.dumps(new_wc)}")

    # ── Rooms ─────────────────────────────────────────────────────────────────

    def menu_rooms(self) -> None:
        while True:
            print(f"\n  ROOMS  ({len(self.world.rooms)} total)")
            print(f"  {hr('─', 40)}")
            print("  1. List rooms")
            print("  2. Add new room")
            print("  3. Edit room")
            print("  4. Delete room")
            print("  5. Edit exits")
            print("  6. Edit locked exits (require a key)")
            print("  0. Back")
            choice = input("\n  > ").strip()

            if choice == "1":
                self.list_rooms()
            elif choice == "2":
                self.add_room()
            elif choice == "3":
                self.edit_room()
            elif choice == "4":
                self.delete_room()
            elif choice == "5":
                self.edit_exits()
            elif choice == "6":
                self.edit_locked_exits()
            elif choice == "0":
                break

    def list_rooms(self) -> None:
        if not self.world.rooms:
            print("  No rooms yet.")
            return
        print()
        for rid in sorted(self.world.rooms.keys()):
            r = self.world.rooms[rid]
            star  = " ★" if rid == self.world.start_room else ""
            exits = ", ".join(r.exits.keys()) or "none"
            locked = f"  locked: {', '.join(r.locked_exits.keys())}" if r.locked_exits else ""
            print(f"  #{rid:>3}  {r.name:<30}  exits: {exits}{locked}{star}")

    def _pick_room(self, title="Select room") -> int | None:
        ids = sorted(self.world.rooms.keys())
        if not ids:
            print("  No rooms exist yet.")
            return None
        names = [f"#{r} {self.world.rooms[r].name}" for r in ids]
        n = choose(names, title)
        return ids[n - 1] if n else None

    def add_room(self) -> None:
        print(f"\n  NEW ROOM")
        rid  = self.world.next_room_id()
        name = prompt("Name")
        if not name:
            print("  Cancelled.")
            return
        desc = prompt("Description")
        dark = prompt_bool("Is it dark (need a light source)?", False)
        room = Room(id=rid, name=name, description=desc, is_dark=dark)
        self.world.rooms[rid] = room
        if len(self.world.rooms) == 1:
            self.world.start_room = rid
        print(f"  Room #{rid} '{name}' created.")

        if self.world.rooms and prompt_bool("Add exits now?", True):
            self._edit_exits_for(room)

    def edit_room(self) -> None:
        rid = self._pick_room("Edit which room?")
        if rid is None:
            return
        r = self.world.rooms[rid]
        print(f"\n  EDIT ROOM #{rid}")
        r.name        = prompt("Name",        r.name)
        r.description = prompt("Description", r.description)
        r.is_dark     = prompt_bool("Is it dark?", r.is_dark)
        print("  Room updated.")

    def delete_room(self) -> None:
        rid = self._pick_room("Delete which room?")
        if rid is None:
            return
        if not prompt_bool(f"Delete room #{rid} '{self.world.rooms[rid].name}'?", False):
            return
        del self.world.rooms[rid]
        for r in self.world.rooms.values():
            r.exits        = {d: dest for d, dest in r.exits.items()        if dest != rid}
            r.locked_exits = {d: dest for d, dest in r.locked_exits.items() if dest != rid}
        print(f"  Room #{rid} deleted.")

    def edit_exits(self) -> None:
        rid = self._pick_room("Edit exits for which room?")
        if rid is None:
            return
        self._edit_exits_for(self.world.rooms[rid])

    def _edit_exits_for(self, room: Room) -> None:
        print(f"\n  EXITS for #{room.id} '{room.name}'")
        print(f"  Current: {room.exit_list()}")
        print(f"  Enter a room #, 'EXIT_TAVERN' for the surface exit, or 'x' to remove.")
        print()
        for direction in DIRECTIONS:
            current = room.exits.get(direction)
            if current is None:
                cur_label = "none"
            elif isinstance(current, str):
                cur_label = current
            else:
                cur_label = (f"#{current} {self.world.rooms[current].name}"
                             if current in self.world.rooms else f"#{current} (missing)")

            raw = input(f"  {direction.capitalize():<12} [{cur_label}]: ").strip()
            if not raw:
                continue
            elif raw.lower() == "x":
                room.exits.pop(direction, None)
                print(f"    {direction} exit removed.")
            else:
                special_codes = ("EXIT_TAVERN", "RETURN_TO_TAVERN", "BACK_TO_TAVERN")
                if raw.upper() in special_codes:
                    room.exits[direction] = raw.upper()
                    print(f"    {direction} → {raw.upper()}")
                else:
                    try:
                        dest_id = int(raw)
                        if dest_id in self.world.rooms:
                            room.exits[direction] = dest_id
                            print(f"    {direction} → #{dest_id} '{self.world.rooms[dest_id].name}'")
                        else:
                            print(f"    Room #{dest_id} not found — skipped.")
                    except ValueError:
                        print(f"    Unknown value '{raw}' — skipped.")
        print("  Exits updated.")

    def edit_locked_exits(self) -> None:
        rid = self._pick_room("Add a locked exit to which room?")
        if rid is None:
            return
        room = self.world.rooms[rid]
        print(f"\n  LOCKED EXITS for #{rid} '{room.name}'")
        print(f"  A locked exit requires the player to carry a KEY artifact to pass.")
        print(f"  Current exits: {room.exit_list()}")
        if room.locked_exits:
            print(f"  Currently locked: {', '.join(room.locked_exits.keys())}")
        print()

        for direction in DIRECTIONS:
            if direction not in room.exits:
                continue
            current_key = room.locked_exits.get(direction)
            cur_label = f"key artifact #{current_key}" if current_key else "unlocked"
            raw = input(f"  {direction.capitalize():<12} [{cur_label}]  "
                        "Enter key artifact # or 'x' to unlock: ").strip()
            if not raw:
                continue
            elif raw.lower() == "x":
                room.locked_exits.pop(direction, None)
                print(f"    {direction} unlocked.")
            else:
                try:
                    key_id = int(raw)
                    room.locked_exits[direction] = key_id
                    key_name = (self.world.artifacts[key_id].name
                                if key_id in self.world.artifacts else f"artifact #{key_id}")
                    print(f"    {direction} locked — requires {key_name}")
                except ValueError:
                    print(f"    Please enter an artifact ID number.")
        print("  Locked exits updated.")

    # ── Artifacts ─────────────────────────────────────────────────────────────

    def menu_artifacts(self) -> None:
        while True:
            print(f"\n  ARTIFACTS  ({len(self.world.artifacts)} total)")
            print(f"  {hr('─', 40)}")
            print("  1. List artifacts")
            print("  2. Add new artifact")
            print("  3. Edit artifact")
            print("  4. Delete artifact")
            print("  5. Move artifact to room")
            print("  0. Back")
            choice = input("\n  > ").strip()

            if choice == "1":
                self.list_artifacts()
            elif choice == "2":
                self.add_artifact()
            elif choice == "3":
                self.edit_artifact()
            elif choice == "4":
                self.delete_artifact()
            elif choice == "5":
                self.move_artifact()
            elif choice == "0":
                break

    def list_artifacts(self) -> None:
        if not self.world.artifacts:
            print("  No artifacts yet.")
            return
        print()
        for aid in sorted(self.world.artifacts.keys()):
            a = self.world.artifacts[aid]
            location = (f"Room #{a.room_id} {self.world.rooms[a.room_id].name}"
                        if a.room_id and a.room_id in self.world.rooms
                        else "carried" if a.room_id is None else f"Room #{a.room_id}")
            extras = ""
            if a.stat_bonuses:
                extras += f"  bonuses:{a.stat_bonuses}"
            if (a.flags or {}).get("cursed"):
                extras += "  [CURSED]"
            if (a.flags or {}).get("adventure_only"):
                extras += "  [ADV-ONLY]"
            print(f"  #{aid:>3}  {a.name:<26}  [{a.artifact_type:<10}]  @ {location}{extras}")

    def _pick_artifact(self, title="Select artifact") -> int | None:
        ids = sorted(self.world.artifacts.keys())
        if not ids:
            print("  No artifacts exist yet.")
            return None
        names = [f"#{a} {self.world.artifacts[a].name}" for a in ids]
        n = choose(names, title)
        return ids[n - 1] if n else None

    def add_artifact(self) -> None:
        print(f"\n  NEW ARTIFACT")
        aid  = self.world.next_artifact_id()
        name = prompt("Name")
        if not name:
            print("  Cancelled.")
            return
        desc = prompt("Description")

        type_labels = [
            "generic    — misc item with no special mechanics",
            "weapon     — can be equipped and used in combat",
            "armor      — wearable protection",
            "shield     — off-hand protection",
            "ring       — equippable; may grant stat bonuses",
            "cloak      — equippable; may grant stat bonuses",
            "container  — chest, bag, etc. (holds other items)",
            "readable   — book, scroll, inscription",
            "spellbook  — teaches a spell when read",
            "food       — restores HP when eaten",
            "potion     — restores HP when drunk",
            "light      — torch, lantern (illuminates dark rooms)",
            "key        — unlocks a locked exit",
        ]
        n = choose(type_labels, "Artifact type")
        atype = ALL_ARTIFACT_TYPES[n - 1] if n else ArtifactType.GENERIC

        weight = prompt_int("Weight (gronds)", 1)
        value  = prompt_int("Sell value (-1 = auto by type)", -1)

        synonyms_raw = prompt("Synonyms / alternate names (comma-separated)", "")
        synonyms     = [s.strip() for s in synonyms_raw.split(",") if s.strip()]

        a = Artifact(id=aid, name=name, description=desc,
                     artifact_type=atype, weight=weight, value=value,
                     synonyms=synonyms, room_id=None)

        # ── Type-specific fields ───────────────────────────────────────────
        if atype == ArtifactType.WEAPON:
            wn = choose(WEAPON_TYPES, "Weapon type (affects proficiency)")
            if wn and wn < len(WEAPON_TYPES):
                a.weapon_type = WEAPON_TYPES[wn - 1] if WEAPON_TYPES[wn-1] != "(other/none)" else None
            a.damage_dice  = prompt_int("Damage dice  (e.g. 1 for 1d8)", 1)
            a.damage_sides = prompt_int("Damage sides (e.g. 8 for 1d8)", 6)

        elif atype == ArtifactType.ARMOR:
            a.armor_class = prompt_int("Armor class bonus", 2)

        elif atype == ArtifactType.SHIELD:
            a.armor_class = prompt_int("Armor class bonus", 1)

        elif atype in (ArtifactType.RING, ArtifactType.CLOAK):
            self._prompt_stat_bonuses(a)
            if a.stat_bonuses:
                default_label = ", ".join(
                    f"+{v} {k.capitalize()}" if v > 0 else f"{v} {k.capitalize()}"
                    for k, v in a.stat_bonuses.items()
                )
                a.flags["ring_label"] = prompt("Label shown when equipped", default_label)
                if prompt_bool("Is this cursed (cannot be removed)?", False):
                    a.flags["cursed"] = True

        elif atype == ArtifactType.CONTAINER:
            a.is_container = True
            a.is_open      = prompt_bool("Starts open?", False)

        elif atype in (ArtifactType.READABLE, ArtifactType.SPELLBOOK):
            a.read_text = prompt("Text displayed when read")
            if atype == ArtifactType.SPELLBOOK:
                print("  Note: name the spellbook after the spell it teaches")
                print("  (e.g. 'blast spellbook') so the engine can identify it.")

        elif atype in (ArtifactType.FOOD, ArtifactType.POTION):
            a.heal_amount = prompt_int("HP restored when consumed", 5)

        elif atype == ArtifactType.KEY:
            print("  Note: link this key to a locked exit via Rooms → Edit locked exits.")

        # ── Common optional flags ──────────────────────────────────────────
        if prompt_bool("Is this a quest item (cannot be sold)?", False):
            a.is_quest_item = True

        if prompt_bool("Is this adventure-only (auto-sold when leaving the adventure)?", False):
            a.flags["adventure_only"] = True

        # ── Place in room ──────────────────────────────────────────────────
        if self.world.rooms and prompt_bool("Place in a room now?", True):
            rid      = self._pick_room("Place in which room?")
            a.room_id = rid

        self.world.artifacts[aid] = a
        print(f"  Artifact #{aid} '{name}' ({atype}) created.")

    def edit_artifact(self) -> None:
        aid = self._pick_artifact("Edit which artifact?")
        if aid is None:
            return
        a = self.world.artifacts[aid]
        print(f"\n  EDIT ARTIFACT #{aid}  [{a.artifact_type}]")
        a.name        = prompt("Name",        a.name)
        a.description = prompt("Description", a.description)
        a.weight      = prompt_int("Weight",  a.weight)
        a.value       = prompt_int("Sell value (-1 = auto)", a.value)

        syns_new   = prompt("Synonyms (comma-separated)", ", ".join(a.synonyms))
        a.synonyms = [s.strip() for s in syns_new.split(",") if s.strip()]

        # ── Type-specific fields ───────────────────────────────────────────
        if a.artifact_type == ArtifactType.WEAPON:
            wn = choose(WEAPON_TYPES, f"Weapon type [{a.weapon_type or 'none'}]")
            if wn:
                a.weapon_type = WEAPON_TYPES[wn - 1] if WEAPON_TYPES[wn-1] != "(other/none)" else None
            a.damage_dice  = prompt_int("Damage dice",  a.damage_dice)
            a.damage_sides = prompt_int("Damage sides", a.damage_sides)

        elif a.artifact_type in (ArtifactType.ARMOR, ArtifactType.SHIELD):
            a.armor_class = prompt_int("Armor class bonus", a.armor_class)

        elif a.artifact_type in (ArtifactType.RING, ArtifactType.CLOAK):
            if a.stat_bonuses:
                print(f"  Current stat bonuses: {a.stat_bonuses}")
            if prompt_bool("Edit stat bonuses?", bool(a.stat_bonuses)):
                a.stat_bonuses = {}
                self._prompt_stat_bonuses(a)
            if a.stat_bonuses:
                default_label = a.flags.get("ring_label", "")
                a.flags["ring_label"] = prompt("Label shown when equipped", default_label)
                a.flags["cursed"] = prompt_bool(
                    "Cursed (cannot be removed)?", a.flags.get("cursed", False))

        elif a.artifact_type == ArtifactType.CONTAINER:
            a.is_open = prompt_bool("Currently open?", a.is_open)

        elif a.artifact_type in (ArtifactType.READABLE, ArtifactType.SPELLBOOK):
            a.read_text = prompt("Text when read", a.read_text or "")

        elif a.artifact_type in (ArtifactType.FOOD, ArtifactType.POTION):
            a.heal_amount = prompt_int("HP restored when consumed", a.heal_amount)

        # ── Common fields ──────────────────────────────────────────────────
        a.is_quest_item = prompt_bool(
            "Quest item (cannot be sold)?", a.is_quest_item)

        if prompt_bool("Edit special flags?", False):
            self._edit_artifact_flags(a)

        print("  Artifact updated.")

    def _prompt_stat_bonuses(self, artifact: Artifact) -> None:
        """Prompt for stat bonuses/penalties and store in artifact.stat_bonuses."""
        print(f"\n  STAT BONUSES  (positive = bonus, negative = penalty, 0 = skip)")
        for stat in STATS:
            current = artifact.stat_bonuses.get(stat, 0)
            val = prompt_int(f"  {stat.capitalize():<14}", current)
            if val != 0:
                artifact.stat_bonuses[stat] = val
            else:
                artifact.stat_bonuses.pop(stat, None)

    def _edit_artifact_flags(self, artifact: Artifact) -> None:
        """Edit special flags on an artifact."""
        print(f"\n  ARTIFACT FLAGS — {artifact.name}  [{artifact.artifact_type}]")
        print(f"  {hr('─', 40)}")
        flags = dict(artifact.flags)

        # adventure_only
        adv_only = prompt_bool(
            "Adventure-only (auto-sold when leaving the adventure)?",
            flags.get("adventure_only", False))
        if adv_only:
            flags["adventure_only"] = True
        else:
            flags.pop("adventure_only", None)

        # Tradeable to NPCs
        is_tradeable = prompt_bool("Tradeable to an NPC?", flags.get("is_tradeable", False))
        if is_tradeable:
            flags["is_tradeable"]   = True
            flags["trade_npc"]      = prompt("Trade with which NPC?", flags.get("trade_npc", ""))
            flags["trade_dialogue"] = prompt("Dialogue when traded?",  flags.get("trade_dialogue", ""))
        else:
            for k in ("is_tradeable", "trade_npc", "trade_dialogue"):
                flags.pop(k, None)

        # Escape vehicle
        is_escape = prompt_bool(
            "Escape vehicle (boat, portal — USE to leave the adventure)?",
            flags.get("is_escape_vehicle", False))
        if is_escape:
            flags["is_escape_vehicle"] = True
            flags["escape_dialogue"]   = prompt(
                "Dialogue when used?", flags.get("escape_dialogue", "You escape!"))
        else:
            for k in ("is_escape_vehicle", "escape_dialogue"):
                flags.pop(k, None)

        # Event trigger
        triggers = prompt_bool(
            "Does using/entering trigger an event?", bool(flags.get("triggers_event")))
        if triggers:
            flags["triggers_event"] = prompt("Event ID", flags.get("triggers_event", ""))
        else:
            flags.pop("triggers_event", None)

        artifact.flags = flags
        print("  Flags updated.")

    def delete_artifact(self) -> None:
        aid = self._pick_artifact("Delete which artifact?")
        if aid is None:
            return
        if not prompt_bool(f"Delete artifact #{aid} '{self.world.artifacts[aid].name}'?", False):
            return
        del self.world.artifacts[aid]
        for a in self.world.artifacts.values():
            if aid in a.contents:
                a.contents.remove(aid)
        print(f"  Artifact #{aid} deleted.")

    def move_artifact(self) -> None:
        aid = self._pick_artifact("Move which artifact?")
        if aid is None:
            return
        a   = self.world.artifacts[aid]
        rid = self._pick_room(f"Move '{a.name}' to which room?")
        if rid is not None:
            a.room_id = rid
            print(f"  '{a.name}' moved to room #{rid}.")

    # ── Monsters ──────────────────────────────────────────────────────────────

    def menu_monsters(self) -> None:
        while True:
            print(f"\n  MONSTERS & NPCs  ({len(self.world.monsters)} total)")
            print(f"  {hr('─', 40)}")
            print("  1. List monsters")
            print("  2. Add new monster / NPC")
            print("  3. Edit monster")
            print("  4. Move monster to room")
            print("  5. Delete monster")
            print("  0. Back")
            choice = input("\n  > ").strip()

            if choice == "1":
                self.list_monsters()
            elif choice == "2":
                self.add_monster()
            elif choice == "3":
                self.edit_monster()
            elif choice == "4":
                self.move_monster()
            elif choice == "5":
                self.delete_monster()
            elif choice == "0":
                break

    def list_monsters(self) -> None:
        if not self.world.monsters:
            print("  No monsters yet.")
            return
        print()
        for mid in sorted(self.world.monsters.keys()):
            m        = self.world.monsters[mid]
            location = (f"Room #{m.room_id} {self.world.rooms[m.room_id].name}"
                        if m.room_id in self.world.rooms else f"Room #{m.room_id}")
            flags    = m.flags or {}
            tags = []
            if flags.get("is_follower"):
                tags.append(f"follower({flags.get('follower_type','?')})")
            if flags.get("is_captive"):
                tags.append("captive")
            tag_str = f"  [{', '.join(tags)}]" if tags else ""
            print(f"  #{mid:>3}  {m.name:<26}  [{m.attitude:<8}]  HP:{m.hp_max:<4}  "
                  f"@ {location}{tag_str}")

    def _pick_monster(self, title="Select monster") -> int | None:
        ids = sorted(self.world.monsters.keys())
        if not ids:
            print("  No monsters exist yet.")
            return None
        names = [f"#{m} {self.world.monsters[m].name}" for m in ids]
        n = choose(names, title)
        return ids[n - 1] if n else None

    def add_monster(self) -> None:
        print(f"\n  NEW MONSTER / NPC")
        mid  = self.world.next_monster_id()
        name = prompt("Name")
        if not name:
            print("  Cancelled.")
            return
        desc = prompt("Description")

        attitudes = [Attitude.HOSTILE, Attitude.NEUTRAL, Attitude.FRIENDLY]
        n        = choose(attitudes, "Attitude")
        attitude = attitudes[n - 1] if n else Attitude.HOSTILE

        hp           = prompt_int("HP", 10)
        damage_dice  = prompt_int("Damage dice  (e.g. 1 for 1d6)", 1)
        damage_sides = prompt_int("Damage sides (e.g. 6 for 1d6)", 6)
        armor_class  = prompt_int("Armor class (damage reduction)", 0)
        xp_value     = prompt_int("XP awarded on defeat (0 = auto)", 0)
        dialogue     = prompt("Dialogue shown on TALK TO", "")
        death_msg    = prompt("Death message", "")
        loot_id      = prompt_int("Loot artifact ID (drops on death, 0 = none)", 0)

        synonyms_raw = prompt("Synonyms / alternate names (comma-separated)", "")
        synonyms     = [s.strip() for s in synonyms_raw.split(",") if s.strip()]

        heal_amount = 0
        heal_cost   = 0
        if attitude in (Attitude.NEUTRAL, Attitude.FRIENDLY):
            if prompt_bool("Can this NPC offer healing to the player?", False):
                heal_amount = prompt_int("HP healed per use", 5)
                heal_cost   = prompt_int("Gold cost per HP healed", 2)

        if not self.world.rooms:
            print("  No rooms exist — monster will be placed in room 1.")
            room_id = 1
        else:
            rid     = self._pick_room("Place in which room?")
            room_id = rid if rid is not None else self.world.start_room

        flags: dict = {}
        if prompt_bool("Configure follower / captive flags?", False):
            flags = self._build_monster_flags(attitude)

        m = Monster(
            id=mid, name=name, description=desc, room_id=room_id,
            attitude=attitude, hp=hp, hp_max=hp,
            damage_dice=damage_dice, damage_sides=damage_sides,
            armor_class=armor_class, xp_value=xp_value,
            dialogue=dialogue, death_message=death_msg,
            heal_amount=heal_amount, heal_cost=heal_cost,
            loot_id=loot_id, synonyms=synonyms, flags=flags,
        )
        self.world.monsters[mid] = m
        print(f"  Monster #{mid} '{name}' created.")

    def edit_monster(self) -> None:
        mid = self._pick_monster("Edit which monster?")
        if mid is None:
            return
        m = self.world.monsters[mid]
        print(f"\n  EDIT MONSTER #{mid}  [{m.attitude}]")
        m.name         = prompt("Name",         m.name)
        m.description  = prompt("Description",  m.description)
        m.hp           = prompt_int("HP",            m.hp_max)
        m.hp_max       = m.hp
        m.damage_dice  = prompt_int("Damage dice",   m.damage_dice)
        m.damage_sides = prompt_int("Damage sides",  m.damage_sides)
        m.armor_class  = prompt_int("Armor class",   m.armor_class)
        m.xp_value     = prompt_int("XP value",      m.xp_value)
        m.loot_id      = prompt_int("Loot artifact ID (0 = none)", m.loot_id)
        m.dialogue     = prompt("Dialogue",      m.dialogue)
        m.death_message = prompt("Death message", m.death_message)

        attitudes = [Attitude.HOSTILE, Attitude.NEUTRAL, Attitude.FRIENDLY]
        n = choose(attitudes, f"Attitude  [{m.attitude}]")
        if n:
            m.attitude = attitudes[n - 1]
            m.aggro    = m.attitude == Attitude.HOSTILE

        syns_new   = prompt("Synonyms (comma-separated)", ", ".join(m.synonyms))
        m.synonyms = [s.strip() for s in syns_new.split(",") if s.strip()]

        if prompt_bool("Edit heal mechanics?", bool(m.heal_amount)):
            m.heal_amount = prompt_int("HP healed per use", m.heal_amount)
            m.heal_cost   = prompt_int("Gold cost per HP",  m.heal_cost)

        if prompt_bool("Edit follower / captive flags?", bool(m.flags)):
            m.flags = self._build_monster_flags(m.attitude, m.flags)

        print("  Monster updated.")

    def move_monster(self) -> None:
        mid = self._pick_monster("Move which monster?")
        if mid is None:
            return
        m   = self.world.monsters[mid]
        rid = self._pick_room(f"Move '{m.name}' to which room?")
        if rid is not None:
            m.room_id = rid
            print(f"  '{m.name}' moved to room #{rid}.")

    def delete_monster(self) -> None:
        mid = self._pick_monster("Delete which monster?")
        if mid is None:
            return
        name = self.world.monsters[mid].name
        if not prompt_bool(f"Delete monster #{mid} '{name}'?", False):
            return
        del self.world.monsters[mid]
        print(f"  Monster #{mid} deleted.")

    def _build_monster_flags(self, attitude: str, existing: dict = None) -> dict:
        """Interactive editor for NPC/monster flags. Returns updated flags dict."""
        flags = dict(existing or {})
        print(f"\n  MONSTER FLAGS")
        print(f"  {hr('─', 40)}")

        # ── FOLLOWER ──────────────────────────────────────────────────────
        is_follower = prompt_bool(
            "Can this NPC be recruited as a follower (TALK TO)?",
            flags.get("is_follower", False))
        if is_follower:
            flags["is_follower"] = True

            ft_n = choose(
                [f"{ft}  — {self._follower_type_hint(ft)}" for ft in FOLLOWER_TYPES],
                "Recruitment condition type")
            ftype = FOLLOWER_TYPES[ft_n - 1] if ft_n else "chance"
            flags["follower_type"] = ftype

            if ftype == "stat":
                sn = choose(STATS, "Which stat is checked?")
                flags["required_stat"]       = STATS[sn - 1] if sn else "strength"
                flags["required_stat_value"] = prompt_int("Minimum value required", 10)

            elif ftype == "chance":
                flags["chance_base"]  = float(prompt("Base probability (0.0–1.0)", str(flags.get("chance_base", 0.5))))
                sn = choose(["(none)"] + STATS, "Stat that modifies the roll (adds stat×0.01)")
                flags["stat_modifier"] = STATS[sn - 2] if sn and sn > 1 else ""
                if not flags["stat_modifier"]:
                    flags.pop("stat_modifier", None)

            elif ftype == "trade":
                flags["required_item"] = prompt(
                    "Item name the player must carry", flags.get("required_item", ""))

            elif ftype == "combat":
                flags["requires_kills"] = prompt_int(
                    "Kills required this adventure", flags.get("requires_kills", 5))

            elif ftype == "alignment":
                flags["requires_alignment"] = prompt(
                    "Required alignment (good/neutral/evil)",
                    flags.get("requires_alignment", "good"))

            elif ftype == "quest":
                flags["quest_condition"] = prompt(
                    "Quest flag ID that must be True", flags.get("quest_condition", ""))

            flags["recruit_cost"] = prompt_int(
                "Gold cost to recruit (0 = free)", flags.get("recruit_cost", 0))
            flags["follower_dialogue"] = prompt(
                "Dialogue shown on successful recruit", flags.get("follower_dialogue", f"I'll join you!"))
            flags["recruit_fail_dialogue"] = prompt(
                "Dialogue on failed recruit", flags.get("recruit_fail_dialogue", "I won't join you."))
            flags["can_fight"] = prompt_bool(
                "Does this follower fight in combat?", flags.get("can_fight", True))
        else:
            for k in ("is_follower", "follower_type", "required_stat", "required_stat_value",
                      "chance_base", "stat_modifier", "required_item", "requires_kills",
                      "requires_alignment", "quest_condition", "recruit_cost",
                      "follower_dialogue", "recruit_fail_dialogue", "can_fight"):
                flags.pop(k, None)

        # ── CAPTIVE ───────────────────────────────────────────────────────
        is_captive = prompt_bool(
            "Is this NPC a captive (freed with FREE command, not TALK TO)?",
            flags.get("is_captive", False))
        if is_captive:
            flags["is_captive"] = True
            guard_id = prompt_int(
                "Guard monster ID (must be killed before freeing, 0 = none)",
                flags.get("guard_id", 0))
            if guard_id:
                flags["guard_id"] = guard_id
            else:
                flags.pop("guard_id", None)
            flags["free_dialogue"]      = prompt(
                "Dialogue on successful free", flags.get("free_dialogue", f"Thank you for freeing me!"))
            flags["free_fail_dialogue"] = prompt(
                "Dialogue when guard is still alive", flags.get("free_fail_dialogue", "You must defeat my captor first!"))
            flags["free_xp_bonus"]      = prompt_int(
                "Bonus XP awarded for freeing (0 = none)", flags.get("free_xp_bonus", 0))
            flags["can_fight"] = prompt_bool(
                "Does the freed NPC fight alongside you?", flags.get("can_fight", False))
        else:
            for k in ("is_captive", "guard_id", "free_dialogue",
                      "free_fail_dialogue", "free_xp_bonus"):
                flags.pop(k, None)
            if not is_follower:
                flags.pop("can_fight", None)

        # Clean up empty strings
        flags = {k: v for k, v in flags.items() if v != ""}
        print("  Monster flags updated.")
        return flags

    @staticmethod
    def _follower_type_hint(ft: str) -> str:
        hints = {
            "stat":      "requires a minimum score in a stat (e.g. Strength ≥ 12)",
            "chance":    "random roll, optionally boosted by Charisma or other stat",
            "trade":     "player must be carrying a specific item",
            "combat":    "player must have reached a kill-count threshold",
            "alignment": "player must have a specific alignment",
            "quest":     "a named quest flag must be True",
        }
        return hints.get(ft, "")

    # ── Test play ─────────────────────────────────────────────────────────────

    def launch_engine(self) -> None:
        self.world.save(self.path)
        print(f"\n  Saved. Launching engine for '{self.world.title}'...\n")
        import subprocess
        subprocess.call([sys.executable, "engine.py", self.path])


# ── Entry point ───────────────────────────────────────────────────────────────

def _choose_or_create(adventures_dir: str = "adventures") -> str:
    """Interactive startup: pick an existing adventure or create a new one."""
    existing = []
    if os.path.isdir(adventures_dir):
        for entry in sorted(os.listdir(adventures_dir)):
            adv_path = os.path.join(adventures_dir, entry)
            meta_path = os.path.join(adv_path, "adventure.json")
            if os.path.isdir(adv_path) and os.path.exists(meta_path):
                try:
                    with open(meta_path) as f:
                        meta = json.load(f)
                    title = meta.get("title", entry)
                except Exception:
                    title = entry
                existing.append((title, adv_path))

    print(f"\n  {hr('═')}")
    print(f"  EAMON REDUX — ADVENTURE DESIGNER")
    print(f"  {hr('═')}\n")

    if existing:
        print(f"  Existing adventures:")
        print(f"  {hr()}")
        for i, (title, path) in enumerate(existing, 1):
            print(f"  {i:>3}. {title}  ({path})")
        print()
        print(f"    N. New adventure")
        print(f"    0. Quit")
    else:
        print(f"  No adventures found in '{adventures_dir}'.")
        print(f"    N. New adventure")
        print(f"    0. Quit")

    while True:
        raw = input("\n  > ").strip().lower()
        if raw == "0":
            print("\n  Goodbye!\n")
            sys.exit(0)
        elif raw == "n":
            break
        else:
            try:
                n = int(raw)
                if 1 <= n <= len(existing):
                    return existing[n - 1][1]
            except ValueError:
                pass
            print("  Invalid choice.")

    # New adventure
    print(f"\n  {hr()}")
    print(f"  NEW ADVENTURE\n")
    while True:
        name = input("  Title: ").strip()
        if not name:
            print("  Title cannot be empty.")
            continue
        slug = "".join(
            c if c.isalnum() or c == "_" else "_"
            for c in name.lower().replace(" ", "_").replace("'", "")
        ).strip("_")
        path = os.path.join(adventures_dir, slug)
        if os.path.exists(path):
            print(f"  '{path}' already exists — choose a different title or select it from the list.")
            continue
        print(f"  Directory: {path}")
        confirm = input("  OK? [Y/n]: ").strip().lower()
        if not confirm or confirm.startswith("y"):
            return path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Eamon Redux — Adventure Designer")
    parser.add_argument("adventure", nargs="?", default=None,
                        help="Path to adventure directory (optional; shows chooser if omitted)")
    args = parser.parse_args()

    path = args.adventure if args.adventure else _choose_or_create()
    Designer(path).run()


if __name__ == "__main__":
    main()
