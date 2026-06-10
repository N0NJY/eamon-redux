"""
engine.py - The game engine.
Handles the command parser and all game commands.
"""

from __future__ import annotations
import sys
from world import World, DIRECTIONS, DIR_ABBREV
from player import Player


# ── Text helpers ──────────────────────────────────────────────────────────────

def wrap(text: str, width: int = 72) -> str:
    """Simple word-wrap."""
    words = text.split()
    lines, line = [], []
    length = 0
    for word in words:
        if length + len(word) + bool(line) > width:
            lines.append(" ".join(line))
            line, length = [word], len(word)
        else:
            line.append(word)
            length += len(word) + bool(line) - 1
    if line:
        lines.append(" ".join(line))
    return "\n".join(lines)


def hr(char: str = "─", width: int = 72) -> str:
    return char * width


# ── Engine ────────────────────────────────────────────────────────────────────

class Engine:

    def __init__(self, world: World, player: Player):
        self.world = world
        self.player = player
        self.running = True

    # ── Room display ──────────────────────────────────────────────────────────

    def describe_room(self, brief: bool = False) -> None:
        room = self.world.get_room(self.player.room_id)
        if room is None:
            print("You are in the void. Something has gone wrong.")
            return

        print(f"\n{hr()}")
        print(f"  {room.name.upper()}")
        print(hr())

        if not brief or room.first_visit:
            print(wrap(room.description))
            room.first_visit = False

        # Exits
        exits = room.exit_list()
        print(f"\nExits: {exits}")

        # Artifacts in room
        artifacts = self.world.artifacts_in_room(room.id)
        if artifacts:
            print("\nYou see:")
            for a in artifacts:
                print(f"  {a.name}")
                if a.is_container and a.is_open:
                    contents = [self.world.artifacts[cid]
                                for cid in a.contents
                                if cid in self.world.artifacts]
                    if contents:
                        for c in contents:
                            print(f"    Inside: {c.name}")
                    else:
                        print(f"    (empty)")
        print()

    # ── Parser ────────────────────────────────────────────────────────────────

    def parse(self, raw: str) -> tuple[str, list[str]]:
        """Return (verb, [rest_of_words])."""
        tokens = raw.strip().lower().split()
        if not tokens:
            return ("", [])
        verb = tokens[0]
        # expand abbreviations for movement
        verb = DIR_ABBREV.get(verb, verb)
        args = tokens[1:]
        return verb, args

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def handle(self, raw: str) -> None:
        verb, args = self.parse(raw)
        if not verb:
            return

        # Movement
        if verb in DIRECTIONS:
            self.cmd_go(verb)
        elif verb == "go":
            if args:
                direction = DIR_ABBREV.get(args[0], args[0])
                self.cmd_go(direction)
            else:
                print("Go where?")
        # Look
        elif verb in ("look", "l"):
            self.describe_room()
        # Inventory
        elif verb in ("inventory", "inv", "i"):
            self.cmd_inventory()
        # Get / Take
        elif verb in ("get", "take", "pick"):
            noun = " ".join(args) if args else ""
            self.cmd_get(noun)
        # Drop
        elif verb == "drop":
            noun = " ".join(args) if args else ""
            self.cmd_drop(noun)
        # Examine
        elif verb in ("examine", "exam", "x", "look at"):
            noun = " ".join(args) if args else ""
            self.cmd_examine(noun)
        # Read
        elif verb == "read":
            noun = " ".join(args) if args else ""
            self.cmd_read(noun)
        # Open
        elif verb == "open":
            noun = " ".join(args) if args else ""
            self.cmd_open(noun)
        # Close
        elif verb == "close":
            noun = " ".join(args) if args else ""
            self.cmd_close(noun)
        # Help
        elif verb in ("help", "?", "h"):
            self.cmd_help()
        # Quit
        elif verb in ("quit", "q", "exit", "bye"):
            self.cmd_quit()
        else:
            print(f"I don't know how to \"{verb}\".")

    # ── Commands ──────────────────────────────────────────────────────────────

    def cmd_go(self, direction: str) -> None:
        room = self.world.get_room(self.player.room_id)
        dest_id = room.exits.get(direction)
        if dest_id is None:
            print("You can't go that way.")
            return
        dest = self.world.get_room(dest_id)
        if dest is None:
            print("That passage leads nowhere. (Data error?)")
            return
        self.player.room_id = dest_id
        self.describe_room()

    def cmd_inventory(self) -> None:
        carried = self.world.artifacts_carried()
        if not carried:
            print("You are carrying nothing.")
            return
        print("You are carrying:")
        for a in carried:
            print(f"  {a.name}")
            if a.is_container and a.is_open:
                contents = [self.world.artifacts[cid]
                            for cid in a.contents
                            if cid in self.world.artifacts]
                for c in contents:
                    print(f"    {c.name}")
        weight = self.player.carried_weight(self.world)
        print(f"\nCarrying weight: {weight}/{self.player.max_carry_weight}")

    def cmd_get(self, noun: str) -> None:
        if not noun:
            print("Get what?")
            return

        room = self.world.get_room(self.player.room_id)
        room_artifacts = self.world.artifacts_in_room(room.id)

        # Also check open containers in the room
        container_contents: list = []
        for a in room_artifacts:
            if a.is_container and a.is_open:
                container_contents += [self.world.artifacts[cid]
                                       for cid in a.contents
                                       if cid in self.world.artifacts]

        target = self.world.find_artifact_by_name(noun, room_artifacts + container_contents)

        if target is None:
            print(f"You don't see any {noun} here.")
            return

        if not self.player.can_carry(target, self.world):
            print(f"The {target.name} is too heavy to carry.")
            return

        # Remove from container if needed
        for a in room_artifacts:
            if a.is_container and target.id in a.contents:
                a.contents.remove(target.id)

        target.room_id = None
        print(f"You pick up the {target.name}.")

    def cmd_drop(self, noun: str) -> None:
        if not noun:
            print("Drop what?")
            return

        carried = self.world.artifacts_carried()
        target = self.world.find_artifact_by_name(noun, carried)

        if target is None:
            print(f"You aren't carrying any {noun}.")
            return

        target.room_id = self.player.room_id
        print(f"You drop the {target.name}.")

    def cmd_examine(self, noun: str) -> None:
        if not noun:
            print("Examine what?")
            return

        # Look in room AND inventory
        room = self.world.get_room(self.player.room_id)
        pool = (self.world.artifacts_in_room(room.id) +
                self.world.artifacts_carried())

        # Also check open containers
        for a in pool[:]:
            if a.is_container and a.is_open:
                pool += [self.world.artifacts[cid]
                         for cid in a.contents
                         if cid in self.world.artifacts]

        target = self.world.find_artifact_by_name(noun, pool)

        if target is None:
            print(f"You don't see any {noun} here.")
            return

        print(f"\n{target.name.upper()}")
        print(wrap(target.description))

        if target.is_container:
            state = "open" if target.is_open else "closed"
            print(f"It is {state}.")
            if target.is_open:
                contents = [self.world.artifacts[cid]
                            for cid in target.contents
                            if cid in self.world.artifacts]
                if contents:
                    print("Inside you see:")
                    for c in contents:
                        print(f"  {c.name}")
                else:
                    print("It is empty.")

    def cmd_read(self, noun: str) -> None:
        if not noun:
            print("Read what?")
            return

        room = self.world.get_room(self.player.room_id)
        pool = (self.world.artifacts_in_room(room.id) +
                self.world.artifacts_carried())
        target = self.world.find_artifact_by_name(noun, pool)

        if target is None:
            print(f"You don't see any {noun} here.")
            return

        if target.read_text:
            print(f"\n{wrap(target.read_text)}")
        else:
            print(f"There is nothing to read on the {target.name}.")

    def cmd_open(self, noun: str) -> None:
        if not noun:
            print("Open what?")
            return

        room = self.world.get_room(self.player.room_id)
        pool = (self.world.artifacts_in_room(room.id) +
                self.world.artifacts_carried())
        target = self.world.find_artifact_by_name(noun, pool)

        if target is None:
            print(f"You don't see any {noun} here.")
            return

        if not target.is_container:
            print(f"You can't open the {target.name}.")
            return

        if target.is_open:
            print(f"The {target.name} is already open.")
            return

        target.is_open = True
        print(f"You open the {target.name}.")
        contents = [self.world.artifacts[cid]
                    for cid in target.contents
                    if cid in self.world.artifacts]
        if contents:
            print("Inside you see:")
            for c in contents:
                print(f"  {c.name}")
        else:
            print("It is empty.")

    def cmd_close(self, noun: str) -> None:
        if not noun:
            print("Close what?")
            return

        room = self.world.get_room(self.player.room_id)
        pool = (self.world.artifacts_in_room(room.id) +
                self.world.artifacts_carried())
        target = self.world.find_artifact_by_name(noun, pool)

        if target is None:
            print(f"You don't see any {noun} here.")
            return

        if not target.is_container:
            print(f"You can't close the {target.name}.")
            return

        if not target.is_open:
            print(f"The {target.name} is already closed.")
            return

        target.is_open = False
        print(f"You close the {target.name}.")

    def cmd_help(self) -> None:
        print("""
Commands:
  NORTH / SOUTH / EAST / WEST / UP / DOWN   Move (or N/S/E/W/U/D)
  GO <direction>                             Move
  LOOK  (or L)                               Describe current room
  INVENTORY  (or I)                          List carried items
  GET <item>  / TAKE <item>                  Pick up an item
  DROP <item>                                Drop an item
  EXAMINE <item>  (or X <item>)              Inspect an item closely
  READ <item>                                Read text on an item
  OPEN <item>  / CLOSE <item>               Open or close a container
  HELP  (or ?)                               Show this list
  QUIT                                       End the game
""")

    def cmd_quit(self) -> None:
        print("\nFarewell, adventurer.\n")
        self.running = False

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        print(f"\n{'═' * 72}")
        print(f"  {self.world.title.upper()}")
        if self.world.author:
            print(f"  by {self.world.author}")
        print(f"{'═' * 72}")

        if self.world.intro:
            print(f"\n{wrap(self.world.intro)}")

        print('\nType HELP for a list of commands.\n')
        self.describe_room()

        while self.running:
            try:
                raw = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                self.cmd_quit()
                break

            if raw:
                self.handle(raw)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import os
    import argparse

    parser = argparse.ArgumentParser(description="Text adventure engine")
    parser.add_argument("adventure", nargs="?", default="adventures/sample",
                        help="Path to adventure directory")
    parser.add_argument("--name", default="Adventurer", help="Player name")
    args = parser.parse_args()

    if not os.path.isdir(args.adventure):
        print(f"Adventure not found: {args.adventure}")
        sys.exit(1)

    world = World.load(args.adventure)
    player = Player(name=args.name, room_id=world.start_room)
    engine = Engine(world, player)
    engine.run()


if __name__ == "__main__":
    main()
