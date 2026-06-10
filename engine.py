"""
engine.py - The game engine.
Handles the command parser, all game commands, combat, and locked doors.

Exit codes:
  0 = player quit normally
  1 = adventure completed (win condition met)
  2 = player died
"""

from __future__ import annotations
import sys
import random
from world import World, DIRECTIONS, DIR_ABBREV, Attitude
from player import Player


# ── ANSI Color ────────────────────────────────────────────────────────────────

class C:
    RESET      = "\033[0m"
    HR         = "\033[2;32m"
    ROOM_NAME  = "\033[1;32m"
    ROOM_DESC  = "\033[0;32m"
    EXITS      = "\033[2;32m"

    ITEM       = "\033[0;33m"
    ITEM_LABEL = "\033[2;33m"

    SYS        = "\033[0;36m"
    ERROR      = "\033[0;31m"
    WARN       = "\033[0;35m"

    COMBAT_HIT = "\033[1;31m"
    COMBAT_DMG = "\033[0;31m"
    COMBAT_WIN = "\033[1;33m"
    COMBAT_DIE = "\033[1;31m"

    TITLE      = "\033[1;32m"
    INTRO      = "\033[0;32m"
    HELP       = "\033[2;36m"

def c(color: str, text: str) -> str:
    return f"{color}{text}{C.RESET}"


# ── Text helpers ──────────────────────────────────────────────────────────────

def wrap(text: str, width: int = 72) -> str:
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
    return c(C.HR, char * width)

def roll(dice: int, sides: int) -> int:
    return sum(random.randint(1, sides) for _ in range(dice))


# ── Engine ────────────────────────────────────────────────────────────────────

class Engine:

    def __init__(self, world: World, player: Player):
        self.world = world
        self.player = player
        self.running = True
        self.exit_code = 0      # 0=quit, 1=completed, 2=died

    # ── Room display ──────────────────────────────────────────────────────────

    def describe_room(self, brief: bool = False) -> None:
        room = self.world.get_room(self.player.room_id)
        if room is None:
            print(c(C.ERROR, "You are in the void. Something has gone wrong."))
            return

        print(f"\n{hr()}")
        print(c(C.ROOM_NAME, f"  {room.name.upper()}"))
        print(hr())

        if not brief or room.first_visit:
            print(c(C.ROOM_DESC, wrap(room.description)))
            room.first_visit = False

        # Exits — note locked ones
        exit_parts = []
        for direction, dest_id in room.exits.items():
            lock = room.locked_exits.get(direction)
            if lock:
                key_name = self._key_name(lock)
                exit_parts.append(f"{direction} {c(C.ERROR, '[locked]')}")
            else:
                exit_parts.append(direction)
        exits_str = ", ".join(exit_parts) if exit_parts else "none"
        print(c(C.EXITS, f"\nExits: ") + exits_str)

        # Monsters
        monsters = self.world.monsters_in_room(room.id)
        if monsters:
            print()
            for m in monsters:
                if m.attitude == Attitude.FRIENDLY:
                    tag = c(C.SYS, " (friendly)")
                elif m.attitude == Attitude.NEUTRAL:
                    tag = c(C.EXITS, " (neutral)")
                else:
                    tag = ""
                print(c(C.WARN, f"  {m.name}") + tag)

        # Artifacts
        artifacts = self.world.artifacts_in_room(room.id)
        if artifacts:
            print(c(C.ITEM_LABEL, "\nYou see:"))
            for a in artifacts:
                print(c(C.ITEM, f"  {a.name}"))
                if a.is_container and a.is_open:
                    contents = [self.world.artifacts[cid]
                                for cid in a.contents if cid in self.world.artifacts]
                    if contents:
                        for cont in contents:
                            print(c(C.ITEM_LABEL, "    Inside: ") + c(C.ITEM, cont.name))
                    else:
                        print(c(C.ITEM_LABEL, "    (empty)"))
        print()

    def _key_name(self, artifact_id: int) -> str:
        a = self.world.artifacts.get(artifact_id)
        return a.name if a else f"key #{artifact_id}"

    # ── Monster auto-attack ───────────────────────────────────────────────────

    def monster_round(self) -> None:
        monsters = self.world.monsters_in_room(self.player.room_id)
        for m in monsters:
            if not m.aggro:
                continue
            # Agility: dodge chance — each point above 10 gives 5% dodge
            dodge_chance = max(0, self.player.agility_bonus * 5)
            if dodge_chance > 0 and random.randint(1, 100) <= dodge_chance:
                print(c(C.SYS, f"  {m.name} swings — you dodge!"))
                continue
            dmg = max(0, roll(m.damage_dice, m.damage_sides)
                      - self.player.armor_class(self.world))
            self.player.hp -= dmg
            if dmg > 0:
                print(c(C.COMBAT_HIT,
                        f"  {m.name} hits you for {c(C.COMBAT_DMG, str(dmg))} damage!"))
            else:
                print(c(C.WARN, f"  {m.name} attacks but your armor absorbs the blow!"))
            if not self.player.is_alive:
                self._player_death()
                return

    def _player_death(self) -> None:
        print(f"\n{c(C.COMBAT_DIE, '══ YOU HAVE DIED ══')}")
        print(c(C.ROOM_DESC, "Your adventure ends here. The darkness claims you."))
        self.exit_code = 2
        self.running = False

    # ── Parser ────────────────────────────────────────────────────────────────

    def parse(self, raw: str) -> tuple[str, list[str]]:
        tokens = raw.strip().lower().split()
        if not tokens:
            return ("", [])
        verb = DIR_ABBREV.get(tokens[0], tokens[0])
        return verb, tokens[1:]

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def handle(self, raw: str) -> None:
        verb, args = self.parse(raw)
        if not verb:
            return

        if verb in DIRECTIONS:
            self.cmd_go(verb)
        elif verb == "go":
            self.cmd_go(DIR_ABBREV.get(args[0], args[0])) if args else print(c(C.ERROR, "Go where?"))
        elif verb in ("look", "l"):
            self.describe_room()
        elif verb in ("inventory", "inv", "i"):
            self.cmd_inventory()
        elif verb in ("get", "take", "pick"):
            self.cmd_get(" ".join(args))
        elif verb == "drop":
            self.cmd_drop(" ".join(args))
        elif verb in ("examine", "exam", "x"):
            self.cmd_examine(" ".join(args))
        elif verb == "read":
            self.cmd_read(" ".join(args))
        elif verb == "open":
            self.cmd_open(" ".join(args))
        elif verb == "close":
            self.cmd_close(" ".join(args))
        elif verb in ("unlock", "lock"):
            self.cmd_unlock(" ".join(args))
        elif verb in ("attack", "kill", "fight", "hit", "stab", "slash"):
            self.cmd_attack(" ".join(args))
        elif verb in ("health", "hp", "status"):
            self.cmd_health()
        elif verb in ("flee", "run", "escape"):
            self.cmd_flee()
        elif verb in ("help", "?", "h"):
            self.cmd_help()
        elif verb in ("quit", "q", "exit", "bye"):
            self.cmd_quit()
        else:
            print(c(C.ERROR, f"I don't know how to \"{verb}\"."))

    # ── Movement ──────────────────────────────────────────────────────────────

    def cmd_go(self, direction: str) -> None:
        hostiles = [m for m in self.world.monsters_in_room(self.player.room_id)
                    if m.aggro]
        if hostiles:
            print(c(C.ERROR, "You can't flee while in combat! (Try FLEE to escape)"))
            return

        room = self.world.get_room(self.player.room_id)
        dest_id = room.exits.get(direction)
        if dest_id is None:
            print(c(C.ERROR, "You can't go that way."))
            return

        # ── Locked door check ──────────────────────────────────────────────
        lock_id = room.locked_exits.get(direction)
        if lock_id:
            # Check if player carries the key
            key = self.world.find_artifact_by_name(
                "", candidates=[a for a in self.world.artifacts_carried()
                                if a.id == lock_id])
            # Direct id match
            key = next((a for a in self.world.artifacts_carried()
                        if a.id == lock_id), None)
            if key is None:
                key_name = self._key_name(lock_id)
                print(c(C.ERROR, f"The way {direction} is locked.") +
                      c(C.EXITS, f" (requires: {key_name})"))
                return
            else:
                # Auto-unlock
                del room.locked_exits[direction]
                print(c(C.SYS, f"You use the {key.name} to unlock the door."))

        dest = self.world.get_room(dest_id)
        if dest is None:
            print(c(C.ERROR, "That passage leads nowhere. (Data error?)"))
            return

        self.player.room_id = dest_id
        self.describe_room()
        self.monster_round()

    # ── Inventory ─────────────────────────────────────────────────────────────

    def cmd_inventory(self) -> None:
        carried = self.world.artifacts_carried()
        if not carried:
            print(c(C.SYS, "You are carrying nothing."))
        else:
            print(c(C.ITEM_LABEL, "You are carrying:"))
            for a in carried:
                print(c(C.ITEM, f"  {a.name}"))
                if a.is_container and a.is_open:
                    contents = [self.world.artifacts[cid]
                                for cid in a.contents if cid in self.world.artifacts]
                    for cont in contents:
                        print(c(C.ITEM_LABEL, "    ") + c(C.ITEM, cont.name))
            weight = self.player.carried_weight(self.world)
            print(c(C.EXITS,
                    f"\nCarrying weight: {weight}/{self.player.max_carry_weight} gronds"))
        print(c(C.SYS, f"\n{self.player.health_bar()}"))

    # ── Get / Drop ────────────────────────────────────────────────────────────

    def cmd_get(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Get what?"))
            return
        room = self.world.get_room(self.player.room_id)
        room_artifacts = self.world.artifacts_in_room(room.id)
        container_contents: list = []
        for a in room_artifacts:
            if a.is_container and a.is_open:
                container_contents += [self.world.artifacts[cid]
                                       for cid in a.contents if cid in self.world.artifacts]
        target = self.world.find_artifact_by_name(noun, room_artifacts + container_contents)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        if not self.player.can_carry(target, self.world):
            print(c(C.ERROR,
                    f"The {target.name} is too heavy. "
                    f"(Carrying {self.player.carried_weight(self.world)}"
                    f"/{self.player.max_carry_weight} gronds)"))
            return
        for a in room_artifacts:
            if a.is_container and target.id in a.contents:
                a.contents.remove(target.id)
        target.room_id = None
        print(c(C.SYS, f"You pick up the {target.name}."))
        self.monster_round()

    def cmd_drop(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Drop what?"))
            return
        target = self.world.find_artifact_by_name(noun, self.world.artifacts_carried())
        if target is None:
            print(c(C.ERROR, f"You aren't carrying any {noun}."))
            return
        target.room_id = self.player.room_id
        print(c(C.SYS, f"You drop the {target.name}."))

    # ── Examine / Read ────────────────────────────────────────────────────────

    def cmd_examine(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Examine what?"))
            return
        room = self.world.get_room(self.player.room_id)
        pool = self.world.artifacts_in_room(room.id) + self.world.artifacts_carried()
        for a in pool[:]:
            if a.is_container and a.is_open:
                pool += [self.world.artifacts[cid]
                         for cid in a.contents if cid in self.world.artifacts]

        monster = self.world.find_monster_by_name(
            noun, self.world.monsters_in_room(room.id))
        if monster:
            print(f"\n{c(C.WARN, monster.name.upper())}")
            print(c(C.ROOM_DESC, wrap(monster.description)))
            print(c(C.WARN, f"{monster.name} {monster.health_desc()}."))
            return

        target = self.world.find_artifact_by_name(noun, pool)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        print(f"\n{c(C.ROOM_NAME, target.name.upper())}")
        print(c(C.ROOM_DESC, wrap(target.description)))
        if target.is_container:
            state = "open" if target.is_open else "closed"
            print(c(C.SYS, f"It is {state}."))
            if target.is_open:
                contents = [self.world.artifacts[cid]
                            for cid in target.contents if cid in self.world.artifacts]
                if contents:
                    print(c(C.ITEM_LABEL, "Inside you see:"))
                    for cont in contents:
                        print(c(C.ITEM, f"  {cont.name}"))
                else:
                    print(c(C.ITEM_LABEL, "It is empty."))

    def cmd_read(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Read what?"))
            return
        room = self.world.get_room(self.player.room_id)
        pool = self.world.artifacts_in_room(room.id) + self.world.artifacts_carried()
        target = self.world.find_artifact_by_name(noun, pool)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        if target.read_text:
            print(f"\n{c(C.ROOM_NAME, wrap(target.read_text))}")
        else:
            print(c(C.ERROR, f"There is nothing to read on the {target.name}."))

    # ── Open / Close ──────────────────────────────────────────────────────────

    def cmd_open(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Open what?"))
            return
        room = self.world.get_room(self.player.room_id)
        pool = self.world.artifacts_in_room(room.id) + self.world.artifacts_carried()
        target = self.world.find_artifact_by_name(noun, pool)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        if not target.is_container:
            print(c(C.ERROR, f"You can't open the {target.name}."))
            return
        if target.is_open:
            print(c(C.WARN, f"The {target.name} is already open."))
            return
        target.is_open = True
        print(c(C.SYS, f"You open the {target.name}."))
        contents = [self.world.artifacts[cid]
                    for cid in target.contents if cid in self.world.artifacts]
        if contents:
            print(c(C.ITEM_LABEL, "Inside you see:"))
            for cont in contents:
                print(c(C.ITEM, f"  {cont.name}"))
        else:
            print(c(C.ITEM_LABEL, "It is empty."))
        self.monster_round()

    def cmd_close(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Close what?"))
            return
        room = self.world.get_room(self.player.room_id)
        pool = self.world.artifacts_in_room(room.id) + self.world.artifacts_carried()
        target = self.world.find_artifact_by_name(noun, pool)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        if not target.is_container:
            print(c(C.ERROR, f"You can't close the {target.name}."))
            return
        if not target.is_open:
            print(c(C.WARN, f"The {target.name} is already closed."))
            return
        target.is_open = False
        print(c(C.SYS, f"You close the {target.name}."))

    # ── Unlock (manual) ───────────────────────────────────────────────────────

    def cmd_unlock(self, noun: str) -> None:
        """UNLOCK <direction> — try to unlock a locked exit manually."""
        if not noun:
            print(c(C.ERROR, "Unlock which direction?"))
            return
        direction = DIR_ABBREV.get(noun, noun)
        room = self.world.get_room(self.player.room_id)
        if direction not in room.exits:
            print(c(C.ERROR, f"There's no exit to the {direction}."))
            return
        lock_id = room.locked_exits.get(direction)
        if not lock_id:
            print(c(C.SYS, f"The way {direction} is already unlocked."))
            return
        key = next((a for a in self.world.artifacts_carried() if a.id == lock_id), None)
        if key is None:
            key_name = self._key_name(lock_id)
            print(c(C.ERROR, f"You need the {key_name} to unlock that."))
            return
        del room.locked_exits[direction]
        print(c(C.SYS, f"You use the {key.name} to unlock the {direction} exit."))

    # ── Combat ────────────────────────────────────────────────────────────────

    def cmd_attack(self, noun: str) -> None:
        if not noun:
            monsters = self.world.monsters_in_room(self.player.room_id)
            if len(monsters) == 1:
                target = monsters[0]
            else:
                print(c(C.ERROR, "Attack what?"))
                return
        else:
            target = self.world.find_monster_by_name(
                noun, self.world.monsters_in_room(self.player.room_id))
            if target is None:
                print(c(C.ERROR, f"You don't see any {noun} here."))
                return

        if not target.is_alive:
            print(c(C.ERROR, f"The {target.name} is already dead."))
            return

        if target.attitude == Attitude.FRIENDLY:
            print(c(C.WARN,
                    f"You raise your weapon against {target.name}, "
                    f"but can't bring yourself to strike a friend."))
            return

        target.aggro = True

        # Player attacks — agility bonus adds to hit roll
        weapon = self.player.best_weapon(self.world)
        if weapon:
            p_dice, p_sides = weapon.damage_dice, weapon.damage_sides
            weapon_name = weapon.name
        else:
            p_dice, p_sides = self.player.damage_dice, self.player.damage_sides
            weapon_name = "your fists"

        # Agility bonus: +1 damage per 2 agility above 10
        bonus = max(0, self.player.agility_bonus)
        p_dmg = max(0, roll(p_dice, p_sides) + bonus - target.armor_class)
        target.hp -= p_dmg

        if p_dmg > 0:
            print(c(C.COMBAT_HIT,
                    f"  You hit {c(C.WARN, target.name)} with {weapon_name} "
                    f"for {c(C.COMBAT_DMG, str(p_dmg))} damage!"))
        else:
            print(c(C.EXITS, f"  You swing at {c(C.WARN, target.name)} but deal no damage."))

        if target.hp <= 0:
            target.is_alive = False
            target.hp = 0
            death_msg = (target.death_message or
                         f"The {target.name} staggers and collapses, dead.")
            print(f"\n{c(C.COMBAT_WIN, death_msg)}")
            if target.loot_id and target.loot_id in self.world.artifacts:
                loot = self.world.artifacts[target.loot_id]
                loot.room_id = self.player.room_id
                print(c(C.ITEM, f"  {loot.name} falls to the ground."))
            # Check win condition
            self._check_win()
            return

        print(c(C.WARN, f"  {target.name} {target.health_desc()}."))
        self._monster_attack(target)

    def _monster_attack(self, monster) -> None:
        dodge_chance = max(0, self.player.agility_bonus * 5)
        if dodge_chance > 0 and random.randint(1, 100) <= dodge_chance:
            print(c(C.SYS, f"  {monster.name} swings — you dodge!"))
            print(c(C.SYS, f"  {self.player.health_bar()}"))
            return
        dmg = max(0, roll(monster.damage_dice, monster.damage_sides)
                  - self.player.armor_class(self.world))
        if dmg > 0:
            self.player.hp -= dmg
            print(c(C.COMBAT_HIT,
                    f"  {c(C.WARN, monster.name)} hits you for "
                    f"{c(C.COMBAT_DMG, str(dmg))} damage!"))
        else:
            print(c(C.EXITS,
                    f"  {c(C.WARN, monster.name)} attacks but your armor deflects the blow!"))
        print(c(C.SYS, f"  {self.player.health_bar()}"))
        if not self.player.is_alive:
            self._player_death()

    def cmd_flee(self) -> None:
        room = self.world.get_room(self.player.room_id)
        if not room.exits:
            print(c(C.ERROR, "There's nowhere to run!"))
            return
        hostiles = [m for m in self.world.monsters_in_room(self.player.room_id)
                    if m.aggro]
        if hostiles:
            print(c(C.WARN, "You turn to run..."))
            for m in hostiles:
                self._monster_attack(m)
                if not self.player.is_alive:
                    return
        direction = random.choice(list(room.exits.keys()))
        dest_id = room.exits[direction]
        self.player.room_id = dest_id
        print(c(C.SYS, f"  You flee {direction}!"))
        self.describe_room()
        self.monster_round()

    def cmd_health(self) -> None:
        print(c(C.SYS, f"\n{self.player.health_bar()}"))
        weapon = self.player.best_weapon(self.world)
        if weapon:
            print(c(C.ITEM,
                    f"  Weapon: {weapon.name} "
                    f"({weapon.damage_dice}d{weapon.damage_sides}"
                    f"+{max(0,self.player.agility_bonus)})"))
        else:
            print(c(C.EXITS,
                    f"  Weapon: unarmed "
                    f"({self.player.damage_dice}d{self.player.damage_sides}"
                    f"+{max(0,self.player.agility_bonus)})"))
        print(c(C.EXITS, f"  Armor class : {self.player.armor_class(self.world)}"))
        print(c(C.EXITS, f"  Agility     : {self.player.agility} "
                         f"(dodge {max(0,self.player.agility_bonus)*5}%)"))

    # ── Win condition ─────────────────────────────────────────────────────────

    def _check_win(self) -> None:
        """Check if the adventure's win condition is met."""
        if not self.world.win_condition:
            return
        wtype = self.world.win_condition.get("type")

        if wtype == "kill_all":
            # Win when all monsters are dead
            if all(not m.is_alive for m in self.world.monsters.values()):
                self._trigger_win()

        elif wtype == "kill_monster":
            # Win when a specific monster is dead
            mid = self.world.win_condition.get("monster_id")
            m = self.world.monsters.get(mid)
            if m and not m.is_alive:
                self._trigger_win()

        elif wtype == "reach_room":
            # Win when player enters a specific room
            rid = self.world.win_condition.get("room_id")
            if self.player.room_id == rid:
                self._trigger_win()

        elif wtype == "carry_artifact":
            # Win when player carries a specific artifact
            aid = self.world.win_condition.get("artifact_id")
            if any(a.id == aid for a in self.world.artifacts_carried()):
                self._trigger_win()

    def _trigger_win(self) -> None:
        msg = self.world.win_condition.get(
            "message", "You have completed the adventure!")
        print(f"\n{c(C.COMBAT_WIN, '═' * 72)}")
        print(c(C.COMBAT_WIN, f"  {msg}"))
        print(c(C.COMBAT_WIN, '═' * 72))
        self.exit_code = 1
        self.running = False

    # ── Help / Quit ───────────────────────────────────────────────────────────

    def cmd_help(self) -> None:
        h, hi, w = C.HELP, C.EXITS, C.WARN
        print(f"""
{c(hi, 'Movement:')}
{c(h, '  NORTH/SOUTH/EAST/WEST/UP/DOWN')}  {c(hi, '(or N/S/E/W/U/D)')}
{c(h, '  FLEE')}                            {c(hi, 'Escape combat in a random direction')}

{c(hi, 'Actions:')}
{c(h, '  LOOK (L)')}                        {c(hi, 'Describe current room')}
{c(h, '  INVENTORY (I)')}                   {c(hi, 'List carried items and health')}
{c(h, '  GET / TAKE <item>')}               {c(hi, 'Pick up an item')}
{c(h, '  DROP <item>')}                     {c(hi, 'Drop an item')}
{c(h, '  EXAMINE / X <thing>')}             {c(hi, 'Inspect item or monster')}
{c(h, '  READ <item>')}                     {c(hi, 'Read text on an item')}
{c(h, '  OPEN / CLOSE <item>')}             {c(hi, 'Open or close a container')}
{c(h, '  UNLOCK <direction>')}              {c(hi, 'Unlock a locked exit (if you have the key)')}

{c(w, 'Combat:')}
{c(h, '  ATTACK / KILL <monster>')}         {c(w, 'Attack a monster')}
{c(h, '  HEALTH / HP / STATUS')}            {c(w, 'Show your health and combat stats')}

{c(hi, 'Other:')}
{c(h, '  HELP (?)')}                        {c(hi, 'Show this list')}
{c(h, '  QUIT')}                            {c(hi, 'End the game')}
""")

    def cmd_quit(self) -> None:
        print(c(C.ROOM_DESC, "\nFarewell, adventurer.\n"))
        self.exit_code = 0
        self.running = False

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> int:
        print(f"\n{c(C.HR, '═' * 72)}")
        print(c(C.TITLE, f"  {self.world.title.upper()}"))
        if self.world.author:
            print(c(C.ROOM_DESC, f"  by {self.world.author}"))
        print(c(C.HR, '═' * 72))
        if self.world.intro:
            print(f"\n{c(C.INTRO, wrap(self.world.intro))}")
        print(c(C.EXITS, '\nType HELP for a list of commands.\n'))
        self.describe_room()
        self.monster_round()

        while self.running:
            try:
                raw = input(c(C.ROOM_NAME, "> ")).strip()
            except (EOFError, KeyboardInterrupt):
                self.cmd_quit()
                break
            if raw:
                self.handle(raw)
                # Check room-based win condition after every command
                if self.running:
                    self._check_win()

        return self.exit_code


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import os, argparse
    parser = argparse.ArgumentParser(description="Text adventure engine")
    parser.add_argument("adventure", nargs="?", default="adventures/sample",
                        help="Path to adventure directory")
    parser.add_argument("--name",      default="Adventurer")
    parser.add_argument("--hardiness", type=int, default=10)
    parser.add_argument("--agility",   type=int, default=10)
    parser.add_argument("--charisma",  type=int, default=10)
    parser.add_argument("--hp",        type=int, default=0)
    args = parser.parse_args()

    if not os.path.isdir(args.adventure):
        print(c(C.ERROR, f"Adventure not found: {args.adventure}"))
        sys.exit(1)

    world = World.load(args.adventure)

    # Build player from character stats
    player = Player(
        name=args.name,
        room_id=world.start_room,
        hardiness=args.hardiness,
        agility=args.agility,
        charisma=args.charisma,
    )
    # HP from character file, or full if not set
    player.hp = args.hp if args.hp > 0 else player.hp_max
    # Carry capacity from hardiness
    player.max_carry_weight = args.hardiness * 10

    engine = Engine(world, player)
    exit_code = engine.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
