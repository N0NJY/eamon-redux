"""
engine.py - Eamon Redux game engine.

Exit codes: 0=quit, 1=completed, 2=died
"""

from __future__ import annotations

import sys
import os
import json
import random

# ── readline: arrow-key history + tab completion ──────────────────────────────

try:
    import readline
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass  # Windows fallback

from world import World, DIRECTIONS, DIR_ABBREV, Attitude, ArtifactType
from player import Player, slot_for_type, EQUIP_SLOTS
from save_system import (
    save_game as save_game_slotted,
    load_game as load_game_slotted,
    get_existing_saves,
)

# ── Colors ────────────────────────────────────────────────────────────────────

class C:
    RESET      = "\033[0m"
    HR         = "\033[2;32m"
    ROOM_NAME  = "\033[1;32m"
    ROOM_DESC  = "\033[0;32m"
    EXITS      = "\033[2;32m"
    ITEM       = "\033[0;33m"
    ITEM_LABEL = "\033[2;33m"
    EQUIPPED   = "\033[1;33m"
    SYS        = "\033[0;36m"
    ERROR      = "\033[0;31m"
    WARN       = "\033[0;35m"
    COMBAT_HIT = "\033[1;31m"
    COMBAT_DMG = "\033[0;31m"
    COMBAT_WIN = "\033[1;33m"
    COMBAT_DIE = "\033[1;31m"
    SPELL      = "\033[1;36m"
    HEAL_COLOR = "\033[0;32m"
    MANA_COLOR = "\033[2;36m"
    TITLE      = "\033[1;32m"
    INTRO      = "\033[0;32m"
    HELP       = "\033[2;36m"

def c(color: str, text: str) -> str:
    return f"{color}{text}{C.RESET}"

MAX_POTIONS = 2

def potion_count(world) -> int:
    return sum(1 for a in world.artifacts_carried()
               if a.artifact_type == "potion")

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

SPELL_DEFS = {
    "heal":     {"name": "Heal",     "cost": 4},
    "fireball": {"name": "Fireball", "cost": 6},
    "shield":   {"name": "Shield",   "cost": 3},
    "light":    {"name": "Light",    "cost": 2},
}

# ── XP and leveling ───────────────────────────────────────────────────────────

XP_LEVELS = [0, 500, 695, 1000, 1500, 1900, 2500, 3800, 5000, 9000, 15000]
MAX_LEVEL = len(XP_LEVELS)

def level_for_xp(xp: int) -> int:
    level = 1
    for i, threshold in enumerate(XP_LEVELS, 1):
        if xp >= threshold:
            level = i
    return min(level, MAX_LEVEL)

def xp_for_next_level(level: int) -> int:
    if level >= MAX_LEVEL:
        return XP_LEVELS[-1]
    return XP_LEVELS[level]

def monster_xp(monster) -> int:
    if monster.xp_value > 0:
        return monster.xp_value
    return monster.hp_max + (monster.damage_dice * monster.damage_sides * 2)

# ── Save / Load ───────────────────────────────────────────────────────────────

SAVE_DIR = "stored_games"

def save_game(engine: "Engine", adv_path: str, save_name: str) -> bool:
    """Serialise full mid-game state to stored_games/<save_name>.json."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    p = engine.player
    player_data = {
        "name":          p.name,
        "char_class":    p.char_class,
        "room_id":       p.room_id,
        "hardiness":     p.hardiness,
        "agility":       p.agility,
        "charisma":      p.charisma,
        "intelligence":  p.intelligence,
        "strength":      p.strength,
        "hp":            p.hp,
        "mana":          p.mana,
        "gold":          p.gold,
        "spells":        p.spells,
        "equipped":      p.equipped,
        "xp":            p.xp,
        "level":         p.level,
        "xp_gained":     p.xp_gained,
        "shield_rounds": p.shield_rounds,
    }
    artifacts_state = {str(aid): a.room_id for aid, a in engine.world.artifacts.items()}
    monsters_state  = {
        str(mid): {"hp": m.hp, "is_alive": m.is_alive, "aggro": m.aggro}
        for mid, m in engine.world.monsters.items()
    }
    rooms_state = {
        str(rid): {"first_visit": r.first_visit, "locked_exits": r.locked_exits}
        for rid, r in engine.world.rooms.items()
    }
    save_data = {
        "save_name":    save_name,
        "adv_path":     adv_path,
        "light_active": engine.light_active,
        "player":       player_data,
        "artifacts":    artifacts_state,
        "monsters":     monsters_state,
        "rooms":        rooms_state,
    }
    safe = save_name.lower().replace(" ", "_")
    with open(os.path.join(SAVE_DIR, f"{safe}.json"), "w") as f:
        json.dump(save_data, f, indent=2)
    return True

def load_game(save_name: str) -> dict | None:
    safe = save_name.lower().replace(" ", "_")
    path = os.path.join(SAVE_DIR, f"{safe}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def apply_save_state(engine: "Engine", save_data: dict) -> None:
    """Restore mutable world/player state from a loaded save dict."""
    p  = engine.player
    pd = save_data["player"]
    p.room_id       = pd["room_id"]
    p.hp            = pd["hp"]
    p.mana          = pd["mana"]
    p.gold          = pd["gold"]
    p.xp            = pd["xp"]
    p.level         = pd["level"]
    p.xp_gained     = pd.get("xp_gained", 0)
    p.shield_rounds = pd.get("shield_rounds", 0)
    p.equipped      = pd["equipped"]
    for slot in p.equipped:
        v = p.equipped[slot]
        p.equipped[slot] = int(v) if v is not None else None
    engine.light_active = save_data.get("light_active", False)
    for aid_str, room_id in save_data["artifacts"].items():
        aid = int(aid_str)
        if aid in engine.world.artifacts:
            engine.world.artifacts[aid].room_id = room_id
    for mid_str, mstate in save_data["monsters"].items():
        mid = int(mid_str)
        if mid in engine.world.monsters:
            m = engine.world.monsters[mid]
            m.hp       = mstate["hp"]
            m.is_alive = mstate["is_alive"]
            m.aggro    = mstate["aggro"]
    for rid_str, rstate in save_data["rooms"].items():
        rid = int(rid_str)
        if rid in engine.world.rooms:
            r = engine.world.rooms[rid]
            r.first_visit  = rstate["first_visit"]
            r.locked_exits = rstate["locked_exits"]

# ── Engine ────────────────────────────────────────────────────────────────────

class Engine:

    def __init__(self, world: World, player: Player):
        self.world        = world
        self.player       = player
        self.running      = True
        self.exit_code    = 0
        self.light_active = False
        self._adv_path    = ""

    # ── Room display ──────────────────────────────────────────────────────────

    def describe_room(self, brief: bool = False) -> None:
        room = self.world.get_room(self.player.room_id)
        if room is None:
            print(c(C.ERROR, "You are in the void."))
            return
        print(f"\n{hr()}")
        print(c(C.ROOM_NAME, f" {room.name.upper()}"))
        print(hr())
        if room.is_dark and not self.light_active:
            print(c(C.ROOM_DESC, "It is pitch dark. You can't see a thing."))
            print(c(C.EXITS, "\nExits: unknown"))
            print()
            return
        if not brief or room.first_visit:
            print(c(C.ROOM_DESC, wrap(room.description)))
            room.first_visit = False
        exit_parts = []
        for direction in room.exits:
            if room.locked_exits.get(direction):
                exit_parts.append(f"{direction} {c(C.ERROR, '[locked]')}")
            else:
                exit_parts.append(direction)
        print(c(C.EXITS, "\nExits: ") + (", ".join(exit_parts) or "none"))
        monsters = self.world.monsters_in_room(room.id)
        if monsters:
            print()
            for m in monsters:
                tag = (c(C.SYS,  " (friendly)") if m.attitude == Attitude.FRIENDLY
                       else c(C.EXITS, " (neutral)") if m.attitude == Attitude.NEUTRAL
                       else "")
                print(c(C.WARN, f" {m.name}") + tag)
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
                            print(c(C.ITEM_LABEL, "   Inside: ") + c(C.ITEM, cont.name))
                    else:
                        print(c(C.ITEM_LABEL, "   (empty)"))
        print()

    def _key_name(self, artifact_id: int) -> str:
        a = self.world.artifacts.get(artifact_id)
        return a.name if a else f"key #{artifact_id}"

    # ── Monster attacks ───────────────────────────────────────────────────────

    def monster_round(self) -> None:
        for m in self.world.monsters_in_room(self.player.room_id):
            if not m.aggro:
                continue
            dodge = max(0, self.player.agility_bonus * 5)
            if dodge > 0 and random.randint(1, 100) <= dodge:
                print(c(C.SYS, f" {m.name} swings — you dodge!"))
                continue
            dmg = max(0, roll(m.damage_dice, m.damage_sides)
                      - self.player.armor_class(self.world))
            self.player.hp -= dmg
            if dmg > 0:
                print(c(C.COMBAT_HIT,
                        f" {m.name} hits you for {c(C.COMBAT_DMG, str(dmg))} damage!"))
            else:
                print(c(C.WARN, f" {m.name} attacks but armor absorbs it!"))
            if not self.player.is_alive:
                self._player_death()
                return

    def _tick_shield(self) -> None:
        if self.player.shield_rounds > 0:
            self.player.shield_rounds -= 1
            if self.player.shield_rounds == 0:
                print(c(C.SPELL, " Your shield fades."))

    def _player_death(self) -> None:
        print(f"\n{c(C.COMBAT_DIE, '══ YOU HAVE DIED ══')}")
        print(c(C.ROOM_DESC, "Your adventure ends here."))
        self.exit_code = 2
        self.running   = False

    # ── Parser ────────────────────────────────────────────────────────────────

    def parse(self, raw: str) -> tuple[str, list[str]]:
        tokens = raw.strip().lower().split()
        if not tokens:
            return ("", [])
        if len(tokens) >= 2 and tokens[0] == "talk" and tokens[1] == "to":
            return "talk", tokens[2:]
        if len(tokens) >= 2 and tokens[0] == "pick" and tokens[1] == "up":
            return "get", tokens[2:]
        if len(tokens) >= 2 and tokens[0] == "get" and tokens[1] == "all":
            return "getall", tokens[2:]
        verb = DIR_ABBREV.get(tokens[0], tokens[0])
        return verb, tokens[1:]

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def handle(self, raw: str) -> None:
        verb, args = self.parse(raw)
        if not verb:
            return
        noun = " ".join(args)
        dispatch = {
            **{d: lambda d=d: self.cmd_go(d) for d in DIRECTIONS},
            "go":        lambda: self.cmd_go(DIR_ABBREV.get(args[0], args[0])) if args else print(c(C.ERROR, "Go where?")),
            "look":      lambda: self.describe_room(),
            "l":         lambda: self.describe_room(),
            "inventory": lambda: self.cmd_inventory(),
            "inv":       lambda: self.cmd_inventory(),
            "i":         lambda: self.cmd_inventory(),
            "get":       lambda: self.cmd_get(noun),
            "take":      lambda: self.cmd_get(noun),
            "getall":    lambda: self.cmd_get_all(noun),
            "drop":      lambda: self.cmd_drop(noun),
            "examine":   lambda: self.cmd_examine(noun),
            "exam":      lambda: self.cmd_examine(noun),
            "x":         lambda: self.cmd_examine(noun),
            "read":      lambda: self.cmd_read(noun),
            "open":      lambda: self.cmd_open(noun),
            "close":     lambda: self.cmd_close(noun),
            "unlock":    lambda: self.cmd_unlock(noun),
            "equip":     lambda: self.cmd_equip(noun),
            "wear":      lambda: self.cmd_equip(noun),
            "wield":     lambda: self.cmd_equip(noun),
            "unequip":   lambda: self.cmd_unequip(noun),
            "remove":    lambda: self.cmd_unequip(noun),
            "equipment": lambda: self.cmd_equipment(),
            "eq":        lambda: self.cmd_equipment(),
            "attack":    lambda: self.cmd_attack(noun),
            "kill":      lambda: self.cmd_attack(noun),
            "fight":     lambda: self.cmd_attack(noun),
            "hit":       lambda: self.cmd_attack(noun),
            "stab":      lambda: self.cmd_attack(noun),
            "health":    lambda: self.cmd_health(),
            "hp":        lambda: self.cmd_health(),
            "status":    lambda: self.cmd_health(),
            "flee":      lambda: self.cmd_flee(),
            "run":       lambda: self.cmd_flee(),
            "rest":      lambda: self.cmd_rest(),
            "eat":       lambda: self.cmd_eat(noun),
            "consume":   lambda: self.cmd_eat(noun),
            "drink":     lambda: self.cmd_drink(noun),
            "quaff":     lambda: self.cmd_drink(noun),
            "talk":      lambda: self.cmd_talk(noun),
            "cast":      lambda: self.cmd_cast(noun),
            "spell":     lambda: self.cmd_cast(noun),
            "spells":    lambda: self.cmd_spellbook(),
            "save":      lambda: self.cmd_save(noun),
            "load":      lambda: self.cmd_load(noun),
            "help":      lambda: self.cmd_help(),
            "?":         lambda: self.cmd_help(),
            "h":         lambda: self.cmd_help(),
            "quit":      lambda: self.cmd_quit(),
            "q":         lambda: self.cmd_quit(),
            "exit":      lambda: self.cmd_quit(),
            "bye":       lambda: self.cmd_quit(),
        }
        action = dispatch.get(verb)
        if action:
            action()
        else:
            print(c(C.ERROR, f"I don't know how to \"{verb}\"."))

    # ── Movement ──────────────────────────────────────────────────────────────

    def cmd_go(self, direction: str) -> None:
        if [m for m in self.world.monsters_in_room(self.player.room_id) if m.aggro]:
            print(c(C.ERROR, "You can't leave while in combat! (Try FLEE)"))
            return
        room    = self.world.get_room(self.player.room_id)
        dest_id = room.exits.get(direction)
        if dest_id is None:
            print(c(C.ERROR, "You can't go that way."))
            return
        lock_id = room.locked_exits.get(direction)
        if lock_id:
            key = next((a for a in self.world.artifacts_carried() if a.id == lock_id), None)
            if key is None:
                print(c(C.ERROR, f"The way {direction} is locked.") +
                      c(C.EXITS,  f" (requires: {self._key_name(lock_id)})"))
                return
            del room.locked_exits[direction]
            print(c(C.SYS, f"You use the {key.name} to unlock the door."))
            self._award_xp(10)
        dest = self.world.get_room(dest_id)
        if dest is None:
            print(c(C.ERROR, "That passage leads nowhere."))
            return
        self._tick_shield()
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
                equipped_tag = ""
                if self.player.is_equipped(a.id):
                    slot = next(s for s, aid in self.player.equipped.items() if aid == a.id)
                    equipped_tag = c(C.EQUIPPED, f" [equipped: {slot}]")
                print(c(C.ITEM, f"  {a.name}") + equipped_tag)
                if a.is_container and a.is_open:
                    for cid in a.contents:
                        if cid in self.world.artifacts:
                            print(c(C.ITEM_LABEL, "   ") +
                                  c(C.ITEM, self.world.artifacts[cid].name))
        weight = self.player.carried_weight(self.world)
        print(c(C.EXITS, f"\nCarrying: {weight}/{self.player.max_carry_weight} gronds"))
        print(c(C.SYS, f"\n{self.player.health_bar()}"))
        if self.player.char_class == "Sorcerer":
            print(c(C.MANA_COLOR, f"{self.player.mana_bar()}"))

    # ── Get ───────────────────────────────────────────────────────────────────

    def _room_pickup_pool(self):
        room = self.world.get_room(self.player.room_id)
        pool = list(self.world.artifacts_in_room(room.id))
        for a in pool[:]:
            if a.is_container and a.is_open:
                pool += [self.world.artifacts[cid] for cid in a.contents
                         if cid in self.world.artifacts]
        return pool

    def _do_pickup(self, target) -> None:
        room           = self.world.get_room(self.player.room_id)
        room_artifacts = self.world.artifacts_in_room(room.id)
        for a in room_artifacts:
            if a.is_container and target.id in a.contents:
                a.contents.remove(target.id)
        target.room_id = None

    def cmd_get(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Get what?"))
            return
        pool   = self._room_pickup_pool()
        target = self.world.find_artifact_by_name(noun, pool)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        if not self.player.can_carry(target, self.world):
            print(c(C.ERROR, f"The {target.name} is too heavy."))
            return
        if target.artifact_type == "potion" and potion_count(self.world) >= MAX_POTIONS:
            print(c(C.ERROR, f"You can only carry {MAX_POTIONS} potions at a time."))
            return
        self._do_pickup(target)
        print(c(C.SYS, f"You pick up the {target.name}."))
        self._tick_shield()
        self.monster_round()

    def cmd_get_all(self, noun: str) -> None:
        pool = self._room_pickup_pool()
        if not pool:
            print(c(C.SYS, "There is nothing here to pick up."))
            return
        if noun:
            type_map = {
                "weapon": "weapon", "weapons": "weapon", "sword": "weapon",
                "armor":  "armor",  "armour":  "armor",
                "potion": "potion", "potions": "potion",
                "food":   "food",   "key":     "key",
                "keys":   "key",    "shield":  "shield",
                "ring":   "ring",   "rings":   "ring",
                "cloak":  "cloak",
            }
            atype = type_map.get(noun.lower())
            if atype:
                pool = [a for a in pool if a.artifact_type == atype]
            else:
                pool = [a for a in pool if noun.lower() in a.name.lower()]
        if not pool:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        picked, skipped = [], []
        for a in pool:
            if not self.player.can_carry(a, self.world):
                skipped.append(a.name)
            elif a.artifact_type == "potion" and potion_count(self.world) >= MAX_POTIONS:
                skipped.append(f"{a.name} (potion limit reached)")
            else:
                self._do_pickup(a)
                picked.append(a.name)
        if picked:
            print(c(C.SYS, f"You pick up: {', '.join(picked)}."))
        if skipped:
            print(c(C.ERROR, f"Too heavy to carry: {', '.join(skipped)}."))
        if picked:
            self._tick_shield()
            self.monster_round()

    # ── Drop ──────────────────────────────────────────────────────────────────

    def cmd_drop(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Drop what?"))
            return
        target = self.world.find_artifact_by_name(noun, self.world.artifacts_carried())
        if target is None:
            print(c(C.ERROR, f"You aren't carrying any {noun}."))
            return
        if self.player.is_equipped(target.id):
            print(c(C.WARN, f"Unequip the {target.name} before dropping it."))
            return
        target.room_id = self.player.room_id
        print(c(C.SYS, f"You drop the {target.name}."))

    # ── Equip / Unequip ───────────────────────────────────────────────────────

    def cmd_equip(self, noun: str) -> None:
        if not noun:
            self.cmd_equipment()
            return
        target = self.world.find_artifact_by_name(noun, self.world.artifacts_carried())
        if target is None:
            print(c(C.ERROR, f"You aren't carrying any {noun}."))
            return
        success, msg = self.player.equip(target, self.world)
        print(c(C.EQUIPPED if success else C.ERROR, f" {msg}"))

    def cmd_unequip(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Unequip what?"))
            return
        if noun in EQUIP_SLOTS:
            success, msg = self.player.unequip_slot(noun, self.world)
        else:
            target = self.world.find_artifact_by_name(noun, self.world.artifacts_carried())
            if target is None:
                print(c(C.ERROR, f"You aren't carrying any {noun}."))
                return
            success, msg = self.player.unequip_artifact(target, self.world)
        print(c(C.SYS if success else C.ERROR, f" {msg}"))

    def cmd_equipment(self) -> None:
        print(c(C.ITEM_LABEL, "\n Equipment:"))
        for slot in EQUIP_SLOTS:
            aid = self.player.equipped.get(slot)
            if aid is not None:
                a     = self.world.artifacts.get(aid)
                name  = a.name if a else f"unknown #{aid}"
                stats = ""
                if a:
                    if a.artifact_type == "weapon":
                        bonus = max(0, self.player.agility_bonus) + self.player.strength_bonus
                        stats = c(C.EXITS, f" ({a.damage_dice}d{a.damage_sides}+{bonus})")
                    elif a.artifact_type in ("armor", "shield"):
                        stats = c(C.EXITS, f" (AC +{a.armor_class})")
                print(c(C.EQUIPPED, f"  {slot:<8}") + c(C.ITEM, f": {name}") + stats)
            else:
                print(c(C.EXITS, f"  {slot:<8}: —"))
        if self.player.shield_rounds > 0:
            print(c(C.SPELL, f"  shield spell: {self.player.shield_rounds} rounds remaining"))

    # ── Examine / Read ────────────────────────────────────────────────────────

    def cmd_examine(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Examine what?"))
            return
        room = self.world.get_room(self.player.room_id)
        pool = self.world.artifacts_in_room(room.id) + self.world.artifacts_carried()
        for a in pool[:]:
            if a.is_container and a.is_open:
                pool += [self.world.artifacts[cid] for cid in a.contents
                         if cid in self.world.artifacts]
        monster = self.world.find_monster_by_name(noun, self.world.monsters_in_room(room.id))
        if monster:
            print(f"\n{c(C.WARN, monster.name.upper())}")
            print(c(C.ROOM_DESC, wrap(monster.description)))
            if monster.is_alive:
                print(c(C.WARN, f"{monster.name} {monster.health_desc()}."))
            return
        target = self.world.find_artifact_by_name(noun, pool)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        print(f"\n{c(C.ROOM_NAME, target.name.upper())}")
        print(c(C.ROOM_DESC, wrap(target.description)))
        if target.artifact_type in (ArtifactType.FOOD, ArtifactType.POTION):
            print(c(C.HEAL_COLOR, f"  Restores {target.heal_amount} HP when consumed."))
        if target.artifact_type == "weapon":
            bonus = max(0, self.player.agility_bonus) + self.player.strength_bonus
            print(c(C.EXITS, f"  Damage: {target.damage_dice}d{target.damage_sides}+{bonus}"))
        if target.artifact_type in ("armor", "shield"):
            print(c(C.EXITS, f"  Armor class: +{target.armor_class}"))
        equip_slot = slot_for_type(target.artifact_type)
        if equip_slot:
            equipped_here = self.player.equipped.get(equip_slot) == target.id
            status = (c(C.EQUIPPED, "[equipped]") if equipped_here
                      else c(C.EXITS, f"[equippable: {equip_slot}]"))
            print(f"  {status}")
        if target.is_container:
            state = "open" if target.is_open else "closed"
            print(c(C.SYS, f"It is {state}."))
            if target.is_open:
                contents = [self.world.artifacts[cid] for cid in target.contents
                            if cid in self.world.artifacts]
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

    # ── Open / Close / Unlock ─────────────────────────────────────────────────

    def cmd_open(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Open what?"))
            return
        room   = self.world.get_room(self.player.room_id)
        pool   = self.world.artifacts_in_room(room.id) + self.world.artifacts_carried()
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
        contents = [self.world.artifacts[cid] for cid in target.contents
                    if cid in self.world.artifacts]
        if contents:
            print(c(C.ITEM_LABEL, "Inside you see:"))
            for cont in contents:
                print(c(C.ITEM, f"  {cont.name}"))
            self._award_xp(10)
        else:
            print(c(C.ITEM_LABEL, "It is empty."))
        self._tick_shield()
        self.monster_round()

    def cmd_close(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Close what?"))
            return
        room   = self.world.get_room(self.player.room_id)
        pool   = self.world.artifacts_in_room(room.id) + self.world.artifacts_carried()
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

    def cmd_unlock(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Unlock which direction?"))
            return
        direction = DIR_ABBREV.get(noun, noun)
        room      = self.world.get_room(self.player.room_id)
        if direction not in room.exits:
            print(c(C.ERROR, f"There's no exit to the {direction}."))
            return
        lock_id = room.locked_exits.get(direction)
        if not lock_id:
            print(c(C.SYS, f"The way {direction} is already unlocked."))
            return
        key = next((a for a in self.world.artifacts_carried() if a.id == lock_id), None)
        if key is None:
            print(c(C.ERROR, f"You need the {self._key_name(lock_id)} to unlock that."))
            return
        del room.locked_exits[direction]
        print(c(C.SYS, f"You use the {key.name} to unlock the {direction} exit."))

    # ── REST ──────────────────────────────────────────────────────────────────

    def cmd_rest(self) -> None:
        if [m for m in self.world.monsters_in_room(self.player.room_id) if m.aggro]:
            print(c(C.ERROR, "You can't rest while monsters are nearby!"))
            return
        if self.player.hp >= self.player.hp_max:
            print(c(C.HEAL_COLOR, "You are already at full health."))
        else:
            heal = max(1, self.player.hp_max // 4)
            self.player.hp = min(self.player.hp_max, self.player.hp + heal)
            print(c(C.HEAL_COLOR, f"You rest and recover {heal} HP."))
            print(c(C.SYS, f"  {self.player.health_bar()}"))
        if self.player.char_class == "Sorcerer" and self.player.mana < self.player.mana_max:
            gain = max(1, self.player.mana_max // 4)
            self.player.mana = min(self.player.mana_max, self.player.mana + gain)
            print(c(C.MANA_COLOR, f"  Recovered {gain} mana. ({self.player.mana}/{self.player.mana_max})"))

    # ── EAT / DRINK ───────────────────────────────────────────────────────────

    def _consume(self, noun: str, atype: str, verb: str) -> None:
        if not noun:
            print(c(C.ERROR, f"{verb.capitalize()} what?"))
            return
        room   = self.world.get_room(self.player.room_id)
        pool   = self.world.artifacts_carried() + self.world.artifacts_in_room(room.id)
        target = self.world.find_artifact_by_name(noun, pool)
        if target is None:
            print(c(C.ERROR, f"You don't see any {noun} here."))
            return
        if target.artifact_type != atype:
            print(c(C.ERROR, f"You can't {verb} the {target.name}."))
            return
        healed = min(target.heal_amount, self.player.hp_max - self.player.hp)
        self.player.hp += healed
        target.room_id  = -999
        if healed > 0:
            print(c(C.HEAL_COLOR, f"You {verb} the {target.name} and recover {healed} HP."))
            print(c(C.SYS, f"  {self.player.health_bar()}"))
        else:
            print(c(C.SYS, f"You {verb} the {target.name}. (Already at full health)"))
        self._tick_shield()
        self.monster_round()

    def cmd_eat(self, noun: str)   -> None: self._consume(noun, ArtifactType.FOOD,   "eat")
    def cmd_drink(self, noun: str) -> None: self._consume(noun, ArtifactType.POTION, "drink")

    # ── TALK ──────────────────────────────────────────────────────────────────

    def cmd_talk(self, noun: str) -> None:
        if not noun:
            print(c(C.ERROR, "Talk to whom?"))
            return
        room = self.world.get_room(self.player.room_id)
        npc  = self.world.find_monster_by_name(noun, self.world.monsters_in_room(room.id))
        if npc is None:
            print(c(C.ERROR, f"There is no {noun} here to talk to."))
            return
        if npc.attitude == Attitude.HOSTILE:
            print(c(C.WARN, f"The {npc.name} doesn't seem interested in conversation."))
            return
        if npc.dialogue:
            print(c(C.WARN, f'\n  {npc.name} says: "{npc.dialogue}"'))
        else:
            print(c(C.WARN, f"  The {npc.name} regards you silently."))
        if npc.heal_amount > 0 and npc.heal_cost > 0:
            missing = self.player.hp_max - self.player.hp
            if missing <= 0:
                print(c(C.SYS, f'\n  {npc.name} says: "You look healthy enough."'))
                return
            cost = missing * npc.heal_cost
            print(c(C.SYS,
                    f'\n  {npc.name} offers to heal {missing} HP '
                    f'for {npc.heal_cost} gold/HP ({cost} gold total).'))
            print(c(C.EXITS, f"  You have {self.player.gold} gold."))
            answer = input(c(C.EXITS, "  Accept? (y/n): ")).strip().lower()
            if answer == "y":
                if self.player.gold >= cost:
                    self.player.gold -= cost
                    self.player.hp    = self.player.hp_max
                    print(c(C.HEAL_COLOR, f"  {npc.name} tends your wounds."))
                    print(c(C.SYS,        f"  {self.player.health_bar()}"))
                    print(c(C.EXITS,      f"  Gold remaining: {self.player.gold}"))
                else:
                    print(c(C.ERROR,
                            f"  Not enough gold. (Need {cost}, have {self.player.gold})"))
            else:
                print(c(C.SYS, "  You decline."))

    # ── CAST ──────────────────────────────────────────────────────────────────

    def cmd_cast(self, noun: str) -> None:
        if self.player.char_class != "Sorcerer":
            print(c(C.ERROR, "Only Sorcerers can cast spells."))
            return
        if not self.player.spells:
            print(c(C.ERROR, "You don't know any spells."))
            return
        if not noun:
            self.cmd_spellbook()
            return
        spell_key = next((k for k in self.player.spells
                          if noun.startswith(k) or k in noun), None)
        if spell_key is None:
            print(c(C.ERROR, f"You don't know a spell called '{noun}'."))
            return
        spell = SPELL_DEFS.get(spell_key)
        cost  = spell["cost"]
        if self.player.mana < cost:
            print(c(C.ERROR, f"Not enough mana. ({spell['name']} costs {cost}, you have {self.player.mana})"))
            return
        self.player.mana -= cost
        if   spell_key == "heal":     self._cast_heal()
        elif spell_key == "fireball": self._cast_fireball(noun.replace("fireball", "").strip())
        elif spell_key == "shield":   self._cast_shield()
        elif spell_key == "light":    self._cast_light()
        print(c(C.MANA_COLOR, f"  Mana: {self.player.mana}/{self.player.mana_max}"))
        self._tick_shield()
        self.monster_round()

    def _cast_heal(self) -> None:
        heal = min(roll(1, 6) + self.player.spell_bonus,
                   self.player.hp_max - self.player.hp)
        self.player.hp += heal
        print(c(C.SPELL,      "  ✦ Healing light surrounds you."))
        print(c(C.HEAL_COLOR, f"  You recover {heal} HP."))
        print(c(C.SYS,        f"  {self.player.health_bar()}"))

    def _cast_fireball(self, noun: str) -> None:
        room     = self.world.get_room(self.player.room_id)
        monsters = self.world.monsters_in_room(room.id)
        target   = None
        if noun:
            for m in monsters:
                if m.matches(noun):
                    target = m
                    break
        if target is None and len(monsters) == 1:
            target = monsters[0]
        if target is None:
            print(c(C.SPELL, "  ✦ Fireball! At whom? (CAST FIREBALL <monster>)"))
            self.player.mana += SPELL_DEFS["fireball"]["cost"]
            return
        dmg = max(0, roll(2, 6) + self.player.spell_bonus - target.armor_class)
        target.hp   -= dmg
        target.aggro = True
        print(c(C.SPELL,      f"  ✦ A ball of fire engulfs {c(C.WARN, target.name)}!"))
        print(c(C.COMBAT_HIT, f"  {target.name} takes {c(C.COMBAT_DMG, str(dmg))} fire damage!"))
        if target.hp <= 0:
            target.is_alive = False
            print(f"\n{c(C.COMBAT_WIN, target.death_message or f'The {target.name} collapses, scorched.')}")
            if target.loot_id and target.loot_id in self.world.artifacts:
                loot         = self.world.artifacts[target.loot_id]
                loot.room_id = self.player.room_id
                print(c(C.ITEM, f"  {loot.name} falls to the ground."))
            self._award_xp(monster_xp(target))
            self._check_stat_advance(took_damage=False)
            self._check_win()
        else:
            print(c(C.WARN, f"  {target.name} {target.health_desc()}."))

    def _cast_shield(self) -> None:
        self.player.shield_rounds = 3
        print(c(C.SPELL, "  ✦ A shimmering barrier forms around you. (+3 armor, 3 rounds)"))

    def _cast_light(self) -> None:
        self.light_active = True
        print(c(C.SPELL, "  ✦ Soft light emanates from your hands."))

    def cmd_spellbook(self) -> None:
        if self.player.char_class != "Sorcerer":
            print(c(C.ERROR, "You are not a Sorcerer."))
            return
        print(c(C.SPELL, "\n  Known spells:"))
        for key in self.player.spells:
            s    = SPELL_DEFS.get(key, {})
            mark = "✦" if self.player.mana >= s.get("cost", 99) else "✗"
            print(c(C.SPELL,      f"  {mark} {s.get('name', key):<12}") +
                  c(C.MANA_COLOR, f"  {s.get('cost', '?')} mana"))
        print(c(C.MANA_COLOR, f"\n  {self.player.mana_bar()}"))

    # ── Combat ────────────────────────────────────────────────────────────────

    def cmd_attack(self, noun: str) -> None:
        monsters = self.world.monsters_in_room(self.player.room_id)
        if not noun:
            if len(monsters) == 1:
                target = monsters[0]
            else:
                print(c(C.ERROR, "Attack what?"))
                return
        else:
            target = self.world.find_monster_by_name(noun, monsters)
            if target is None:
                print(c(C.ERROR, f"You don't see any {noun} here."))
                return
        if not target.is_alive:
            print(c(C.ERROR, f"The {target.name} is already dead."))
            return
        if target.attitude == Attitude.FRIENDLY:
            print(c(C.WARN, f"You can't bring yourself to strike {target.name}."))
            return
        target.aggro = True
        weapon = self.player.equipped_weapon(self.world)
        if weapon:
            p_dice, p_sides = weapon.damage_dice, weapon.damage_sides
            weapon_name     = weapon.name
        else:
            p_dice, p_sides = self.player.damage_dice, self.player.damage_sides
            weapon_name     = "your fists"
        bonus = max(0, self.player.agility_bonus) + self.player.strength_bonus
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
            print(f"\n{c(C.COMBAT_WIN, target.death_message or f'The {target.name} collapses, dead.')}")
            if target.loot_id and target.loot_id in self.world.artifacts:
                loot         = self.world.artifacts[target.loot_id]
                loot.room_id = self.player.room_id
                print(c(C.ITEM, f"  {loot.name} falls to the ground."))
            self._award_xp(monster_xp(target))
            self._check_stat_advance(took_damage=self.player.took_damage_this_fight)
            self.player.took_damage_this_fight = False
            self._check_win()
            return
        self.player.took_damage_this_fight = True
        print(c(C.WARN, f"  {target.name} {target.health_desc()}."))
        self._monster_attack(target)
        self._tick_shield()

    def _monster_attack(self, monster) -> None:
        dodge = max(0, self.player.agility_bonus * 5)
        if dodge > 0 and random.randint(1, 100) <= dodge:
            print(c(C.SYS, f"  {monster.name} swings — you dodge!"))
            print(c(C.SYS, f"  {self.player.health_bar()}"))
            return
        dmg = max(0, roll(monster.damage_dice, monster.damage_sides)
                  - self.player.armor_class(self.world))
        if dmg > 0:
            self.player.hp -= dmg
            self.player.took_damage_this_fight = True
            print(c(C.COMBAT_HIT,
                    f"  {c(C.WARN, monster.name)} hits you for "
                    f"{c(C.COMBAT_DMG, str(dmg))} damage!"))
        else:
            print(c(C.EXITS, f"  {c(C.WARN, monster.name)} attacks — armor absorbs it!"))
        print(c(C.SYS, f"  {self.player.health_bar()}"))
        if not self.player.is_alive:
            self._player_death()

    def cmd_flee(self) -> None:
        room = self.world.get_room(self.player.room_id)
        if not room.exits:
            print(c(C.ERROR, "There's nowhere to run!"))
            return
        hostiles = [m for m in self.world.monsters_in_room(self.player.room_id) if m.aggro]
        if hostiles:
            print(c(C.WARN, "You turn to run..."))
            for m in hostiles:
                self._monster_attack(m)
            if not self.player.is_alive:
                return
        direction           = random.choice(list(room.exits.keys()))
        self.player.room_id = room.exits[direction]
        print(c(C.SYS, f"  You flee {direction}!"))
        self.describe_room()
        self.monster_round()

    def cmd_health(self) -> None:
        print(c(C.SYS, f"\n{self.player.health_bar()}"))
        if self.player.char_class == "Sorcerer":
            print(c(C.MANA_COLOR, f"  {self.player.mana_bar()}"))
        weapon = self.player.equipped_weapon(self.world)
        bonus  = max(0, self.player.agility_bonus) + self.player.strength_bonus
        if weapon:
            print(c(C.ITEM,  f"  Weapon : {weapon.name} ({weapon.damage_dice}d{weapon.damage_sides}+{bonus})"))
        else:
            print(c(C.EXITS, f"  Weapon : unarmed ({self.player.damage_dice}d{self.player.damage_sides}+{bonus}) — EQUIP a weapon!"))
        print(c(C.EXITS, f"  Armor  : {self.player.armor_class(self.world)}"
              + (f" (+3 shield spell, {self.player.shield_rounds} rounds)" if self.player.shield_rounds > 0 else "")))
        print(c(C.EXITS, f"  Dodge  : {max(0, self.player.agility_bonus) * 5}%"))
        print(c(C.EXITS, f"  Gold   : {self.player.gold}"))

    # ── XP and leveling ───────────────────────────────────────────────────────

    def _award_xp(self, amount: int) -> None:
        if amount <= 0:
            return
        self.player.xp        += amount
        self.player.xp_gained += amount
        print(c(C.MANA_COLOR, f"  +{amount} XP (total: {self.player.xp})"))
        new_level = level_for_xp(self.player.xp)
        if new_level > self.player.level:
            self.player.level = new_level
            self._level_up(new_level)

    def _level_up(self, new_level: int) -> None:
        print("\n" + c(C.COMBAT_WIN, chr(9733) * 50))
        print(c(C.COMBAT_WIN, f"  LEVEL UP! You are now level {new_level}!"))
        if new_level < MAX_LEVEL:
            print(c(C.EXITS, f"  Next level at {xp_for_next_level(new_level)} XP"))
        print(c(C.COMBAT_WIN, chr(9733) * 50))
        self._choose_stat_boost()

    def _choose_stat_boost(self) -> None:
        stats = ["hardiness", "agility", "strength", "intelligence", "charisma"]
        if self.player.char_class == "Fighter":
            pool = ["strength", "strength", "agility", "agility",
                    "hardiness", "hardiness", "charisma", "intelligence"]
        else:
            pool = ["intelligence", "intelligence", "agility", "agility",
                    "hardiness", "hardiness", "charisma", "strength"]
        choices = random.sample(pool, 2)
        if choices[0] == choices[1]:
            others     = [s for s in stats if s != choices[0]]
            choices[1] = random.choice(others)
        print(c(C.ROOM_NAME, "\n  Choose a stat to increase by 1:"))
        for i, stat in enumerate(choices, 1):
            current = getattr(self.player, stat)
            print(c(C.ITEM, f"  {i}. {stat.capitalize():<15} (currently {current})"))
        while True:
            raw = input(c(C.EXITS, "  > ")).strip()
            if raw in ("1", "2"):
                chosen  = choices[int(raw) - 1]
                old_val = getattr(self.player, chosen)
                setattr(self.player, chosen, old_val + 1)
                print(c(C.COMBAT_WIN, f"  {chosen.capitalize()} increased to {old_val + 1}!"))
                if chosen == "hardiness":
                    self.player.hp = min(self.player.hp + 2, self.player.hp_max)
                    print(c(C.HEAL_COLOR, f"  Max HP is now {self.player.hp_max}."))
                break

    def _check_stat_advance(self, took_damage: bool = False) -> None:
        if random.randint(1, 10) != 1:
            return
        if self.player.char_class == "Fighter":
            candidates = ["strength", "agility"] + (["hardiness"] if took_damage else [])
        else:
            candidates = ["intelligence", "agility"] + (["hardiness"] if took_damage else [])
        stat    = random.choice(candidates)
        old_val = getattr(self.player, stat)
        setattr(self.player, stat, old_val + 1)
        print(c(C.COMBAT_WIN, f"\n  Your {stat.capitalize()} improves! ({old_val} → {old_val + 1})"))
        if stat == "hardiness":
            self.player.hp = min(self.player.hp + 2, self.player.hp_max)
            print(c(C.HEAL_COLOR, f"  Max HP is now {self.player.hp_max}."))

    # ── Win condition ─────────────────────────────────────────────────────────

    def _check_win(self) -> None:
        wc = getattr(self.world, "win_condition", None)
        if not wc:
            return
        wc_type = wc.get("type")
        won     = False
        if wc_type == "kill_monster":
            mid = wc.get("monster_id")
            m   = self.world.monsters.get(mid)
            won = m is not None and not m.is_alive
        elif wc_type == "kill_all":
            won = all(not m.is_alive for m in self.world.monsters.values())
        elif wc_type == "reach_room":
            won = self.player.room_id == wc.get("room_id")
        elif wc_type == "carry_artifact":
            aid = wc.get("artifact_id")
            a   = self.world.artifacts.get(aid)
            won = a is not None and a.room_id is None
        if won:
            self._win(wc.get("message", "You have won!"))

    def _win(self, message: str) -> None:
        print(f"\n{c(C.COMBAT_WIN, '═' * 60)}")
        print(c(C.COMBAT_WIN, f"  {message}"))
        print(c(C.COMBAT_WIN, '═' * 60))
        self.exit_code = 1
        self.running   = False

    # ── Save command ──────────────────────────────────────────────────────────

    def cmd_save(self, noun: str) -> None:
        """Save game with 3-slot system and combat check."""
        # Check for combat: look for alive monsters in current room
        monsters_here = [m for m in self.world.monsters.values() 
                        if m.room_id == self.player.room_id and m.is_alive]
        if monsters_here:
            print(c(C.ERROR, "  ❌ Cannot save during combat!"))
            return
        
        # Get character name and adventure name for save slot management
        char_name = self.player.name
        # Extract adventure name from path (e.g., "adventures/sample" -> "sample")
        adv_name = os.path.basename(self._adv_path.rstrip("/"))
        
        # Show existing saves and prompt for slot
        existing = get_existing_saves(char_name, adv_name)
        print(c(C.SYS, f"\n  ═══ SAVE GAME ({len(existing)}/3 slots used) ═══"))
        
        for slot, filename, meta in existing:
            print(c(C.SYS, f"    Slot {slot}: {meta['room']} (HP: {meta['hp']}, {meta['timestamp']})"))
        
        for slot in range(1, 4):
            if not any(s[0] == slot for s in existing):
                print(c(C.SYS, f"    Slot {slot}: [EMPTY]"))
        
        print(c(C.SYS, "\n  Save to which slot? (1-3, or 'cancel'): "), end='')
        choice = input().strip()
        
        if choice.lower() == 'cancel':
            print(c(C.SYS, "  ⊘ Save cancelled."))
            return
        
        try:
            slot = int(choice)
            if not (1 <= slot <= 3):
                print(c(C.ERROR, "  ❌ Invalid slot."))
                return
        except ValueError:
            print(c(C.ERROR, "  ❌ Invalid input."))
            return
        
        # Build save data in format expected by apply_save_state
        player_state = {
            "name":          self.player.name,
            "char_class":    self.player.char_class,
            "room_id":       self.player.room_id,
            "hardiness":     self.player.hardiness,
            "agility":       self.player.agility,
            "charisma":      self.player.charisma,
            "intelligence":  self.player.intelligence,
            "strength":      self.player.strength,
            "hp":            self.player.hp,
            "mana":          self.player.mana,
            "gold":          self.player.gold,
            "spells":        self.player.spells,
            "equipped":      self.player.equipped,
            "xp":            self.player.xp,
            "level":         self.player.level,
            "xp_gained":     getattr(self.player, "xp_gained", 0),
            "shield_rounds": getattr(self.player, "shield_rounds", 0),
        }
        
        world_state = {
            'artifacts': {str(aid): a.room_id for aid, a in self.world.artifacts.items()},
            'monsters': {
                str(mid): {"hp": m.hp, "is_alive": m.is_alive, "aggro": m.aggro}
                for mid, m in self.world.monsters.items()
            },
            'rooms': {
                str(rid): {"first_visit": r.first_visit, "locked_exits": r.locked_exits}
                for rid, r in self.world.rooms.items()
            },
            'light_active': self.light_active,
        }
        
        if save_game_slotted(char_name, adv_name, player_state, world_state, slot, interactive=False):
            print(c(C.COMBAT_WIN, f"  ✅ Game saved to slot {slot}"))
        else:
            print(c(C.ERROR, "  ❌ Save failed."))

    def cmd_load(self, noun: str) -> None:
        """Load a previously saved game (mid-adventure)."""
        char_name = self.player.name
        adv_name = os.path.basename(self._adv_path.rstrip("/"))
        
        # Get list of saves
        existing = get_existing_saves(char_name, adv_name)
        if not existing:
            print(c(C.ERROR, "  ❌ No saves found for this adventure."))
            return
        
        # Show saves
        print(c(C.SYS, f"\n  ═══ LOAD GAME ({len(existing)} save(s)) ═══"))
        for slot, filename, meta in existing:
            print(c(C.SYS, f"    Slot {slot}: {meta['room']} (HP: {meta['hp']}, {meta['timestamp']})"))
        print(c(C.SYS, f"    {len(existing) + 1}. Cancel"))
        
        print(c(C.SYS, "\n  Load from which slot? (1-3, or 'cancel'): "), end='')
        choice = input().strip()
        
        if choice.lower() == 'cancel':
            print(c(C.SYS, "  ⊘ Load cancelled."))
            return
        
        try:
            slot = int(choice)
            if not any(s[0] == slot for s in existing):
                print(c(C.ERROR, "  ❌ Invalid slot."))
                return
        except ValueError:
            print(c(C.ERROR, "  ❌ Invalid input."))
            return
        
        # Load the save
        save_data = load_game_slotted(char_name, adv_name, slot, interactive=False)
        if not save_data:
            print(c(C.ERROR, "  ❌ Load failed."))
            return
        
        # Apply save state
        apply_save_state(self, save_data)
        print(c(C.COMBAT_WIN, f"  ✅ Loaded from slot {slot}\n"))
        
        # Show new room
        self.describe_room()


    # ── Help / Quit ───────────────────────────────────────────────────────────

    def cmd_help(self) -> None:
        print(c(C.HELP, "\n── Commands ──────────────────────────────────────────────────"))
        print(c(C.HELP, "  NORTH/SOUTH/EAST/WEST (N/S/E/W)  Move"))
        print(c(C.HELP, "  GO <direction>                   Move explicitly"))
        print(c(C.HELP, "  LOOK / L                         Describe current room"))
        print(c(C.HELP, "  INVENTORY / I                    List carried items"))
        print(c(C.HELP, "  GET <item>  /  GET ALL           Pick up item(s)"))
        print(c(C.HELP, "  DROP <item>                      Drop an item"))
        print(c(C.HELP, "  EXAMINE / X <thing>              Inspect item or monster"))
        print(c(C.HELP, "  READ <item>                      Read a readable item"))
        print(c(C.HELP, "  OPEN / CLOSE <item>              Open or close a container"))
        print(c(C.HELP, "  UNLOCK <direction>               Unlock a locked exit"))
        print(c(C.HELP, "  EQUIP / WEAR / WIELD <item>      Equip an item"))
        print(c(C.HELP, "  UNEQUIP / REMOVE <item>          Unequip an item"))
        print(c(C.HELP, "  EQUIPMENT / EQ                   Show equipped items"))
        print(c(C.HELP, "  ATTACK / KILL <monster>          Attack a monster"))
        print(c(C.HELP, "  FLEE                             Escape combat"))
        print(c(C.HELP, "  HEALTH / HP                      Show health and stats"))
        print(c(C.HELP, "  REST                             Recover HP and mana"))
        print(c(C.HELP, "  EAT <food>  /  DRINK <potion>    Consume an item"))
        print(c(C.HELP, "  TALK TO <npc>                    Speak with an NPC"))
        print(c(C.HELP, "  CAST <spell>  (Sorcerer only)    Cast a spell"))
        print(c(C.HELP, "  SPELLS                           List known spells"))
        print(c(C.HELP, "  SAVE                             Save game (up to 3 slots)"))
        print(c(C.HELP, "  LOAD                             Load a saved game"))
        print(c(C.HELP, "  QUIT / Q                         Quit to tavern"))
        print()

    def cmd_quit(self) -> None:
        answer = input(c(C.EXITS, "  Really quit? (y/n): ")).strip().lower()
        if answer == "y":
            self.exit_code = 0
            self.running   = False


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Eamon Redux engine")
    ap.add_argument("adv_path")
    ap.add_argument("--name",         default="Adventurer")
    ap.add_argument("--class",        dest="char_class", default="Fighter")
    ap.add_argument("--hardiness",    type=int, default=10)
    ap.add_argument("--agility",      type=int, default=10)
    ap.add_argument("--charisma",     type=int, default=10)
    ap.add_argument("--intelligence", type=int, default=10)
    ap.add_argument("--strength",     type=int, default=10)
    ap.add_argument("--hp",           type=int, default=0)
    ap.add_argument("--mana",         type=int, default=0)
    ap.add_argument("--gold",         type=int, default=100)
    ap.add_argument("--spells",       default="")
    ap.add_argument("--xp",           type=int, default=0)
    ap.add_argument("--level",        type=int, default=1)
    ap.add_argument("--savefile",     default="",
                    help="Resume from stored_games/<savefile>.json")
    ap.add_argument("--items-file",   default="",
                    help="Path to character items file (from tavern)")
    args = ap.parse_args()

    world = World.load(args.adv_path)
    if world is None:
        print(f"Could not load adventure at {args.adv_path}", file=sys.stderr)
        sys.exit(3)

    player = Player(
        name             = args.name,
        char_class       = args.char_class,
        room_id          = world.start_room,
        hardiness        = args.hardiness,
        agility          = args.agility,
        charisma         = args.charisma,
        intelligence     = args.intelligence,
        strength         = args.strength,
        hp               = args.hp,
        mana             = args.mana,
        gold             = args.gold,
        spells           = [s for s in args.spells.split(",") if s],
        xp               = args.xp,
        level            = args.level,
        max_carry_weight = args.hardiness * 10,
    )

    engine           = Engine(world, player)
    engine._adv_path = args.adv_path

    # ── Resume from save if requested ────────────────────────────
    if args.savefile:
        save_data = load_game(args.savefile)
        if save_data is None:
            print(c(C.ERROR, f"  Save file '{args.savefile}' not found."))
            sys.exit(3)
        apply_save_state(engine, save_data)
        print(c(C.SYS, f"\n  Resumed from save: {args.savefile}\n"))

    # ── Adventure intro (skip on resume) ─────────────────────────
    if not args.savefile:
        meta_path = os.path.join(args.adv_path, "adventure.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            title = meta.get("title", "Adventure")
            intro = meta.get("intro", "")
            print(f"\n{c(C.TITLE, title.upper())}")
            if intro:
                print(c(C.INTRO, wrap(intro)))
            print()

    engine.describe_room()

    # ── Main game loop ────────────────────────────────────────────
    while engine.running:
        try:
            raw = input(c(C.ROOM_NAME, "\n> ")).strip()
        except (EOFError, KeyboardInterrupt):
            engine.exit_code = 0
            break
        if raw:
            engine.handle(raw)

    # ── Write carried items back for tavern ───────────────────────
    carried    = world.artifacts_carried()
    items_file = os.path.join("characters",
                              f"{player.name.lower().replace(' ', '_')}_items.json")
    os.makedirs("characters", exist_ok=True)
    with open(items_file, "w") as f:
        json.dump([a.to_dict() for a in carried], f, indent=2)

    sys.exit(engine.exit_code)
