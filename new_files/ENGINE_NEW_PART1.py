"""
engine.py - Eamon Redux game engine (REWRITTEN for proficiency-based magic system).

Exit codes: 0=quit, 1=completed, 2=died
"""

from __future__ import annotations

import sys
import os
import json
import random
from character import SPELL_DEFS, WEAPON_TYPES
from world import WeaponType

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
    ensure_saves_dir,
    get_existing_saves,
    prompt_save_slot,
)
from command_parser import parse_command

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

# ── XP and leveling ───────────────────────────────────────────────────────────

XP_LEVELS = [0, 500, 695, 1000, 1500, 1900, 2500, 3800, 5000, 9000, 15000]
MAX_LEVEL = len(XP_LEVELS)

def xp_to_next_level(xp: int) -> int:
    for i, threshold in enumerate(XP_LEVELS):
        if xp < threshold:
            return threshold - xp
    return 0

# ── Game Engine ───────────────────────────────────────────────────────────────

class Engine:
    """Main game engine for Eamon Redux adventures."""

    def __init__(self, world: World, character):
        """Initialize engine with world and character data."""
        self.world = world
        self.character = character
        
        # Create player runtime state from character
        self.player = Player(
            name=character.name,
            room_id=world.start_room,
            hardiness=character.hardiness,
            agility=character.agility,
            charisma=character.charisma,
            intelligence=character.intelligence,
            strength=character.strength,
            hp=character.hp_max,
            gold=character.gold,
            spell_proficiencies=character.spell_proficiencies.copy(),
            weapon_proficiencies=character.weapon_proficiencies.copy(),
            xp=character.xp,
            level=character.level,
        )
        
        # Initialize spell fatigue multipliers to 1.0
        for spell_key in self.player.spell_proficiencies:
            if self.player.spell_proficiencies[spell_key] is not None:
                self.player.spell_fatigue_multiplier[spell_key] = 1.0
        
        self.turn = 0
        self.in_combat = False
        self.enemy = None

    def tc(self, text: str, style: str = "sys") -> str:
        """Text color helper."""
        colors = {
            "reset":   C.RESET,
            "hr":      C.HR,
            "room":    C.ROOM_NAME,
            "desc":    C.ROOM_DESC,
            "exits":   C.EXITS,
            "item":    C.ITEM,
            "equipped": C.EQUIPPED,
            "sys":     C.SYS,
            "error":   C.ERROR,
            "warn":    C.WARN,
            "hit":     C.COMBAT_HIT,
            "dmg":     C.COMBAT_DMG,
            "win":     C.COMBAT_WIN,
            "die":     C.COMBAT_DIE,
            "spell":   C.SPELL,
            "heal":    C.HEAL_COLOR,
            "title":   C.TITLE,
            "intro":   C.INTRO,
            "success": C.HEAL_COLOR,
        }
        color = colors.get(style, C.SYS)
        return c(color, text)

    # ── Room & World ──────────────────────────────────────────────────────────

    def look(self) -> None:
        """Display current room."""
        room = self.world.get_room(self.player.room_id)
        if not room:
            print(self.tc("(Room not found)", "error"))
            return
        
        print()
        print(self.tc(room.name, "room"))
        print(self.tc("─" * 72, "exits"))
        print(self.tc(wrap(room.description), "desc"))
        
        # Artifacts in room
        artifacts = self.world.artifacts_in_room(self.player.room_id)
        if artifacts:
            print()
            print(self.tc("You see:", "sys"))
            for a in artifacts:
                print(self.tc(f"  • {a.name}", "item"))
        
        # Monsters in room
        monsters = self.world.monsters_in_room(self.player.room_id)
        if monsters:
            print()
            print(self.tc("Creatures:", "warn"))
            for m in monsters:
                print(self.tc(f"  • {m.name} ({m.health_desc()})", "warn"))
        
        # Exits
        if room.exits:
            print()
            print(self.tc(f"Exits: {room.exit_list()}", "exits"))
        
        print()

    def handle(self, raw_input: str) -> int:
        """
        Handle a player command.
        Returns: 0=continue, 1=win, 2=die
        """
        self.turn += 1
        
        # Parse command
        cmd, status, suggestions = parse_command(raw_input, "engine")
        
        if status == "empty":
            return 0
        elif status == "not_found":
            print(self.tc("Unknown command. Type HELP for available commands.", "error"))
            return 0
        elif status == "ambiguous":
            print(self.tc(f"Ambiguous: {', '.join(suggestions)}. Be more specific.", "warn"))
            return 0
        
        # Handle partial/exact matches
        if status in ("partial", "exact"):
            if cmd in ["north", "south", "east", "west", "up", "down"]:
                self.cmd_go(cmd)
                # Fatigue recovery on movement
                recovery = random.randint(5, 10)
                self.player.recover_all_spell_fatigue(recovery)
            elif cmd == "go":
                parts = raw_input.split()
                if len(parts) > 1:
                    self.cmd_go(parts[1])
                    recovery = random.randint(5, 10)
                    self.player.recover_all_spell_fatigue(recovery)
            elif cmd == "look":
                self.look()
            elif cmd == "examine":
                noun = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_examine(noun)
            elif cmd == "read":
                noun = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_read(noun)
            elif cmd == "inventory":
                self.cmd_inventory()
            elif cmd == "get":
                parts = raw_input.split(maxsplit=1)
                if len(parts) > 1 and parts[1].lower() == "all":
                    self.cmd_get_all("")
                else:
                    noun = parts[1] if len(parts) > 1 else ""
                    self.cmd_get(noun)
            elif cmd == "drop":
                noun = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_drop(noun)
            elif cmd == "equip":
                noun = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_equip(noun)
            elif cmd == "unequip":
                noun = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_unequip(noun)
            elif cmd == "equipment":
                self.cmd_equipment()
            elif cmd == "health":
                self.cmd_health()
            elif cmd == "rest":
                self.cmd_rest()
            elif cmd == "cast":
                args = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_cast(args)
            elif cmd == "attack":
                noun = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_attack(noun)
            elif cmd == "flee":
                self.cmd_flee()
            elif cmd == "spells":
                self.cmd_spells()
            elif cmd == "help":
                self.cmd_help()
            elif cmd == "save":
                noun = raw_input.split(maxsplit=1)[1] if len(raw_input.split(maxsplit=1)) > 1 else ""
                self.cmd_save(noun)
            elif cmd == "load":
                self.cmd_load("")
            elif cmd == "quit":
                return self.cmd_quit_with_confirm()
        
        # Check win condition
        if self._check_win():
            return 1
        
        # Check death
        if not self.player.is_alive:
            return 2
        
        return 0

    def _check_win(self) -> bool:
        """Check if player has achieved win condition."""
        wc = self.world.win_condition
        if not wc:
            return False
        
        wc_type = wc.get("type")
        
        if wc_type == "reach_room":
            return self.player.room_id == wc.get("room_id")
        elif wc_type == "kill_monster":
            monster = self.world.monsters.get(wc.get("monster_id"))
            return monster and not monster.is_alive
        elif wc_type == "kill_all":
            return not any(m.is_alive for m in self.world.monsters.values())
        elif wc_type == "carry_artifact":
            artifact = self.world.artifacts.get(wc.get("artifact_id"))
            return artifact and artifact.room_id is None
        
        return False

    # ── Movement ───────────────────────────────────────────────────────────────

    def cmd_go(self, direction: str) -> None:
        """Move in a direction."""
        direction = direction.lower()
        if direction in DIR_ABBREV:
            direction = DIR_ABBREV[direction]
        
        if direction not in DIRECTIONS:
            print(self.tc(f"Invalid direction: {direction}", "error"))
            return
        
        room = self.world.get_room(self.player.room_id)
        if not room:
            print(self.tc("(No current room)", "error"))
            return
        
        # Check for exit
        if direction not in room.exits:
            print(self.tc("You can't go that way.", "error"))
            return
        
        # Check for locked exit
        if direction in room.locked_exits:
            key_id = room.locked_exits[direction]
            key = self.world.artifacts.get(key_id)
            if key and key.room_id is not None:
                print(self.tc(f"The {direction} exit is locked. (Need: {key.name})", "warn"))
                return
        
        # Move
        new_room_id = room.exits[direction]
        self.player.room_id = new_room_id
        
        new_room = self.world.get_room(new_room_id)
        if new_room and new_room.first_visit:
            new_room.first_visit = False
            self.look()
        else:
            print(self.tc(f"You go {direction}.", "sys"))
        
        # Check for hostile monsters
        monsters = self.world.monsters_in_room(new_room_id)
        for m in monsters:
            if m.attitude == Attitude.HOSTILE:
                print(self.tc(f"A {m.name} attacks you!", "warn"))
                self.cmd_attack(m.name)
                break

    # ── Inventory & Equipment ─────────────────────────────────────────────────

    def cmd_inventory(self) -> None:
        """Show carried items."""
        artifacts = self.world.artifacts_carried()
        if not artifacts:
            print(self.tc("You're carrying nothing.", "sys"))
            return
        
        print()
        print(self.tc("Inventory:", "sys"))
        total_weight = 0
        for a in artifacts:
            equipped_tag = ""
            if self.player.is_equipped(a.id):
                equipped_tag = self.tc(" [EQUIPPED]", "equipped")
            print(self.tc(f"  • {a.name}", "item") + equipped_tag)
            total_weight += a.weight
        
        print(self.tc(f"  Total weight: {total_weight}/{self.player.max_carry_weight} gronds", "sys"))
        print()

    def cmd_get(self, noun: str) -> None:
        """Pick up an item."""
        if not noun:
            print(self.tc("Get what?", "error"))
            return
        
        artifacts = self.world.artifacts_in_room(self.player.room_id)
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return
        
        if not self.player.can_carry(artifact, self.world):
            print(self.tc(f"The {artifact.name} is too heavy to carry.", "warn"))
            return
        
        artifact.room_id = None
        print(self.tc(f"You pick up the {artifact.name}.", "sys"))

    def cmd_get_all(self, noun: str) -> None:
        """Pick up all items (or all of a type)."""
        artifacts = self.world.artifacts_in_room(self.player.room_id)
        
        if noun:
            artifact_type = noun.lower()
            artifacts = [a for a in artifacts if artifact_type in a.artifact_type.lower()]
        
        if not artifacts:
            print(self.tc("Nothing to pick up.", "sys"))
            return
        
        picked_up = 0
        for a in artifacts:
            if self.player.can_carry(a, self.world):
                a.room_id = None
                picked_up += 1
        
        if picked_up > 0:
            print(self.tc(f"You pick up {picked_up} item(s).", "sys"))
        else:
            print(self.tc("Can't carry anything else.", "warn"))

    def cmd_drop(self, noun: str) -> None:
        """Drop an item."""
        if not noun:
            print(self.tc("Drop what?", "error"))
            return
        
        artifacts = self.world.artifacts_carried()
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You're not carrying a {noun}.", "error"))
            return
        
        # Unequip if equipped
        if self.player.is_equipped(artifact.id):
            self.player.unequip_artifact(artifact, self.world)
        
        artifact.room_id = self.player.room_id
        print(self.tc(f"You drop the {artifact.name}.", "sys"))

    def cmd_equip(self, noun: str) -> None:
        """Equip an item."""
        if not noun:
            print(self.tc("Equip what?", "error"))
            return
        
        artifacts = self.world.artifacts_carried()
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You're not carrying a {noun}.", "error"))
            return
        
        success, msg = self.player.equip(artifact, self.world)
        print(self.tc(msg, "sys" if success else "error"))

    def cmd_unequip(self, noun: str) -> None:
        """Unequip an item."""
        if not noun:
            print(self.tc("Unequip what?", "error"))
            return
        
        artifacts = self.world.artifacts_carried()
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You're not carrying a {noun}.", "error"))
            return
        
        success, msg = self.player.unequip_artifact(artifact, self.world)
        print(self.tc(msg, "sys" if success else "error"))

    def cmd_equipment(self) -> None:
        """Show equipped items."""
        print()
        print(self.tc("Equipment:", "sys"))
        for slot, aid in self.player.equipped.items():
            if aid is not None:
                a = self.world.artifacts.get(aid)
                name = a.name if a else f"item #{aid}"
                print(self.tc(f"  {slot:<8}: {name}", "item"))
            else:
                print(self.tc(f"  {slot:<8}: (empty)", "sys"))
        
        print()
        ac = self.player.armor_class(self.world)
        print(self.tc(f"Armor Class: {ac}", "sys"))
        print()

    # ── Examination & Interaction ──────────────────────────────────────────────

    def cmd_examine(self, noun: str) -> None:
        """Examine something in detail."""
        if not noun:
            print(self.tc("Examine what?", "error"))
            return
        
        # Check artifacts in room
        room_artifacts = self.world.artifacts_in_room(self.player.room_id)
        artifact = self.world.find_artifact_by_name(noun, room_artifacts)
        if artifact:
            print()
            print(self.tc(artifact.name, "item"))
            print(self.tc(artifact.description, "desc"))
            print()
            return
        
        # Check carried artifacts
        carried = self.world.artifacts_carried()
        artifact = self.world.find_artifact_by_name(noun, carried)
        if artifact:
            print()
            print(self.tc(artifact.name, "item"))
            print(self.tc(artifact.description, "desc"))
            print()
            return
        
        # Check monsters
        monsters = self.world.monsters_in_room(self.player.room_id)
        monster = self.world.find_monster_by_name(noun, monsters)
        if monster:
            print()
            print(self.tc(monster.name, "warn"))
            print(self.tc(monster.description, "desc"))
            print(self.tc(f"Status: {monster.health_desc()}", "sys"))
            print()
            return
        
        print(self.tc(f"You don't see a {noun} here.", "error"))

    def cmd_read(self, noun: str) -> None:
        """Read a readable item."""
        if not noun:
            print(self.tc("Read what?", "error"))
            return
        
        artifacts = self.world.artifacts_carried()
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You're not carrying a {noun}.", "error"))
            return
        
        if artifact.artifact_type != ArtifactType.READABLE:
            print(self.tc(f"You can't read the {artifact.name}.", "error"))
            return
        
        print()
        print(self.tc(artifact.read_text or "(blank page)", "desc"))
        print()

    # ── Consumption ───────────────────────────────────────────────────────────

    def _consume(self, noun: str, artifact_type: str, verb: str) -> None:
        """Generic consume (eat/drink) handler."""
        if not noun:
            print(self.tc(f"{verb.capitalize()} what?", "error"))
            return
        
        artifacts = self.world.artifacts_carried()
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You're not carrying a {noun}.", "error"))
            return
        
        if artifact.artifact_type != artifact_type:
            print(self.tc(f"You can't {verb} the {artifact.name}.", "error"))
            return
        
        # Consume
        healing = artifact.heal_amount
        self.player.hp = min(self.player.hp + healing, self.player.hp_max)
        print(self.tc(f"You {verb} the {artifact.name}. ({healing} HP restored)", "heal"))
        
        # Remove from inventory
        self.world.artifacts[artifact.id].room_id = self.player.room_id

    def cmd_eat(self, noun: str) -> None:
        self._consume(noun, ArtifactType.FOOD, "eat")

    def cmd_drink(self, noun: str) -> None:
        self._consume(noun, ArtifactType.POTION, "drink")

    # ── Doors & Locks ──────────────────────────────────────────────────────────

    def cmd_open(self, noun: str) -> None:
        """Open a container."""
        if not noun:
            print(self.tc("Open what?", "error"))
            return
        
        artifacts = self.world.artifacts_in_room(self.player.room_id)
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return
        
        if not artifact.is_container:
            print(self.tc(f"The {artifact.name} isn't a container.", "error"))
            return
        
        if artifact.is_open:
            print(self.tc(f"The {artifact.name} is already open.", "sys"))
            return
        
        artifact.is_open = True
        print(self.tc(f"You open the {artifact.name}.", "sys"))
        
        if artifact.contents:
            print(self.tc(f"Inside: {', '.join(self.world.artifacts.get(i).name for i in artifact.contents if self.world.artifacts.get(i))}", "item"))

    def cmd_close(self, noun: str) -> None:
        """Close a container."""
        if not noun:
            print(self.tc("Close what?", "error"))
            return
        
        artifacts = self.world.artifacts_in_room(self.player.room_id)
        artifact = self.world.find_artifact_by_name(noun, artifacts)
        
        if not artifact:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return
        
        if not artifact.is_container:
            print(self.tc(f"The {artifact.name} isn't a container.", "error"))
            return
        
        if not artifact.is_open:
            print(self.tc(f"The {artifact.name} is already closed.", "sys"))
            return
        
        artifact.is_open = False
        print(self.tc(f"You close the {artifact.name}.", "sys"))

    def cmd_unlock(self, direction: str) -> None:
        """Unlock a direction with a key."""
        if not direction:
            print(self.tc("Unlock which direction?", "error"))
            return
        
        direction = direction.lower()
        if direction in DIR_ABBREV:
            direction = DIR_ABBREV[direction]
        
        room = self.world.get_room(self.player.room_id)
        if not room or direction not in room.locked_exits:
            print(self.tc("That exit isn't locked.", "error"))
            return
        
        key_id = room.locked_exits[direction]
        key = self.world.artifacts.get(key_id)
        
        if not key:
            print(self.tc(f"(No key found for lock)", "error"))
            return
        
        # Check if player is carrying the key
        if key.room_id is not None:
            print(self.tc(f"You need the {key.name}.", "warn"))
            return
        
        # Unlock
        del room.locked_exits[direction]
        print(self.tc(f"You unlock the {direction} exit with the {key.name}.", "success"))

    # ── Status & Rest ──────────────────────────────────────────────────────────

    def cmd_rest(self) -> None:
        """Rest to recover HP and fatigue."""
        # Check for hostile monsters
        monsters = self.world.monsters_in_room(self.player.room_id)
        if any(m.attitude == Attitude.HOSTILE for m in monsters):
            print(self.tc("You can't rest with monsters around!", "warn"))
            return
        
        # Rest
        old_hp = self.player.hp
        self.player.hp = self.player.hp_max
        hp_restored = self.player.hp - old_hp
        
        print(self.tc(f"You rest. ({hp_restored} HP restored)", "heal"))
        
        # Fatigue recovery (larger than movement)
        recovery = random.randint(10, 20)
        self.player.recover_all_spell_fatigue(recovery)
        print(self.tc(f"Your mental fatigue eases. (recovery: {recovery}%)", "sys"))

    def cmd_health(self) -> None:
        """Show health status."""
        print()
        print(self.tc(self.player.health_bar(), "sys"))
        
        # Equipped items
        weapon = self.player.equipped_weapon(self.world)
        armor_id = self.player.equipped.get("armor")
        shield_id = self.player.equipped.get("shield")
        
        weapon_str = weapon.name if weapon else "(unarmed)"
        armor_str = self.world.artifacts.get(armor_id).name if armor_id else "(none)"
        shield_str = self.world.artifacts.get(shield_id).name if shield_id else "(none)"
        
        print(self.tc(f"Weapon: {weapon_str}", "item"))
        print(self.tc(f"Armor: {armor_str}", "item"))
        print(self.tc(f"Shield: {shield_str}", "item"))
        print(self.tc(f"AC: {self.player.armor_class(self.world)}", "sys"))
        print(self.tc(f"Gold: {self.player.gold}g", "sys"))
        
        # Speed spell status
        if self.player.speed_active:
            print(self.tc(f"Speed: ACTIVE ({self.player.speed_rounds_remaining} rounds remaining)", "spell"))
        
        print()

    # ── SPELL SYSTEM (NEW) ─────────────────────────────────────────────────────

    def _attempt_cast(self, spell_key: str, target_name: str = None) -> bool:
        """
        Core spell casting logic with proficiency checks, fatigue, and skill growth.
        Returns True if spell succeeded, False otherwise.
        """
        # Check if spell is learned
        if self.player.spell_proficiencies.get(spell_key) is None:
            print(self.tc(f"You don't know the {SPELL_DEFS[spell_key]['name']} spell.", "error"))
            return False
        
        # Check if spell is locked (1% critical failure)
        if self.player.is_spell_locked(spell_key):
            print(self.tc(f"The {SPELL_DEFS[spell_key]['name']} spell overloaded your mind! It's unusable.", "error"))
            return False
        
        # Get effective proficiency (with fatigue applied)
        effective_prof = self.player.get_effective_spell_proficiency(spell_key)
        
        # Roll for success (1D100)
        success_roll = random.randint(1, 100)
        
        # Check for CRITICAL FAILURE (1% chance)
        if random.randint(1, 100) == 1:
            print(self.tc(f"MENTAL OVERLOAD! Your mind fractures. {SPELL_DEFS[spell_key]['name']} is now locked!", "error"))
            self.player.lock_spell(spell_key)
            self.player.apply_spell_fatigue(spell_key)
            return False
        
        # Check for success
        if success_roll <= effective_prof:
            # SPELL SUCCEEDED
            
            # Check for CRITICAL SUCCESS (roll == 01)
            if success_roll == 1:
                print(self.tc("CRITICAL SUCCESS!", "spell"))
            
            # Attempt skill growth (only on success)
            failure_chance = 100 - self.player.spell_proficiencies[spell_key]
            growth_roll = random.randint(1, 100)
            if growth_roll < failure_chance:
                old_prof = self.player.spell_proficiencies[spell_key]
                self.player.spell_proficiencies[spell_key] += 2
                new_prof = self.player.spell_proficiencies[spell_key]
                print(self.tc(f"Your {SPELL_DEFS[spell_key]['name']} proficiency increased: {old_prof}% → {new_prof}%", "success"))
            
            # Apply fatigue AFTER successful cast
            self.player.apply_spell_fatigue(spell_key)
            return True
        else:
            # SPELL FAILED
            print(self.tc(f"Your {SPELL_DEFS[spell_key]['name']} fails to manifest.", "error"))
            # Fatigue still applies even on failure
            self.player.apply_spell_fatigue(spell_key)
            return False

    def cmd_cast(self, args: str) -> None:
        """
        CAST <spell> [target]
        Main spell casting command.
        """
        if not args:
            print(self.tc("Cast what? (CAST BLAST, CAST HEAL, CAST SPEED, CAST POWER)", "error"))
            return
        
        parts = args.split(maxsplit=1)
        spell_name = parts[0].lower()
        target_name = parts[1] if len(parts) > 1 else None
        
        # Map spell names to spell keys
        spell_map = {
            "blast": "blast",
            "heal": "heal",
            "speed": "speed",
            "power": "power",
        }
        
        spell_key = spell_map.get(spell_name)
        if not spell_key:
            print(self.tc(f"Unknown spell: {spell_name}", "error"))
            return
        
        # Attempt to cast
        if self._attempt_cast(spell_key, target_name):
            # Execute the spell effect
            spell_method = f"_cast_{spell_key}"
            if hasattr(self, spell_method):
                getattr(self, spell_method)(target_name)

    def _cast_blast(self, target_name: str = None) -> None:
        """
        Blast spell: 1D6 damage, bypasses armor completely.
        """
        # Find target monster
        monsters = self.world.monsters_in_room(self.player.room_id)
        
        if target_name:
            target = self.world.find_monster_by_name(target_name, monsters)
        else:
            if not monsters:
                print(self.tc("No target here.", "error"))
                return
            target = monsters[0]
        
        if not target:
            print(self.tc("Target not found.", "error"))
            return
        
        # Roll damage (1D6, bypasses armor)
        damage = random.randint(1, 6)
        print(self.tc(f"A blast of pure energy hits {target.name} for {damage} damage!", "spell"))
        
        # Apply damage (no armor reduction)
        target.hp -= damage
        
        # Monster dies?
        if target.hp <= 0:
            print(self.tc(f"{target.name} {target.death_message}", "win"))
            target.is_alive = False
            return
        
        # Monster attacks back if still alive
        print(self.tc(f"{target.name} {target.health_desc()}", "sys"))
        self.monster_round(target)

    def _cast_heal(self, target_name: str = None) -> None:
        """
        Heal spell: 1D10 HP restoration.
        """
        # Roll healing (1D10)
        healing = random.randint(1, 10)
        old_hp = self.player.hp
        self.player.hp = min(self.player.hp + healing, self.player.hp_max)
        actual_healing = self.player.hp - old_hp
        
        print(self.tc(f"You feel revitalized! ({actual_healing} HP restored)", "heal"))

    def _cast_speed(self, target_name: str = None) -> None:
        """
        Speed spell: Double agility for 11-20 combat rounds.
        """
        # Roll duration
        duration = 10 + random.randint(1, 10)  # 11-20
        
        if self.player.speed_active:
            # Recast resets duration (no stacking)
            self.player.speed_rounds_remaining = duration
            print(self.tc(f"Your speed resets! ({duration} rounds remaining)", "spell"))
        else:
            # Activate speed
            self.player.activate_speed(duration)
            print(self.tc(f"Your body surges with supernatural speed! ({duration} rounds)", "spell"))

    def _cast_power(self, target_name: str = None) -> None:
        """
        Power spell: Adventure-specific effect.
        For Beginner's Cave: sonic boom (no gameplay effect).
        """
        messages = [
            "A sonic boom erupts from your body!",
            "The air crackles with chaotic energy!",
            "You hear mysterious laughter echo through the chamber!",
            "Reality shimmers around you momentarily.",
            "An otherworldly hum fills the air.",
        ]
        print(self.tc(random.choice(messages), "spell"))

    def cmd_spells(self) -> None:
        """Show all learned spells and proficiencies."""
        print()
        print(self.tc("SPELLS:", "title"))
        print()
        
        for spell_key, spell_info in SPELL_DEFS.items():
            prof = self.player.spell_proficiencies.get(spell_key)
            if prof is None:
                print(self.tc(f"  {spell_info['name']:<12} : Not learned ({spell_info['cost']} gold)", "sys"))
            else:
                locked = " [LOCKED]" if self.player.is_spell_locked(spell_key) else ""
                print(self.tc(f"  {spell_info['name']:<12} : {prof:>3}%{locked}", "spell"))
        
        print()

