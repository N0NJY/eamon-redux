"""
designer.py - Adventure Designer Tool

Two modes:
  Menu mode  - create/edit rooms and artifacts via numbered menus
  Map mode   - display ASCII grid map of room connections
"""

from __future__ import annotations
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

    Grid step: each room cell is 7 wide x 3 tall (plus connector rows/cols).
    """
    if not world.rooms:
        print("  (no rooms to display)")
        return

    # ── BFS to assign grid positions ──────────────────────────────────────
    DELTAS = {
        "north": (0,  1),
        "south": (0, -1),
        "east":  (1,  0),
        "west":  (-1, 0),
    }
    pos: dict[int, tuple[int, int]] = {}   # room_id -> (gx, gy)
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
                # check for collision, shift if needed
                candidate = (gx + dx, gy + dy)
                # simple collision avoidance: keep nudging
                while candidate in pos.values():
                    candidate = (candidate[0] + dx, candidate[1] + dy)
                pos[dest_id] = candidate
                visited.add(dest_id)
                queue.append(dest_id)

    # Rooms not reachable via NSEW (up/down, orphans) — place below main map
    unreachable = [rid for rid in world.rooms if rid not in pos]
    col = 0
    min_y = min(y for _, y in pos.values()) - 2 if pos else 0
    for rid in unreachable:
        pos[rid] = (col, min_y)
        col += 1

    if not pos:
        print("  (nothing to display)")
        return

    # ── Normalize to 0-based grid ─────────────────────────────────────────
    min_gx = min(x for x, _ in pos.values())
    min_gy = min(y for _, y in pos.values())
    pos = {rid: (x - min_gx, y - min_gy) for rid, (x, y) in pos.items()}

    max_gx = max(x for x, _ in pos.values())
    max_gy = max(y for _, y in pos.values())

    # Grid layout: each cell is CELL_W cols wide, CELL_H rows tall
    # Between cells: 1 connector row/col
    CELL_W = 9    # inner width of room box
    CELL_H = 3    # inner height of room box

    # Canvas size in characters
    cols_per_step = CELL_W + 3   # cell + connector col + padding
    rows_per_step = CELL_H + 2   # cell + connector row + padding

    # We flip y so north is up: gy_screen = max_gy - gy
    grid_w = (max_gx + 1) * cols_per_step + 2
    grid_h = (max_gy + 1) * rows_per_step + 2

    canvas = [[" "] * grid_w for _ in range(grid_h)]

    def screen_xy(gx: int, gy: int) -> tuple[int, int]:
        """Top-left corner of a room box in canvas coordinates."""
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
        W = CELL_W + 2   # total box width including borders
        H = CELL_H + 2

        # corners
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

        # Label: truncate to fit, center
        inner_w = CELL_W
        id_str = f"#{room_id}"
        put_str(sx + 1, sy + 1, id_str[:inner_w].ljust(inner_w))
        name_trunc = label[:inner_w]
        put_str(sx + 1, sy + 2, name_trunc[:inner_w].ljust(inner_w))

    # Draw room boxes
    for rid, (gx, gy) in pos.items():
        sx, sy = screen_xy(gx, gy)
        room = world.rooms[rid]
        draw_box(sx, sy, room.name, rid, rid == world.start_room)

    # Draw connectors between rooms (NSEW only)
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
            dsx, dsy = screen_xy(gx + dx, gy + dy)

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

    # Render
    print()
    for row in canvas:
        line = "".join(row).rstrip()
        if line:
            print("  " + line)

    print()
    print(f"  ╔═ Start room   ┌─ Regular room")
    if unreachable:
        print(f"  Rooms without N/S/E/W connections shown at bottom.")

    # Up/down exits summary
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
            print("  1. Adventure settings")
            print("  2. Rooms")
            print("  3. Artifacts (objects)")
            print("  4. Monsters & NPCs")
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
        self.world.title  = prompt("Title",  self.world.title)
        self.world.author = prompt("Author", self.world.author)
        self.world.intro  = prompt("Intro text", self.world.intro)
        if self.world.rooms:
            ids = sorted(self.world.rooms.keys())
            names = [f"#{r} {self.world.rooms[r].name}" for r in ids]
            n = choose(names, "Starting room")
            if n:
                self.world.start_room = ids[n - 1]
        print("  Settings updated.")

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
            elif choice == "0":
                break

    def list_rooms(self) -> None:
        if not self.world.rooms:
            print("  No rooms yet.")
            return
        print()
        for rid in sorted(self.world.rooms.keys()):
            r = self.world.rooms[rid]
            star = " ★" if rid == self.world.start_room else ""
            exits = ", ".join(r.exits.keys()) or "none"
            print(f"  #{rid:>3}  {r.name:<30}  exits: {exits}{star}")

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
        rid = self.world.next_room_id()
        name = prompt("Name")
        if not name:
            print("  Cancelled.")
            return
        desc = prompt("Description")
        dark = prompt_bool("Is it dark?", False)
        room = Room(id=rid, name=name, description=desc, is_dark=dark)
        self.world.rooms[rid] = room
        if len(self.world.rooms) == 1:
            self.world.start_room = rid
        print(f"  Room #{rid} '{name}' created.")

    def edit_room(self) -> None:
        rid = self._pick_room("Edit which room?")
        if rid is None:
            return
        r = self.world.rooms[rid]
        print(f"\n  EDIT ROOM #{rid}")
        r.name        = prompt("Name",        r.name)
        r.description = prompt("Description", r.description)
        r.is_dark     = prompt_bool("Is it dark?", r.is_dark)

        if prompt_bool("Edit flags (special behaviors)?", False):
            self._edit_room_flags(r)

        print("  Room updated.")

    def _edit_room_flags(self, room) -> None:
        """Edit flags for a room (exit, win condition, event trigger)."""
        print(f"\n  ROOM FLAGS — {room.name} (#{room.id})")
        print(f"  {hr('─', 40)}")

        flags = dict(room.flags)

        # --- EXIT ROOM ---
        is_exit = prompt_bool("Is this an exit room (way out)?", flags.get("is_exit", False))
        if is_exit:
            flags["is_exit"] = True
        else:
            flags.pop("is_exit", None)

        # --- WIN ROOM ---
        is_win = prompt_bool("Is this a win room (victory condition)?", flags.get("is_win_room", False))
        if is_win:
            flags["is_win_room"]    = True
            flags["win_condition"]  = prompt("Win condition (e.g., 'has_rescued_girl')", flags.get("win_condition", ""))
            flags["win_dialogue"]   = prompt("Victory message", flags.get("win_dialogue", "You have won!"))
        else:
            flags.pop("is_win_room",   None)
            flags.pop("win_condition", None)
            flags.pop("win_dialogue",  None)

        # --- EVENT TRIGGER ---
        triggers = prompt_bool("Does entering this room trigger an event?", bool(flags.get("triggers_event")))
        if triggers:
            flags["triggers_event"] = prompt("Event ID to trigger", flags.get("triggers_event", ""))
        else:
            flags.pop("triggers_event", None)

        room.flags = flags
        print("  Room flags updated.")

    def delete_room(self) -> None:
        rid = self._pick_room("Delete which room?")
        if rid is None:
            return
        if not prompt_bool(f"Delete room #{rid} '{self.world.rooms[rid].name}'?", False):
            return
        del self.world.rooms[rid]
        # Clean up exits pointing to deleted room
        for r in self.world.rooms.values():
            r.exits = {d: dest for d, dest in r.exits.items() if dest != rid}
        print(f"  Room #{rid} deleted.")

    def edit_exits(self) -> None:
        rid = self._pick_room("Edit exits for which room?")
        if rid is None:
            return
        room = self.world.rooms[rid]
        print(f"\n  EXITS for #{rid} '{room.name}'")
        print(f"  Current exits: {room.exit_list()}")
        print(f"  Special codes: EXIT_TAVERN, RETURN_TO_TAVERN, BACK_TO_TAVERN")
        print()
        for direction in DIRECTIONS:
            current = room.exits.get(direction)
            # Format current exit label (room ID or special code)
            if current is None:
                cur_label = "none"
            elif isinstance(current, str):
                cur_label = current
            else:
                cur_label = f"#{current} {self.world.rooms[current].name}" if current in self.world.rooms else f"#{current} (missing)"
            
            raw = input(f"  {direction.capitalize():<8} [{cur_label}]  "
                        "Enter room #, special code, or 'x' to remove: ").strip()
            if raw == "":
                continue
            elif raw.lower() == "x":
                room.exits.pop(direction, None)
                print(f"    {direction} exit removed.")
            else:
                # Try to parse as room ID first
                try:
                    dest_id = int(raw)
                    if dest_id in self.world.rooms:
                        room.exits[direction] = dest_id
                        print(f"    {direction} → #{dest_id} '{self.world.rooms[dest_id].name}'")
                    else:
                        print(f"    Room #{dest_id} not found, skipping.")
                except ValueError:
                    # Not a number, treat as special code
                    special_codes = ("EXIT_TAVERN", "RETURN_TO_TAVERN", "BACK_TO_TAVERN")
                    if raw.upper() in special_codes:
                        room.exits[direction] = raw.upper()
                        print(f"    {direction} → {raw.upper()} (special exit)")
                    else:
                        print(f"    Unknown: '{raw}'. Enter a room # or special code (EXIT_TAVERN, etc).")
        print("  Exits updated.")

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
            print(f"  #{aid:>3}  {a.name:<28}  [{a.artifact_type}]  @ {location}")

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
        aid = self.world.next_artifact_id()
        name = prompt("Name")
        if not name:
            print("  Cancelled.")
            return
        desc = prompt("Description")

        # Type
        types = [ArtifactType.GENERIC, ArtifactType.WEAPON, ArtifactType.ARMOR,
                 ArtifactType.CONTAINER, ArtifactType.READABLE, ArtifactType.LIGHT]
        n = choose(types, "Artifact type")
        atype = types[n - 1] if n else ArtifactType.GENERIC

        weight = prompt_int("Weight", 1)
        synonyms_raw = prompt("Synonyms (comma-separated)", "")
        synonyms = [s.strip() for s in synonyms_raw.split(",") if s.strip()]

        a = Artifact(id=aid, name=name, description=desc,
                     artifact_type=atype, weight=weight, synonyms=synonyms,
                     room_id=None)

        if atype == ArtifactType.CONTAINER:
            a.is_container = True
            a.is_open = prompt_bool("Starts open?", False)

        if atype == ArtifactType.READABLE:
            a.read_text = prompt("Text to read")

        if atype == ArtifactType.WEAPON:
            a.damage_dice  = prompt_int("Damage dice", 1)
            a.damage_sides = prompt_int("Damage sides", 6)

        if atype == ArtifactType.ARMOR:
            a.armor_class = prompt_int("Armor class bonus", 1)

        # Place in room
        if self.world.rooms and prompt_bool("Place in a room now?", True):
            rid = self._pick_room("Place in which room?")
            a.room_id = rid

        self.world.artifacts[aid] = a
        print(f"  Artifact #{aid} '{name}' created.")

    def edit_artifact(self) -> None:
        aid = self._pick_artifact("Edit which artifact?")
        if aid is None:
            return
        a = self.world.artifacts[aid]
        print(f"\n  EDIT ARTIFACT #{aid}")
        a.name        = prompt("Name",        a.name)
        a.description = prompt("Description", a.description)
        a.weight      = prompt_int("Weight",  a.weight)
        syns = ", ".join(a.synonyms)
        syns_new = prompt("Synonyms (comma-separated)", syns)
        a.synonyms = [s.strip() for s in syns_new.split(",") if s.strip()]

        if a.artifact_type == ArtifactType.READABLE:
            a.read_text = prompt("Read text", a.read_text or "")

        if a.is_container:
            a.is_open = prompt_bool("Currently open?", a.is_open)

        if prompt_bool("Edit flags (special behaviors)?", False):
            self._edit_artifact_flags(a)

        print("  Artifact updated.")

    def _edit_artifact_flags(self, artifact) -> None:
        """Edit flags for an artifact (tradeable, escape vehicle, quest, event trigger)."""
        print(f"\n  ARTIFACT FLAGS — {artifact.name}")
        print(f"  {hr('─', 40)}")

        flags = dict(artifact.flags)

        # --- TRADEABLE ---
        is_tradeable = prompt_bool("Is this tradeable to NPCs?", flags.get("is_tradeable", False))
        if is_tradeable:
            flags["is_tradeable"] = True
            flags["trade_npc"]       = prompt("Trade with which NPC?",      flags.get("trade_npc", ""))
            flags["trade_dialogue"]  = prompt("Dialogue when traded?",       flags.get("trade_dialogue", ""))
        else:
            flags.pop("is_tradeable",    None)
            flags.pop("trade_npc",       None)
            flags.pop("trade_dialogue",  None)

        # --- ESCAPE VEHICLE ---
        is_escape = prompt_bool("Is this an escape vehicle (boat, portal)?", flags.get("is_escape_vehicle", False))
        if is_escape:
            flags["is_escape_vehicle"] = True
            flags["escape_dialogue"]   = prompt("Dialogue when used to escape?", flags.get("escape_dialogue", "You escape!"))
        else:
            flags.pop("is_escape_vehicle", None)
            flags.pop("escape_dialogue",   None)

        # --- QUEST ITEM ---
        is_quest = prompt_bool("Is this a quest item (can't be sold)?", flags.get("is_quest_item", False))
        if is_quest:
            flags["is_quest_item"] = True
            flags["quest_id"]      = prompt("Quest ID (for tracking)", flags.get("quest_id", ""))
        else:
            flags.pop("is_quest_item", None)
            flags.pop("quest_id",      None)

        # --- EVENT TRIGGER ---
        triggers = prompt_bool("Does using this trigger an event?", bool(flags.get("triggers_event")))
        if triggers:
            flags["triggers_event"] = prompt("Event ID to trigger", flags.get("triggers_event", ""))
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
        # Remove from any container contents
        for a in self.world.artifacts.values():
            if aid in a.contents:
                a.contents.remove(aid)
        print(f"  Artifact #{aid} deleted.")

    def move_artifact(self) -> None:
        aid = self._pick_artifact("Move which artifact?")
        if aid is None:
            return
        a = self.world.artifacts[aid]
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
            print("  2. Add new monster")
            print("  3. Edit monster")
            print("  4. Delete monster")
            print("  0. Back")
            choice = input("\n  > ").strip()

            if choice == "1":
                self.list_monsters()
            elif choice == "2":
                self.add_monster()
            elif choice == "3":
                self.edit_monster()
            elif choice == "4":
                self.delete_monster()
            elif choice == "0":
                break

    def list_monsters(self) -> None:
        if not self.world.monsters:
            print("  No monsters yet.")
            return
        print()
        for mid in sorted(self.world.monsters.keys()):
            m = self.world.monsters[mid]
            location = (f"Room #{m.room_id} {self.world.rooms[m.room_id].name}"
                        if m.room_id in self.world.rooms
                        else f"Room #{m.room_id}")
            print(f"  #{mid:>3}  {m.name:<28}  [{m.attitude}]  HP:{m.hp_max}  @ {location}")

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
        mid = self.world.next_monster_id()
        name = prompt("Name")
        if not name:
            print("  Cancelled.")
            return
        desc = prompt("Description")

        attitudes = [Attitude.HOSTILE, Attitude.NEUTRAL, Attitude.FRIENDLY]
        n = choose(attitudes, "Attitude")
        attitude = attitudes[n - 1] if n else Attitude.HOSTILE

        hp           = prompt_int("HP", 10)
        damage_dice  = prompt_int("Damage dice", 1)
        damage_sides = prompt_int("Damage sides", 6)
        armor_class  = prompt_int("Armor class", 0)
        xp_value     = prompt_int("XP value (0 = auto)", 0)
        dialogue     = prompt("Dialogue (shown on TALK)", "")
        death_msg    = prompt("Death message", "")

        synonyms_raw = prompt("Synonyms (comma-separated)", "")
        synonyms = [s.strip() for s in synonyms_raw.split(",") if s.strip()]

        heal_amount = 0
        heal_cost   = 0
        if attitude in (Attitude.NEUTRAL, Attitude.FRIENDLY):
            if prompt_bool("Can this NPC heal the player?", False):
                heal_amount = prompt_int("HP healed per use", 5)
                heal_cost   = prompt_int("Gold cost per use", 10)

        if not self.world.rooms:
            print("  No rooms exist — monster will be placed in room 1.")
            room_id = 1
        else:
            rid = self._pick_room("Place in which room?")
            room_id = rid if rid is not None else self.world.start_room

        m = Monster(
            id=mid, name=name, description=desc, room_id=room_id,
            attitude=attitude, hp=hp, hp_max=hp,
            damage_dice=damage_dice, damage_sides=damage_sides,
            armor_class=armor_class, xp_value=xp_value,
            dialogue=dialogue, death_message=death_msg,
            heal_amount=heal_amount, heal_cost=heal_cost,
            synonyms=synonyms,
        )
        self.world.monsters[mid] = m
        print(f"  Monster #{mid} '{name}' created.")

    def edit_monster(self) -> None:
        mid = self._pick_monster("Edit which monster?")
        if mid is None:
            return
        m = self.world.monsters[mid]
        print(f"\n  EDIT MONSTER #{mid}")
        m.name         = prompt("Name",         m.name)
        m.description  = prompt("Description",  m.description)
        m.hp           = prompt_int("HP",           m.hp_max)
        m.hp_max       = m.hp
        m.damage_dice  = prompt_int("Damage dice",  m.damage_dice)
        m.damage_sides = prompt_int("Damage sides", m.damage_sides)
        m.armor_class  = prompt_int("Armor class",  m.armor_class)
        m.xp_value     = prompt_int("XP value",     m.xp_value)
        m.dialogue     = prompt("Dialogue",     m.dialogue)
        m.death_message = prompt("Death message", m.death_message)

        attitudes = [Attitude.HOSTILE, Attitude.NEUTRAL, Attitude.FRIENDLY]
        n = choose(attitudes, f"Attitude [{m.attitude}]")
        if n:
            m.attitude = attitudes[n - 1]
            m.aggro = m.attitude == Attitude.HOSTILE

        syns = ", ".join(m.synonyms)
        syns_new = prompt("Synonyms (comma-separated)", syns)
        m.synonyms = [s.strip() for s in syns_new.split(",") if s.strip()]

        if prompt_bool("Edit heal mechanics?", False):
            m.heal_amount = prompt_int("HP healed per use", m.heal_amount)
            m.heal_cost   = prompt_int("Gold cost per use", m.heal_cost)

        print("  Monster updated.")

    def delete_monster(self) -> None:
        mid = self._pick_monster("Delete which monster?")
        if mid is None:
            return
        name = self.world.monsters[mid].name
        if not prompt_bool(f"Delete monster #{mid} '{name}'?", False):
            return
        del self.world.monsters[mid]
        print(f"  Monster #{mid} deleted.")

    # ── Test play ─────────────────────────────────────────────────────────────

    def launch_engine(self) -> None:
        self.world.save(self.path)
        print(f"\n  Saved. Launching engine for '{self.world.title}'...\n")
        import subprocess
        subprocess.call([sys.executable, "engine.py", self.path])


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Adventure Designer")
    parser.add_argument("adventure", nargs="?", default="adventures/sample",
                        help="Path to adventure directory (created if new)")
    args = parser.parse_args()

    designer = Designer(args.adventure)
    designer.run()


if __name__ == "__main__":
    main()
