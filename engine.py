"""
engine.py - Eamon Redux game engine (REWRITTEN for proficiency-based magic system).

Exit codes: 0=quit, 1=completed, 2=died
"""

from __future__ import annotations

import sys
import os
import json
import random
import importlib
from character import SPELL_DEFS, WEAPON_TYPES
from world import WeaponType

# ── readline: arrow-key history + tab completion ──────────────────────────────

try:
    import readline
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass  # Windows fallback

from world import World, DIRECTIONS, DIR_ABBREV, Attitude, ArtifactType
from core.base_handlers import BaseAdventureHandlers
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
    HR         = "\033[0;32m"   # green           — room separator line
    ROOM_NAME  = "\033[1;32m"   # bright green    — room title
    ROOM_DESC  = "\033[0;32m"   # green           — room description
    EXITS      = "\033[0;33m"   # yellow          — exit list
    ITEM       = "\033[0;33m"   # yellow          — item names
    ITEM_LABEL = "\033[1;33m"   # bright yellow   — item labels / equipped tag
    EQUIPPED   = "\033[1;33m"   # bright yellow   — equipped marker
    SYS        = "\033[0;36m"   # cyan            — system messages
    ERROR      = "\033[1;31m"   # bright red      — errors
    WARN       = "\033[1;35m"   # bright magenta  — creatures, danger, warnings
    COMBAT_HIT = "\033[1;31m"   # bright red      — player hits monster
    COMBAT_DMG = "\033[0;31m"   # red             — monster hits player
    COMBAT_WIN = "\033[1;33m"   # bright yellow   — monster defeated
    COMBAT_DIE = "\033[1;31m"   # bright red      — player death
    SPELL      = "\033[1;36m"   # bright cyan     — spell effects
    HEAL_COLOR = "\033[0;32m"   # green           — healing
    MANA_COLOR = "\033[1;36m"   # bright cyan     — mana display
    TITLE      = "\033[1;32m"   # bright green    — adventure titles
    INTRO      = "\033[0;32m"   # green           — adventure intro text
    HELP       = "\033[0;36m"   # cyan            — help text

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

# ── Item Persistence ──────────────────────────────────────────────────────────

def _sync_player_to_character(character, player, world) -> None:
    """Sync all runtime player state back to the persistent character."""
    character.spell_proficiencies  = player.spell_proficiencies.copy()
    character.weapon_proficiencies = player.weapon_proficiencies.copy()
    character.hp   = player.hp
    character.gold = player.gold
    character.xp   = player.xp
    character.equipped = {}
    for slot, aid in player.equipped.items():
        if aid is not None:
            artifact = world.artifacts.get(aid)
            if artifact:
                character.equipped[slot] = artifact.name


def _save_carried_items(character, world) -> None:
    """
    Save carried items to the character's items file.
    Items flagged adventure_only are auto-sold for their value (min 1 gold)
    and not persisted.
    """
    safe_name = character.name.lower().replace(" ", "_")
    items_path = os.path.join("characters", f"{safe_name}_items.json")
    os.makedirs("characters", exist_ok=True)

    carried = [a for a in world.artifacts.values() if a.room_id is None]

    to_save = []
    auto_sold = []   # list of (name, gold)

    for a in carried:
        if (a.flags or {}).get("adventure_only"):
            gold = max(1, a.value if a.value > 0 else 1)
            auto_sold.append((a.name, gold))
            character.gold += gold
        else:
            to_save.append(a)

    if auto_sold:
        print()
        print("\033[0;33mThe following items could not leave the adventure:\033[0m")
        for name, gold in auto_sold:
            print(f"\033[0;33m  • {name}  →  {gold} gold\033[0m")
        total = sum(g for _, g in auto_sold)
        print(f"\033[0;33mYou received {total} gold.\033[0m")
        character.save()   # re-save with updated gold

    with open(items_path, "w") as f:
        json.dump([a.to_dict() for a in to_save], f, indent=2)

# ── Game Engine ───────────────────────────────────────────────────────────────

class Engine:
    """Main game engine for Eamon Redux adventures."""

    def __init__(self, world: World, character, adventure_path: str = None):
        """Initialize engine with world and character data."""
        self.world = world
        self.character = character
        self.adventure_path = adventure_path
        self.game_data = {}

        # Create player runtime state from character
        self.player = Player(
            name=character.name,
            room_id=world.start_room,
            strength=character.strength,
            dex=character.dex,
            con=character.con,
            intelligence=character.intelligence,
            wis=character.wis,
            charisma=character.charisma,
            hp=character.hp_max,
            mana=character.mana_max,
            gold=character.gold,
            spell_proficiencies=character.spell_proficiencies.copy(),
            weapon_proficiencies=character.weapon_proficiencies.copy(),
            xp=character.xp,
            level=character.level,
            max_carry_weight=character.carry_capacity,
        )
        # Load character's carried items from JSON file
        self._load_character_items(character)

        # Suppress body artifacts until their monster is killed
        self._suppress_body_artifacts()

        # Initialize spell fatigue multipliers to 1.0
        for spell_key in self.player.spell_proficiencies:
            if self.player.spell_proficiencies[spell_key] is not None:
                self.player.spell_fatigue_multiplier[spell_key] = 1.0
        
        self.turn = 0
        self.in_combat = False
        self.enemy = None
        self.running = True  # BUG-01 fix: must be set before any room-entry hooks
        self.verbose_mode = True  # VERBOSE=full desc every entry, BRIEF=brief after first visit

        # Tier 1: generic flag-reading handlers
        self.base_handlers = BaseAdventureHandlers(self)

        # Tier 2: adventure-specific custom handlers (optional)
        self.custom_handlers = {}
        if adventure_path:
            self._load_adventure_handlers(adventure_path)

    # ── Handler infrastructure ─────────────────────────────────────────────────

    def _load_adventure_handlers(self, adventure_path: str) -> None:
        """Dynamically load adventure-specific handlers if they exist."""
        try:
            adventure_name = adventure_path.rstrip("/").split("/")[-1]
            module = importlib.import_module(f"adventures.{adventure_name}.handlers")
            if hasattr(module, "HANDLERS"):
                self.custom_handlers = getattr(module, "HANDLERS")
            elif hasattr(module, "AdventureHandlers"):
                self.custom_handlers = getattr(module, "AdventureHandlers")(self)
        except ImportError:
            self.custom_handlers = {}
        except Exception as e:
            print(f"Warning: Could not load adventure handlers: {e}")
            self.custom_handlers = {}

    def trigger_event(self, event_id: str) -> None:
        """Trigger a named event, checking custom handlers first."""
        if isinstance(self.custom_handlers, dict):
            handler = self.custom_handlers.get(event_id)
            if handler and callable(handler):
                handler(self)
                return
        if hasattr(self.custom_handlers, event_id):
            method = getattr(self.custom_handlers, event_id)
            if callable(method):
                method(self)

    def call_hook(self, hook_name: str, *args, **kwargs):
        """Call a hook — custom handlers take priority, then base handlers."""
        if isinstance(self.custom_handlers, dict):
            handler = self.custom_handlers.get(hook_name)
            if handler and callable(handler):
                return handler(self, *args, **kwargs)
        elif hasattr(self.custom_handlers, hook_name):
            method = getattr(self.custom_handlers, hook_name)
            if callable(method):
                return method(*args, **kwargs)

        if hasattr(self.base_handlers, hook_name):
            method = getattr(self.base_handlers, hook_name)
            if callable(method):
                return method(*args, **kwargs)

    def on_game_start(self) -> None:
        self.call_hook("on_game_start")

    def on_enter_room(self, room_id: int) -> None:
        self.call_hook("on_enter_room", room_id)

    def on_talk_to_npc(self, npc_name: str) -> None:
        self.call_hook("on_talk_to_npc", npc_name)

    def on_use_item(self, artifact_name: str, target: str = None) -> bool:
        result = self.call_hook("on_use_item", artifact_name, target)
        return result if result is not None else False

    def _body_monster_name(self, artifact) -> str | None:
        """Extract the creature name from a body artifact name, or None if not a body."""
        name = artifact.name.lower()
        if name.startswith("dead "):
            return name[5:]
        if name.endswith("'s body"):
            return name[:-7]
        return None

    _SUPPRESSED = -1  # sentinel room_id for body artifacts not yet revealed

    def _suppress_body_artifacts(self) -> None:
        """Hide body artifacts that have a living monster in the same room."""
        for artifact in self.world.artifacts.values():
            creature = self._body_monster_name(artifact)
            if creature is None:
                continue
            for monster in self.world.monsters.values():
                if (monster.is_alive
                        and monster.name.lower() == creature
                        and monster.room_id == artifact.room_id):
                    artifact.room_id = self._SUPPRESSED
                    break

    def _reveal_body_artifact(self, monster) -> None:
        """Place a monster's body artifact in the room when it dies."""
        patterns = {f"dead {monster.name.lower()}", f"{monster.name.lower()}'s body"}
        for artifact in self.world.artifacts.values():
            if artifact.room_id == self._SUPPRESSED and artifact.name.lower() in patterns:
                artifact.room_id = monster.room_id
                break

    def on_monster_defeated(self, monster_id: int) -> None:
        monster = self.world.monsters.get(monster_id)
        if monster:
            self._reveal_body_artifact(monster)
        self.call_hook("on_monster_defeated", monster_id)

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
    
    def _load_character_items(self, character) -> None:
        """Load character's carried items from JSON and add to world."""
        from world import Artifact
        import os
        import json

        safe_name = character.name.lower().replace(" ", "_")
        items_path = os.path.join("characters", f"{safe_name}_items.json")

        if not os.path.exists(items_path):
            return

        try:
            with open(items_path) as f:
                items_data = json.load(f)

            for item_dict in items_data:
                # Drop adventure_only items that slipped into the save file
                if item_dict.get("flags", {}).get("adventure_only"):
                    continue
                artifact = Artifact.from_dict(item_dict)
                artifact.room_id = None
                # Avoid overwriting adventure artifacts with same ID
                if artifact.id in self.world.artifacts:
                    artifact.id = max(self.world.artifacts.keys(), default=0) + 1
                self.world.artifacts[artifact.id] = artifact

        except (json.JSONDecodeError, IOError, KeyError):
            pass

        # Restore equipped slots by name, then re-apply any stat bonuses
        for slot, item_name in character.equipped.items():
            if item_name:
                for artifact in self.world.artifacts.values():
                    if artifact.name == item_name and artifact.room_id is None:
                        self.player.equipped[slot] = artifact.id
                        self.player._apply_stat_bonuses(artifact)
                        break

    # ── Room & World ──────────────────────────────────────────────────────────

    # ── Follower helpers ──────────────────────────────────────────────────────

    def active_followers(self) -> list:
        """Return followers who are still alive."""
        return [m for m in self.player.followers if m.is_alive]

    def _move_followers(self, new_room_id) -> None:
        """Move all living followers to the player's new room."""
        for follower in self.active_followers():
            follower.room_id = new_room_id

    def _follower_combat_turn(self, enemy) -> None:
        """Each living follower in the room attacks the enemy (if they can fight)."""
        for follower in self.active_followers():
            if follower.room_id != self.player.room_id:
                continue
            if not enemy.is_alive:
                break
            if (follower.flags or {}).get("can_fight") is False:
                continue
            hit_chance = max(5, min(95, 50 - enemy.armor_class))
            if random.randint(1, 100) <= hit_chance:
                dmg = max(1, roll(follower.damage_dice, follower.damage_sides) - enemy.armor_class)
                enemy.hp -= dmg
                print(self.tc(f"{follower.name} hits {enemy.name} for {dmg} damage!", "heal"))
                if enemy.hp <= 0:
                    enemy.is_alive = False
                    print(self.tc(f"{enemy.name} {enemy.death_message}", "win"))
                    self.on_monster_defeated(enemy.id)
                    xp = enemy.xp_value or (enemy.hp_max * 10)
                    self.player.xp += xp
                    print(self.tc(f"You gain {xp} XP!", "heal"))
            else:
                print(self.tc(f"{follower.name} misses {enemy.name}.", "sys"))

    def _monster_attacks_followers(self, monster) -> None:
        """A hostile monster may strike a follower instead of (or after) the player."""
        targets = [f for f in self.active_followers()
                   if f.room_id == self.player.room_id]
        if not targets:
            return
        target = random.choice(targets)
        hit_chance = max(5, min(95, 50))
        if random.randint(1, 100) <= hit_chance:
            dmg = max(1, roll(monster.damage_dice, monster.damage_sides))
            target.hp -= dmg
            print(self.tc(f"{monster.name} strikes {target.name} for {dmg} damage!", "dmg"))
            if target.hp <= 0:
                target.is_alive = False
                print(self.tc(f"{target.name} has fallen!", "die"))
                self.player.followers = [f for f in self.player.followers if f.is_alive]

    def _has_light(self) -> bool:
        """True if the current room is illuminated — not dark, or player/room has a lit light source."""
        room = self.world.get_room(self.player.room_id)
        if not room or not room.is_dark:
            return True
        sources = self.world.artifacts_carried() + self.world.artifacts_in_room(self.player.room_id)
        return any(a.artifact_type == ArtifactType.LIGHT and a.lit for a in sources)

    def look(self, brief: bool = False) -> None:
        """Display current room. brief=True shows short description if available."""
        room = self.world.get_room(self.player.room_id)
        if not room:
            print(self.tc("(Room not found)", "error"))
            return

        print()

        if room.is_dark and not self._has_light():
            print(self.tc("*** Pitch Dark ***", "room"))
            print(self.tc("─" * 72, "exits"))
            print(self.tc("It is pitch dark. You cannot see anything.", "desc"))
            print(self.tc("(If you are carrying a torch or lantern, type LIGHT TORCH to use it.)", "sys"))
            print()
            return

        print(self.tc(room.name, "room"))
        print(self.tc("─" * 72, "exits"))
        if brief and room.brief_description:
            print(self.tc(wrap(room.brief_description), "desc"))
        else:
            print(self.tc(wrap(room.description), "desc"))

        # Artifacts in room
        artifacts = self.world.artifacts_in_room(self.player.room_id)
        if artifacts:
            print()
            print(self.tc("You see:", "sys"))
            for a in artifacts:
                print(self.tc(f"  • {a.name}", "item"))

        # Companions (followers in this room)
        companions = [f for f in self.active_followers()
                      if f.room_id == self.player.room_id]
        if companions:
            print()
            print(self.tc("Companions:", "heal"))
            for f in companions:
                print(self.tc(f"  • {f.name} ({f.health_desc()})", "heal"))

        # Monsters in room (hostile/neutral only — not followers)
        follower_ids = {f.id for f in self.player.followers}
        monsters = [m for m in self.world.monsters_in_room(self.player.room_id)
                    if m.id not in follower_ids]
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

    _COMMANDS_REQUIRING_NOUN = frozenset({
        "attack", "examine", "read", "talk", "get", "drop", "equip", "unequip",
        "use", "eat", "drink", "cast", "light", "open", "close", "give", "put",
        "free", "unlock",
    })

    def handle(self, raw_input: str) -> int:
        """
        Handle a player command.
        Returns: 0=quit, 1=win, 2=die, 3=tavern, -1=continue
        """
        self.turn += 1

        # ── Parse command ────────────────────────────────────────────────────
        try:
            cmd, status, suggestions = parse_command(raw_input, "engine")
        except Exception as e:
            print(self.tc(f"Command parser error: {e}", "error"))
            return -1

        if status == "empty":
            return -1
        elif status == "not_found":
            print(self.tc("Unknown command. Type HELP for available commands.", "error"))
            return -1
        elif status == "ambiguous":
            print(self.tc(f"Ambiguous: {', '.join(suggestions)}. Be more specific.", "warn"))
            return -1

        if status not in ("partial", "exact"):
            return -1

        # ── Safe argument extraction ─────────────────────────────────────────
        input_parts = raw_input.split(maxsplit=1)
        noun = input_parts[1].strip() if len(input_parts) > 1 else ""

        if not noun and cmd in self._COMMANDS_REQUIRING_NOUN:
            print(self.tc(f"{cmd.upper()} what?", "error"))
            return -1

        # ── Command dispatch with error wrapping ─────────────────────────────
        try:
            # ── Movement ─────────────────────────────────────────────────────
            if cmd in ("north", "south", "east", "west", "up", "down",
                       "northeast", "northwest", "southeast", "southwest"):
                self.cmd_go(cmd)
                if self.player.room_id == "EXIT_TAVERN":
                    return 3
                self.player.recover_all_spell_fatigue(random.randint(5, 10))
            elif cmd == "go":
                go_parts = raw_input.split()
                if len(go_parts) > 1:
                    self.cmd_go(go_parts[1])
                else:
                    print(self.tc("Go where?", "error"))
                if self.player.room_id == "EXIT_TAVERN":
                    return 3
                self.player.recover_all_spell_fatigue(random.randint(5, 10))
            elif cmd == "flee":
                self.cmd_flee()

            # ── Examination ──────────────────────────────────────────────────
            elif cmd == "look":
                self.look()
            elif cmd == "verbose":
                self.verbose_mode = True
                print(self.tc("Verbose mode on — full room descriptions every visit.", "sys"))
            elif cmd == "brief":
                self.verbose_mode = False
                print(self.tc("Brief mode on — short descriptions after first visit.", "sys"))
            elif cmd == "examine":
                self.cmd_examine(noun)
            elif cmd == "read":
                self.cmd_read(noun)

            # ── Interaction ──────────────────────────────────────────────────
            elif cmd == "talk":
                talk_parts = raw_input.strip().lower().split(maxsplit=2)
                if len(talk_parts) >= 3 and talk_parts[1] == "to":
                    noun = talk_parts[2]
                self.cmd_talk(noun)
            elif cmd == "say":
                self.cmd_say(noun)
            elif cmd == "smile":
                self.cmd_smile(noun)
            elif cmd == "free":
                self.cmd_free(noun)

            # ── Inventory ────────────────────────────────────────────────────
            elif cmd == "inventory":
                self.cmd_inventory()
            elif cmd == "get":
                if not noun:
                    self.cmd_get("")
                elif noun.lower() == "all":
                    self.cmd_get_all("")
                elif noun.lower().startswith("all "):
                    self.cmd_get_all(noun[4:].strip())
                else:
                    self.cmd_get(noun)
            elif cmd == "drop":
                self.cmd_drop(noun)
            elif cmd == "put":
                self.cmd_put(noun)
            elif cmd == "give":
                self.cmd_give(noun)
            elif cmd == "use":
                self.cmd_use(noun)
            elif cmd == "light":
                self.cmd_light(noun)
            elif cmd == "open":
                self.cmd_open(noun)
            elif cmd == "close":
                self.cmd_close(noun)
            elif cmd == "unlock":
                self.cmd_unlock(noun)

            # ── Equipment ────────────────────────────────────────────────────
            elif cmd == "equip":
                self.cmd_equip_safe(noun)
            elif cmd == "unequip":
                self.cmd_unequip(noun)
            elif cmd == "equipment":
                self.cmd_equipment()

            # ── Combat ───────────────────────────────────────────────────────
            elif cmd == "attack":
                self.cmd_attack_safe(noun)
            elif cmd == "cast":
                self.cmd_cast_safe(noun)
            elif cmd in ("blast", "heal", "speed", "power"):
                self.cmd_cast_safe(f"{cmd} {noun}".strip())

            # ── Items ────────────────────────────────────────────────────────
            elif cmd == "eat":
                self.cmd_eat(noun)
            elif cmd == "drink":
                self.cmd_drink(noun)

            # ── Status ───────────────────────────────────────────────────────
            elif cmd == "character":
                self.cmd_status()
            elif cmd == "health":
                self.cmd_health()
            elif cmd == "rest":
                self.cmd_rest()
            elif cmd == "spells":
                self.cmd_spells()

            # ── Game Control ─────────────────────────────────────────────────
            elif cmd == "save":
                self.cmd_save(noun)
            elif cmd == "load":
                self.cmd_load("")
            elif cmd in ("help", "?"):
                self.cmd_help()
            elif cmd == "quit":
                return self.cmd_quit_with_confirm()

            # ── Special / Adventure hooks ─────────────────────────────────────
            elif cmd == "trollsfire":
                self.cmd_trollsfire()
            else:
                self.call_hook("on_special_command", cmd, noun)

        except Exception as e:
            print(self.tc(f"Error executing command: {e}", "error"))
            return -1

        # ── Check win/death ──────────────────────────────────────────────────
        if self._check_win():
            return 1
        if not self.player.is_alive:
            return 2

        return -1


    def _check_win(self) -> bool:
        """Check if player has achieved win condition."""
        wc = self.world.win_condition
        if not wc:
            return False
        return self._eval_condition(wc)

    def _eval_condition(self, cond: dict) -> bool:
        """Evaluate a single condition dict."""
        ctype = cond.get("type")
        if ctype == "reach_room":
            return self.player.room_id == cond.get("room_id")
        elif ctype == "kill_monster":
            m = self.world.monsters.get(cond.get("monster_id"))
            return bool(m and not m.is_alive)
        elif ctype == "kill_all":
            return not any(m.is_alive for m in self.world.monsters.values())
        elif ctype == "carry_artifact":
            a = self.world.artifacts.get(cond.get("artifact_id"))
            return bool(a and a.room_id is None)
        elif ctype == "has_follower":
            mid = cond.get("monster_id")
            return any(f.id == mid for f in self.player.followers)
        elif ctype == "compound":
            return all(self._eval_condition(c) for c in cond.get("all_of", []))
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

        # BUG-09 fix: block movement while hostile monsters are present
        hostiles = [m for m in self.world.monsters_in_room(self.player.room_id)
                    if m.attitude == Attitude.HOSTILE]
        if hostiles:
            print(self.tc("You cannot move while hostile monsters are present! Fight or flee.", "warn"))
            return

        room = self.world.get_room(self.player.room_id)
        if not room:
            print(self.tc("(No current room)", "error"))
            return
        
        # Check for exit
        if direction not in room.exits:
            print(self.tc("You can't go that way.", "error"))
            return
            
        # Check for surface exit — signals engine to return player to tavern
        next_exit = room.exits[direction]
        if next_exit == "EXIT_TAVERN":
            print(self.tc("You escape to the surface and return to town!", "spell"))
            self.player.room_id = "EXIT_TAVERN"
            return
        
        # Check for locked exit
        if direction in room.locked_exits:
            key_id = room.locked_exits[direction]
            key = self.world.artifacts.get(key_id)
            if key and key.room_id is not None:
                print(self.tc(f"The {direction} exit is locked. (Need: {key.name})", "warn"))
                return
        
        # Move to new room
        new_room_id = room.exits[direction]
        self.player.room_id = new_room_id
        self._move_followers(new_room_id)

        new_room = self.world.get_room(new_room_id)
        
        if new_room:
            if new_room.first_visit:
                new_room.first_visit = False
                self.look()
            elif self.verbose_mode:
                self.look()
            else:
                self.look(brief=True)
        
        # Fire room-entry hooks (win conditions, event triggers)
        self.on_enter_room(new_room_id)
        if not self.running:
            return

        # Check for hostile monsters — monster gets the first strike on entry
        monsters = self.world.monsters_in_room(new_room_id)
        for m in monsters:
            if m.attitude == Attitude.HOSTILE:
                print(self.tc(f"A {m.name} leaps at you!", "warn"))
                self.monster_round(m)
                break

    def cmd_status(self) -> None:
        """Display character sheet (same layout as tavern CHAR command)."""
        # Sync live adventure state into character before display
        self.character.hp   = self.player.hp
        self.character.gold = self.player.gold
        self.character.xp   = self.player.xp
        self.character.level = self.player.level
        # Sync equipped items by name so the sheet shows current gear
        self.character.equipped = {}
        for slot, aid in self.player.equipped.items():
            if aid is not None:
                a = self.world.artifacts.get(aid)
                if a:
                    self.character.equipped[slot] = a.name
        # Pass player's current stats so equipment bonuses show on the sheet
        effective = {s: getattr(self.player, s)
                     for s in ('strength', 'dex', 'con', 'intelligence', 'wis', 'charisma')}
        print(f"\033[1;33m{self.character.stat_summary(effective_stats=effective)}\033[0m")

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
            # Match if user's noun appears in artifact type OR artifact type appears in noun
            # (handles "potions" matching "potion", "weapons" matching "weapon", etc.)
            noun_lower = noun.lower().rstrip("s")  # strip plural 's'
            artifacts = [a for a in artifacts
                         if noun_lower in a.artifact_type.lower()
                         or a.artifact_type.lower() in noun_lower
                         or noun_lower in a.name.lower()]
        
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

    def cmd_equip_safe(self, noun: str) -> None:
        """cmd_equip with pre-flight validation."""
        if not noun:
            print(self.tc("Equip what?", "error"))
            return

        try:
            artifacts = self.world.artifacts_carried()

            if not artifacts:
                print(self.tc("You're not carrying anything to equip.", "error"))
                return

            artifact = self.world.find_artifact_by_name(noun, artifacts)

            if not artifact:
                print(self.tc(f"You're not carrying a {noun}.", "error"))
                return

            if not hasattr(artifact, "artifact_type"):
                print(self.tc(f"Invalid item: {noun}.", "error"))
                return

            self.cmd_equip(noun)

        except Exception as e:
            print(self.tc(f"Equipment error: {e}", "error"))

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
        """Read a readable item — works on items in the room or carried."""
        if not noun:
            print(self.tc("Read what?", "error"))
            return

        # Check room artifacts first, then carried
        candidates = (
            self.world.artifacts_in_room(self.player.room_id)
            + self.world.artifacts_carried()
        )
        artifact = self.world.find_artifact_by_name(noun, candidates)

        if artifact:
            if artifact.artifact_type != ArtifactType.READABLE:
                print(self.tc(f"There's nothing to read on the {artifact.name}.", "error"))
                return
            print()
            print(self.tc(artifact.read_text or "(the page is blank)", "desc"))
            print()
            return

        # Check monsters — can't read a living creature
        monsters = self.world.monsters_in_room(self.player.room_id)
        monster = self.world.find_monster_by_name(noun, monsters)
        if monster:
            print(self.tc(f"You can't read a {monster.name}.", "error"))
            return

        print(self.tc(f"You don't see a {noun} here.", "error"))

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
        
        # Remove from inventory (delete the artifact, don't drop it)
        del self.world.artifacts[artifact.id]

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
        
        # BUG-06 fix: restore 25% HP (not full)
        old_hp = self.player.hp
        restore_hp = max(1, self.player.hp_max // 4)
        self.player.hp = min(self.player.hp + restore_hp, self.player.hp_max)
        hp_restored = self.player.hp - old_hp

        # Restore 25% mana
        old_mana = self.player.mana
        restore_mana = max(1, self.player.mana_max // 4)
        self.player.mana = min(self.player.mana + restore_mana, self.player.mana_max)
        mana_restored = self.player.mana - old_mana

        print(self.tc(f"You rest. ({hp_restored} HP restored, {mana_restored} mana recovered)", "heal"))

        # Fatigue recovery
        recovery = random.randint(5, 10)
        self.player.recover_all_spell_fatigue(recovery)
        print(self.tc(f"Your mental fatigue eases. (fatigue recovery: {recovery}%)", "sys"))

    def cmd_health(self) -> None:
        """Show health status."""
        print()
        print(self.tc(self.player.health_bar(), "sys"))
        print(self.tc(f"Mana: {self.player.mana}/{self.player.mana_max}", "spell"))

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

        if self.player.speed_active:
            print(self.tc(f"Speed: ACTIVE ({self.player.speed_rounds_remaining} rounds remaining)", "spell"))

        print()

    # ── SPELL SYSTEM (NEW) ─────────────────────────────────────────────────────

    def _attempt_cast(self, spell_key: str, target_name: str = None) -> bool:
        """
        Core spell casting logic with mana check, proficiency rolls, fatigue, and skill growth.
        Returns True if spell succeeded, False otherwise.
        """
        # Check if spell is learned
        if self.player.spell_proficiencies.get(spell_key) is None:
            print(self.tc(f"You don't know the {SPELL_DEFS[spell_key]['name']} spell.", "error"))
            return False

        # Check mana
        mana_cost = SPELL_DEFS[spell_key].get("mana_cost", 2)
        if self.player.mana < mana_cost:
            print(self.tc(f"Not enough mana. ({mana_cost} needed, {self.player.mana} available.)", "error"))
            return False

        # Check if spell is locked (1% critical failure from previous overload)
        if self.player.is_spell_locked(spell_key):
            print(self.tc(f"The {SPELL_DEFS[spell_key]['name']} spell overloaded your mind! It's unusable.", "error"))
            return False

        # Deduct mana (spent on attempt regardless of success)
        self.player.mana -= mana_cost

        # Get effective proficiency (with fatigue applied)
        effective_prof = self.player.get_effective_spell_proficiency(spell_key)

        # Check for CRITICAL FAILURE (1% chance — overload)
        if random.randint(1, 100) == 1:
            print(self.tc(f"MENTAL OVERLOAD! Your mind fractures. {SPELL_DEFS[spell_key]['name']} is now locked!", "error"))
            self.player.lock_spell(spell_key)
            self.player.apply_spell_fatigue(spell_key)
            return False

        # Roll for success (1D100)
        success_roll = random.randint(1, 100)

        if success_roll <= effective_prof:
            # SPELL SUCCEEDED
            if success_roll == 1:
                print(self.tc("CRITICAL SUCCESS!", "spell"))

            # Skill growth on success (BUG-07 fix: +1 not +2)
            failure_chance = 100 - self.player.spell_proficiencies[spell_key]
            if random.randint(1, 100) < failure_chance:
                old_prof = self.player.spell_proficiencies[spell_key]
                self.player.spell_proficiencies[spell_key] += 1
                new_prof = self.player.spell_proficiencies[spell_key]
                print(self.tc(f"Your {SPELL_DEFS[spell_key]['name']} proficiency increased: {old_prof}% → {new_prof}%", "success"))

            self.player.apply_spell_fatigue(spell_key)
            return True
        else:
            # SPELL FAILED
            print(self.tc(f"Your {SPELL_DEFS[spell_key]['name']} fails to manifest.", "error"))
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

    def cmd_cast_safe(self, args: str) -> None:
        """cmd_cast with pre-flight validation."""
        if not args:
            print(self.tc("Cast what? (CAST BLAST, CAST HEAL, CAST SPEED, CAST POWER)", "error"))
            return

        try:
            cast_parts = args.split(maxsplit=1)
            spell_name = cast_parts[0].lower()
            target_name = cast_parts[1] if len(cast_parts) > 1 else None

            valid_spells = {"blast", "heal", "speed", "power"}
            if spell_name not in valid_spells:
                print(self.tc(f"Unknown spell: '{spell_name}'. Try: BLAST, HEAL, SPEED, POWER", "error"))
                return

            # Only validate target for blast (the only targeting spell)
            if spell_name == "blast" and target_name:
                monsters = self.world.monsters_in_room(self.player.room_id)
                if not self.world.find_monster_by_name(target_name, monsters):
                    print(self.tc(f"No creature named '{target_name}' here.", "error"))
                    return

            self.cmd_cast(args)

        except Exception as e:
            print(self.tc(f"Spell error: {e}", "error"))

    def _cast_blast(self, target_name: str = None) -> None:
        """
        Blast spell: 1D6 + Intelligence bonus damage, bypasses armor.
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

        # Roll damage (1D6 + Intelligence bonus, bypasses armor)
        damage = max(1, random.randint(1, 6) + self.player.intelligence_bonus)
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
        Heal spell: 1D10 + WIS bonus HP restoration (WIS governs divine/healing magic).
        """
        healing = max(1, random.randint(1, 10) + self.player.wis_bonus)
        old_hp = self.player.hp
        self.player.hp = min(self.player.hp + healing, self.player.hp_max)
        actual_healing = self.player.hp - old_hp

        print(self.tc(f"You feel revitalized! ({actual_healing} HP restored)", "heal"))

    def _cast_speed(self, target_name: str = None) -> None:
        """
        Speed spell: Double DEX for 11-20 combat rounds.
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
        """Show all learned spells with mana costs and affordability."""
        print()
        print(self.tc(f"SPELLS  (mana: {self.player.mana}/{self.player.mana_max}):", "title"))
        print()

        for spell_key, spell_info in SPELL_DEFS.items():
            mana_cost = spell_info.get("mana_cost", 2)
            prof = self.player.spell_proficiencies.get(spell_key)
            if prof is None:
                print(self.tc(f"  {spell_info['name']:<12} : Not learned  ({spell_info['cost']} gold)", "sys"))
            else:
                locked = " [LOCKED]" if self.player.is_spell_locked(spell_key) else ""
                affordable = "✦" if self.player.mana >= mana_cost else "✗"
                print(self.tc(f"  {spell_info['name']:<12} : {prof:>3}%  cost: {mana_cost} mana {affordable}{locked}", "spell"))

        print()

    # ── COMBAT SYSTEM (WITH WEAPON PROFICIENCIES) ───────────────────────────────

    # Weapon types that use ranged combat rules (DEX to hit, no STR damage bonus)
    RANGED_WEAPON_TYPES = {"bow", "crossbow", "sling", "dart", "thrown"}

    def cmd_attack(self, noun: str) -> None:
        """
        ATTACK <monster>
        D&D-style initiative (DEX vs flat d6), ranged/melee split,
        weapon proficiencies, critical hits (5%), fumbles (4%).
        """
        if not noun:
            print(self.tc("Attack what?", "error"))
            return

        monsters = self.world.monsters_in_room(self.player.room_id)
        monster = self.world.find_monster_by_name(noun, monsters)

        if not monster:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return

        if not monster.is_alive:
            print(self.tc(f"The {monster.name} is already dead.", "error"))
            return

        # ── Get weapon, type, and proficiency ────────────────────────────────

        weapon = self.player.equipped_weapon(self.world)
        weapon_type = "unarmed" if not weapon else weapon.weapon_type
        weapon_prof = self.player.weapon_proficiencies.get(weapon_type, 0) if weapon_type else 0
        is_ranged = weapon is not None and weapon_type in self.RANGED_WEAPON_TYPES

        # ── Initiative (D&D-style: 1d6 + DEX bonus vs 1d6 flat) ─────────────

        player_init  = random.randint(1, 6) + self.player.dex_effective_bonus
        monster_init = random.randint(1, 6)
        monster_acts_first = monster_init > player_init  # ties go to player

        if monster_acts_first:
            print(self.tc(
                f"{monster.name} seizes initiative! "
                f"({monster_init} vs your {player_init})", "warn"))
            self.monster_round(monster)
            if not self.player.is_alive or not monster.is_alive:
                return
        else:
            if player_init > monster_init:
                print(self.tc(
                    f"You seize initiative! "
                    f"({player_init} vs {monster_init})", "hit"))

        # ── Roll for hit (DEX governs both melee and ranged) ─────────────────

        dex_bonus  = self.player.dex_effective_bonus
        monster_ac = monster.armor_class

        hit_chance = max(5, min(95, 50 + dex_bonus + weapon_prof - monster_ac))
        hit_roll   = random.randint(1, 100)
        is_hit     = hit_roll <= hit_chance

        # ── Check for FUMBLE (4% chance on any attack) ───────────────────────

        if random.randint(1, 100) <= 4:
            fumble_roll = random.randint(1, 100)
            if fumble_roll <= 35:
                print(self.tc("You fumble the attack but recover!", "warn"))
            elif fumble_roll <= 75:
                print(self.tc(f"You drop your {weapon.name if weapon else 'weapon'}!", "error"))
                if weapon:
                    self.player.unequip_artifact(weapon, self.world)
            elif fumble_roll <= 95:
                print(self.tc("Your weapon breaks!", "error"))
                if weapon:
                    self.player.unequip_artifact(weapon, self.world)
                    weapon.room_id = self.player.room_id
                if random.randint(1, 100) <= 50:
                    damage = random.randint(1, 4)
                    self.player.hp -= damage
                    print(self.tc(f"The broken weapon cuts you for {damage} damage!", "dmg"))
            elif fumble_roll <= 99:
                damage = random.randint(2, 6)
                self.player.hp -= damage
                print(self.tc(f"You accidentally hit yourself for {damage} damage!", "error"))
            else:
                self.player.hp = 0
                print(self.tc("You fatally wound yourself!", "die"))
                return
            if not monster_acts_first:
                self.monster_round(monster)
            return

        # ── Normal attack resolution ──────────────────────────────────────────

        if not is_hit:
            print(self.tc(f"You miss the {monster.name}.", "warn"))
            if not monster_acts_first:
                self.monster_round(monster)
            return

        # ── HIT! Roll damage ──────────────────────────────────────────────────

        if weapon:
            base_damage = roll(weapon.damage_dice, weapon.damage_sides)
        else:
            base_damage = roll(self.player.damage_dice, self.player.damage_sides)

        # STR bonus for melee and unarmed; ranged uses weapon dice only
        if not is_ranged:
            base_damage += self.player.strength_bonus
        base_damage = max(1, base_damage)

        # ── Check for CRITICAL HIT (5% chance on successful hit) ─────────────

        damage      = base_damage
        ignore_armor = False

        if random.randint(1, 100) <= 5:
            crit_roll = random.randint(1, 100)
            if crit_roll <= 50:
                print(self.tc("CRITICAL HIT! You bypass the armor!", "hit"))
                ignore_armor = True
            elif crit_roll <= 85:
                damage = int(damage * 1.5)
                print(self.tc(f"CRITICAL HIT! {damage} damage!", "hit"))
            elif crit_roll <= 95:
                damage = damage * 2
                print(self.tc(f"CRITICAL HIT! {damage} damage!", "hit"))
            elif crit_roll <= 99:
                damage = damage * 3
                print(self.tc(f"CRITICAL HIT! {damage} damage!", "hit"))
            else:
                print(self.tc(f"INSTANT KILL! A perfect strike fells {monster.name}!", "hit"))
                monster.hp = 0

        # ── Apply armor reduction ─────────────────────────────────────────────

        if not ignore_armor:
            damage = max(1, damage - monster_ac)

        # ── Apply damage ──────────────────────────────────────────────────────

        monster.hp -= damage
        attack_label = "shoot" if is_ranged else "hit"
        print(self.tc(f"You {attack_label} {monster.name} for {damage} damage!", "dmg"))

        # ── TrollsFire bonus fire damage (bypasses armor) ────────────────────

        if self.player.trollsfire_active:
            weapon = self.player.equipped_weapon(self.world)
            if weapon and weapon.matches("trollsfire"):
                fire_dmg = roll(1, 4)
                monster.hp -= fire_dmg
                print(self.tc(f"TrollsFire's flames scorch {monster.name} for {fire_dmg} fire damage!", "spell"))

        # ── Monster dies? ─────────────────────────────────────────────────────

        if monster.hp <= 0:
            print(self.tc(f"{monster.name} {monster.death_message}", "win"))
            monster.is_alive = False
            self.player.combat_kills += 1
            self.on_monster_defeated(monster.id)
            xp_value = monster.xp_value or (monster.hp_max * 10)
            self.player.xp += xp_value
            print(self.tc(f"You gain {xp_value} XP!", "heal"))
            if monster.loot_id:
                loot = self.world.artifacts.get(monster.loot_id)
                if loot:
                    loot.room_id = self.player.room_id
                    print(self.tc(f"{monster.name} drops {loot.name}!", "item"))
            return

        # ── Weapon proficiency growth (only on successful hit) ────────────────

        if weapon_type:
            failure_chance = 100 - weapon_prof
            if random.randint(1, 100) < failure_chance:
                old_prof = self.player.weapon_proficiencies.get(weapon_type, 0)
                self.player.weapon_proficiencies[weapon_type] = old_prof + 1
                new_prof = self.player.weapon_proficiencies[weapon_type]
                print(self.tc(f"Your {weapon_type} proficiency increased: {old_prof}% → {new_prof}%", "success"))

        # ── Followers attack ──────────────────────────────────────────────────

        self._follower_combat_turn(monster)

        if not monster.is_alive:
            return

        # ── Monster attacks back (only if monster hasn't gone yet this round) ─

        if not monster_acts_first:
            print(self.tc(f"{monster.name} {monster.health_desc()}", "sys"))
            self.monster_round(monster)

    def cmd_attack_safe(self, noun: str) -> None:
        """cmd_attack with pre-flight validation."""
        if not noun:
            print(self.tc("Attack what?", "error"))
            return

        try:
            monsters = self.world.monsters_in_room(self.player.room_id)

            if not monsters:
                print(self.tc("There are no creatures here to attack.", "error"))
                return

            monster = self.world.find_monster_by_name(noun, monsters)

            if not monster:
                print(self.tc(f"You don't see a {noun} here.", "error"))
                return

            if not getattr(monster, "is_alive", True) or monster.hp <= 0:
                monster.is_alive = False
                print(self.tc(f"The {monster.name} is already dead.", "error"))
                return

            self.cmd_attack(noun)

        except AttributeError as e:
            print(self.tc(f"Invalid creature state: {e}", "error"))
        except Exception as e:
            print(self.tc(f"Combat error: {e}", "error"))

    def monster_round(self, monster) -> None:
        """Monster attacks the player (or a follower, 30% of the time)."""
        if not monster.is_alive:
            return

        # 30% chance monster targets a follower instead of the player
        followers_here = [f for f in self.active_followers()
                          if f.room_id == self.player.room_id]
        if followers_here and random.randint(1, 100) <= 30:
            self._monster_attacks_followers(monster)
        else:
            hit_chance = 50 - self.player.dex_effective_bonus - self.player.armor_class(self.world)
            if random.randint(1, 100) > hit_chance:
                print(self.tc(f"{monster.name} misses you.", "sys"))
            else:
                damage = roll(monster.damage_dice, monster.damage_sides)
                damage = max(1, damage - self.player.armor_class(self.world))
                self.player.hp -= damage
                print(self.tc(f"{monster.name} hits you for {damage} damage!", "dmg"))

        # Decrement speed spell duration
        if self.player.speed_active:
            self.player.tick_speed_duration()
            if not self.player.speed_active:
                print(self.tc("Your speed enhancement fades.", "sys"))

    def cmd_flee(self) -> None:
        """Flee from combat."""
        monsters = self.world.monsters_in_room(self.player.room_id)
        if not monsters:
            print(self.tc("You're not in combat.", "sys"))
            return
        
        # Random direction
        direction = random.choice(DIRECTIONS)
        room = self.world.get_room(self.player.room_id)
        
        # Monster always gets a free strike — whether flee succeeds or not
        for monster in monsters:
            if monster.is_alive:
                print(self.tc(f"{monster.name} strikes as you attempt to flee!", "dmg"))
                self.monster_round(monster)
                break

        if direction not in room.exits:
            print(self.tc(f"You can't flee {direction}! You're trapped!", "warn"))
            return

        print(self.tc(f"You flee {direction}!", "warn"))
        new_room_id = room.exits[direction]
        self.player.room_id = new_room_id
        self._move_followers(new_room_id)

    # ── NPC Interaction ────────────────────────────────────────────────────────

    def cmd_talk(self, noun: str) -> None:
        """Talk to an NPC."""
        if not noun:
            print(self.tc("Talk to whom?", "error"))
            return

        monsters = self.world.monsters_in_room(self.player.room_id)
        npc = self.world.find_monster_by_name(noun, monsters)

        if not npc:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return

        if npc.attitude == Attitude.HOSTILE:
            print(self.tc(f"The {npc.name} snarls at you.", "warn"))
            return

        # Handler manages dialogue, follower recruitment, healing, etc.
        self.on_talk_to_npc(npc.name)

    def cmd_say(self, noun: str) -> None:
        """Broadcast speech to the room."""
        if not noun:
            print(self.tc("Say what?", "error"))
            return
        print(self.tc(f'You say, "{noun}"', "warn"))
        # Let adventure hook react to spoken words
        self.call_hook("on_say", noun.lower())

    def cmd_smile(self, noun: str) -> None:
        """Smile, wave, bow — friendly emote."""
        monsters = self.world.monsters_in_room(self.player.room_id)
        if noun:
            target = self.world.find_monster_by_name(noun, monsters)
            if target:
                print(self.tc(f"You smile at the {target.name}.", "sys"))
                if target.attitude == Attitude.HOSTILE:
                    print(self.tc(f"The {target.name} doesn't look impressed.", "warn"))
                return
        print(self.tc("You smile pleasantly.", "sys"))

    def cmd_free(self, noun: str) -> None:
        """Free or release a creature or captive."""
        if not noun:
            print(self.tc("Free what?", "error"))
            return
        monsters = self.world.monsters_in_room(self.player.room_id)
        target = self.world.find_monster_by_name(noun, monsters)
        if target:
            self.call_hook("on_free", target.name.lower())
            return
        print(self.tc(f"You don't see a {noun} here to free.", "error"))

    def cmd_give(self, noun: str) -> None:
        """Give an item to an NPC — GIVE <item> TO <npc>."""
        if not noun:
            print(self.tc("Give what to whom?", "error"))
            return
        parts = noun.lower().split(" to ", 1)
        if len(parts) != 2:
            print(self.tc("Usage: GIVE <item> TO <npc>", "error"))
            return
        item_name, npc_name = parts[0].strip(), parts[1].strip()
        artifact = self.world.find_artifact_by_name(item_name, self.world.artifacts_carried())
        if not artifact:
            print(self.tc(f"You're not carrying a {item_name}.", "error"))
            return
        monsters = self.world.monsters_in_room(self.player.room_id)
        npc = self.world.find_monster_by_name(npc_name, monsters)
        if not npc:
            print(self.tc(f"You don't see a {npc_name} here.", "error"))
            return
        # Let the adventure hook decide what happens; default: just drop the item
        handled = self.call_hook("on_give", artifact.name.lower(), npc.name.lower())
        if not handled:
            artifact.room_id = self.player.room_id
            print(self.tc(f"You give the {artifact.name} to the {npc.name}.", "sys"))

    def cmd_put(self, noun: str) -> None:
        """Put an item in/on a container — PUT <item> IN <container>."""
        if not noun:
            print(self.tc("Put what where?", "error"))
            return
        for prep in (" in ", " into ", " on ", " inside "):
            if prep in noun.lower():
                parts = noun.lower().split(prep, 1)
                item_name, container_name = parts[0].strip(), parts[1].strip()
                carried = self.world.artifacts_carried()
                artifact = self.world.find_artifact_by_name(item_name, carried)
                if not artifact:
                    print(self.tc(f"You're not carrying a {item_name}.", "error"))
                    return
                room_artifacts = self.world.artifacts_in_room(self.player.room_id)
                container = self.world.find_artifact_by_name(container_name, carried + room_artifacts)
                if not container:
                    print(self.tc(f"You don't see a {container_name} here.", "error"))
                    return
                if container.artifact_type != ArtifactType.CONTAINER:
                    print(self.tc(f"The {container.name} isn't a container.", "error"))
                    return
                artifact.room_id = self.player.room_id
                print(self.tc(f"You put the {artifact.name} in the {container.name}.", "sys"))
                return
        # No preposition — treat as DROP
        self.cmd_drop(noun)

    def cmd_use(self, noun: str) -> None:
        """Generic USE — delegates to the appropriate typed command."""
        if not noun:
            print(self.tc("Use what?", "error"))
            return
        candidates = self.world.artifacts_carried() + self.world.artifacts_in_room(self.player.room_id)
        artifact = self.world.find_artifact_by_name(noun, candidates)
        if not artifact:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return
        t = artifact.artifact_type
        if t == ArtifactType.POTION:
            self.cmd_drink(noun)
        elif t == ArtifactType.FOOD:
            self.cmd_eat(noun)
        elif t in (ArtifactType.WEAPON, ArtifactType.SHIELD, ArtifactType.ARMOR):
            self.cmd_equip(noun)
        elif t == ArtifactType.READABLE:
            self.cmd_read(noun)
        elif t == ArtifactType.LIGHT:
            self.cmd_light(noun)
        else:
            # Let adventure hook handle specialised use
            handled = self.call_hook("on_use", artifact.name.lower())
            if not handled:
                print(self.tc(f"You're not sure how to use the {artifact.name}.", "sys"))

    def cmd_light(self, noun: str) -> None:
        """Light or extinguish a torch, lamp, or other light-source artifact."""
        if not noun:
            print(self.tc("Light what?", "error"))
            return
        candidates = self.world.artifacts_carried() + self.world.artifacts_in_room(self.player.room_id)
        artifact = self.world.find_artifact_by_name(noun, candidates)
        if not artifact:
            print(self.tc(f"You don't see a {noun} here.", "error"))
            return
        if artifact.artifact_type != ArtifactType.LIGHT:
            print(self.tc(f"The {artifact.name} can't be lit.", "error"))
            return

        if artifact.lit:
            handled = self.call_hook("on_extinguish", artifact.name.lower())
            artifact.lit = False
            if not handled:
                print(self.tc(f"You extinguish the {artifact.name}.", "sys"))
            return

        handled = self.call_hook("on_light", artifact.name.lower())
        artifact.lit = True
        if not handled:
            print(self.tc(f"You light the {artifact.name}.", "spell"))
        room = self.world.get_room(self.player.room_id)
        if room and room.is_dark:
            self.look()

    def cmd_trollsfire(self) -> None:
        """TROLLSFIRE — toggle flame on/off if equipped; burns player if only carried."""
        candidates = (self.world.artifacts_in_room(self.player.room_id)
                      + self.world.artifacts_carried())
        sword = self.world.find_artifact_by_name("trollsfire", candidates)
        if not sword:
            print(self.tc("TrollsFire is not here.", "error"))
            return

        is_equipped = self.player.equipped.get("weapon") == sword.id
        is_carried  = sword.room_id is None

        if not is_carried:
            print(self.tc(sword.description, "desc"))
            print(self.tc("(GET TROLLSFIRE to pick it up, then EQUIP it.)", "sys"))
            return

        if not is_equipped:
            burn = roll(1, 4)
            self.player.hp -= burn
            print(self.tc(
                "TrollsFire surges with uncontrolled flame in your unready hands!", "dmg"))
            print(self.tc(f"The fire burns you for {burn} damage!", "dmg"))
            return

        # Toggle flame
        if self.player.trollsfire_active:
            self.player.trollsfire_active = False
            print(self.tc("TrollsFire's flame dies down to a cold gleam.", "sys"))
        else:
            self.player.trollsfire_active = True
            print(self.tc(
                "TrollsFire FLAMES ON! A blade of roaring fire erupts from the sword's edge!", "spell"))
            print(self.tc("(+1d4 fire damage per strike while the blade burns)", "help"))

    # ── Save/Load System ───────────────────────────────────────────────────────

    def cmd_save(self, noun: str) -> None:
        """Save game to a slot."""
        adv_name = os.path.basename(self.adventure_path.rstrip("/")) if self.adventure_path else "unknown"

        player_state = {
            "name":                    self.player.name,
            "room_id":                 self.player.room_id,
            "hp":                      self.player.hp,
            "mana":                    self.player.mana,
            "gold":                    self.player.gold,
            "xp":                      self.player.xp,
            "level":                   self.player.level,
            "spell_proficiencies":     self.player.spell_proficiencies.copy(),
            "weapon_proficiencies":    self.player.weapon_proficiencies.copy(),
            "equipped":                {k: v for k, v in self.player.equipped.items()},
            "spell_fatigue_multiplier": self.player.spell_fatigue_multiplier.copy(),
            "spell_locked":            self.player.spell_locked.copy(),
            "speed_active":            self.player.speed_active,
            "speed_rounds_remaining":  self.player.speed_rounds_remaining,
            "quest_flags":             self.player.quest_flags.copy(),
        }

        world_state = {
            "adv_path": self.adventure_path,
            "monsters": {
                str(mid): {"hp": m.hp, "is_alive": m.is_alive, "room_id": m.room_id}
                for mid, m in self.world.monsters.items()
            },
            "artifacts": {
                str(aid): {"room_id": a.room_id, "lit": a.lit}
                for aid, a in self.world.artifacts.items()
            },
        }

        save_game_slotted(self.character.name, adv_name, player_state, world_state)

    def _apply_save_data(self, data: dict) -> None:
        """Restore player and world state from a save dict, handling stat bonuses correctly."""
        ps = data.get("player", {})
        ws = data.get("world", {})

        # Reverse bonuses from any equipment applied at startup, then clear equipped
        for slot, aid in list(self.player.equipped.items()):
            if aid is not None:
                a = self.world.artifacts.get(aid)
                if a:
                    self.player._apply_stat_bonuses(a, reverse=True)
        self.player.equipped = {}

        # Restore scalar player state
        self.player.room_id                  = ps.get("room_id", self.player.room_id)
        self.player.hp                       = ps.get("hp", self.player.hp)
        self.player.mana                     = ps.get("mana", self.player.mana)
        self.player.gold                     = ps.get("gold", self.player.gold)
        self.player.xp                       = ps.get("xp", self.player.xp)
        self.player.level                    = ps.get("level", self.player.level)
        self.player.spell_proficiencies      = ps.get("spell_proficiencies", self.player.spell_proficiencies)
        self.player.weapon_proficiencies     = ps.get("weapon_proficiencies", self.player.weapon_proficiencies)
        self.player.spell_fatigue_multiplier = ps.get("spell_fatigue_multiplier", self.player.spell_fatigue_multiplier)
        self.player.spell_locked             = ps.get("spell_locked", self.player.spell_locked)
        self.player.speed_active             = ps.get("speed_active", False)
        self.player.speed_rounds_remaining   = ps.get("speed_rounds_remaining", 0)
        self.player.quest_flags              = ps.get("quest_flags", {})

        # Restore equipped items and re-apply their stat bonuses
        for slot, aid in ps.get("equipped", {}).items():
            if aid is not None:
                aid = int(aid)
                a = self.world.artifacts.get(aid)
                if a:
                    self.player.equipped[slot] = aid
                    self.player._apply_stat_bonuses(a)

        # Restore world state
        for mid_str, mstate in ws.get("monsters", {}).items():
            mid = int(mid_str)
            if mid in self.world.monsters:
                m = self.world.monsters[mid]
                m.hp       = mstate.get("hp", m.hp)
                m.is_alive = mstate.get("is_alive", m.is_alive)
                m.room_id  = mstate.get("room_id", m.room_id)

        for aid_str, astate in ws.get("artifacts", {}).items():
            aid = int(aid_str)
            if aid in self.world.artifacts:
                self.world.artifacts[aid].room_id = astate.get("room_id")
                self.world.artifacts[aid].lit = astate.get("lit", False)

    def cmd_load(self, noun: str) -> None:
        """Load a saved game from a slot."""
        adv_name = os.path.basename(self.adventure_path.rstrip("/")) if self.adventure_path else "unknown"
        data = load_game_slotted(self.character.name, adv_name)
        if not data:
            return
        self._apply_save_data(data)
        print(self.tc("Game loaded.", "sys"))
        self.look()

    # ── Help & Quit ────────────────────────────────────────────────────────────

    def cmd_help(self) -> None:
        """Show available commands."""
        print()
        print(self.tc("ADVENTURE COMMANDS", "title"))
        print()
        print(self.tc("Movement", "sys"))
        print(self.tc("  N S E W U D  NE NW SE SW  GO <dir>  FLEE / RUN", "help"))
        print()
        print(self.tc("Interaction", "sys"))
        print(self.tc("  LOOK  EXAMINE <thing>  READ <item>", "help"))
        print(self.tc("  TALK TO <npc>  SAY <words>  SMILE  FREE <creature>", "help"))
        print()
        print(self.tc("Inventory", "sys"))
        print(self.tc("  INVENTORY  GET <item>  DROP <item>  GIVE <item> TO <npc>", "help"))
        print(self.tc("  PUT <item> IN <container>  USE <item>  LIGHT <item>", "help"))
        print(self.tc("  EAT <food>  DRINK <potion>  OPEN/CLOSE <item>", "help"))
        print()
        print(self.tc("Equipment", "sys"))
        print(self.tc("  EQUIP / WEAR / READY <item>  REMOVE <item>  EQUIPMENT", "help"))
        print()
        print(self.tc("Combat", "sys"))
        print(self.tc("  ATTACK / FIGHT / KILL / HIT <monster>", "help"))
        print()
        print(self.tc("Magic", "sys"))
        print(self.tc("  CAST <spell> [target]  SPELLS", "help"))
        print(self.tc("  BLAST  HEAL  SPEED  POWER  (shortcut — no CAST needed)", "help"))
        print()
        print(self.tc("Status", "sys"))
        print(self.tc("  HEALTH  REST  CHAR (character sheet)", "help"))
        print()
        print(self.tc("Game", "sys"))
        print(self.tc("  SAVE  LOAD / RESTORE  QUIT  HELP", "help"))
        print()

    def cmd_quit(self) -> int:
        """Quit without confirmation."""
        return 0

    def cmd_quit_with_confirm(self) -> int:
        """Quit with confirmation."""
        from core.input_validator import prompt_bool
        if prompt_bool("Really quit?", default=False):
            return 0
        return -1


# ── Game Runner ───────────────────────────────────────────────────────────────

def run_adventure(character, adventure_path: str, save_data: dict = None) -> int:
    """
    Run an adventure with the given character.
    save_data: if provided, resume from that save instead of starting fresh.
    Returns: 0=quit, 1=won, 2=died
    """
    world = World.load(adventure_path)
    engine = Engine(world, character, adventure_path=adventure_path)

    print()
    print(engine.tc(world.title, "title"))
    print(engine.tc(f"by {world.author}", "sys"))
    print(engine.tc("─" * 72, "exits"))

    if save_data:
        # Resume — skip intro, restore saved state, show current room
        engine._apply_save_data(save_data)
        print(engine.tc("(Resumed from save)", "sys"))
    else:
        # Fresh start — show intro
        if world.intro:
            print(engine.tc(wrap(world.intro), "intro"))

    print()

    # Initial look
    engine.look()
    
    # Main game loop
    while True:
        try:
            raw_input = input(engine.tc("[Adventure] > ", "sys")).strip()
        except KeyboardInterrupt:
            print()
            print(engine.tc("(Interrupted)", "sys"))
            result = engine.cmd_quit_with_confirm()
            if result == 0:
                return 0
            continue
        except EOFError:
            return 0
        
        if not raw_input:
            continue
        
        result = engine.handle(raw_input)
        
        if result == 1:
            # Won!
            print()
            print(engine.tc("★ " * 36, "win"))
            print(engine.tc(world.win_condition.get("message", "You have won!"), "win"))
            print(engine.tc("★ " * 36, "win"))
            print()

            # Adventure-specific win bonus (e.g. Cynthia rescue gold)
            engine.call_hook("on_adventure_win")

            # Sync all player state back to character
            _sync_player_to_character(character, engine.player, engine.world)
            character.save()
            _save_carried_items(character, engine.world)
            return 1
        elif result == 2:
            # Died!
            print()
            print(engine.tc("╔" + "═" * 70 + "╗", "die"))
            print(engine.tc("║" + " " * 70 + "║", "die"))
            print(engine.tc("║" + "YOU HAVE DIED".center(70) + "║", "die"))
            print(engine.tc("║" + " " * 70 + "║", "die"))
            print(engine.tc("╚" + "═" * 70 + "╝", "die"))
            print()
            _sync_player_to_character(character, engine.player, engine.world)
            character.hp = max(0, engine.player.hp)  # clamp overkill damage
            character.save()
            _save_carried_items(character, engine.world)
            return 2
        elif result == 3:
            # Escaped to tavern mid-adventure
            _sync_player_to_character(character, engine.player, engine.world)
            character.save()
            _save_carried_items(character, engine.world)
            return 3
        elif result == 0:
            # Quit confirmed - ask to save
            response = input(engine.tc("Save progress? (y/n): ", "warn"))
            if response.lower() == 'y':
                _sync_player_to_character(character, engine.player, engine.world)
                character.save()
                _save_carried_items(character, engine.world)
                print(engine.tc("Progress saved.", "sys"))
            return 0
        elif result == -1:    # Don't quit - continue playing
            continue

if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) < 2:
        print(c(C.ERROR, "Usage: python3 engine.py <adventure_path>  (test mode)"))
        _sys.exit(1)
    _adv_path = _sys.argv[1]
    # Build a disposable test character with average stats
    from character import Character as _Char
    _test_char = _Char(
        name="Test Hero", strength=12, dex=12, con=12,
        intelligence=12, wis=12, charisma=12,
        hp=24, gold=500,
    )
    print(c(C.SYS, "[TEST MODE — disposable character, progress not saved]"))
    run_adventure(_test_char, _adv_path)
