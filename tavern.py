"""
tavern.py - The Saunter Inn and Tavern.

Entry point for the whole game system. Handles character creation/selection,
adventure launching, and the tavern as a navigable space with rooms, NPCs,
and character management commands.
"""

from __future__ import annotations

import os
import sys
import subprocess
import json
import time
from dataclasses import dataclass
from typing import Optional

# ── Colors ────────────────────────────────────────────────────────────────────

_TAVERN_COLORS = {
    "title"  : "\033[1;33m", # bold yellow
    "border" : "\033[2;33m", # dim yellow
    "stat"   : "\033[0;37m", # white
    "sys"    : "\033[0;36m", # cyan
    "error"  : "\033[0;31m", # red
    "warn"   : "\033[0;33m", # yellow
    "prompt" : "\033[1;37m", # bold white
    "npc"    : "\033[0;35m", # magenta
    "desc"   : "\033[2;37m", # dim white
    "reset"  : "\033[0m",
}

def tc(text: str, role: str) -> str:
    color = _TAVERN_COLORS.get(role, "")
    return f"{color}{text}{_TAVERN_COLORS['reset']}"

def tinput(prompt_text: str) -> str:
    return input(tc(prompt_text, "prompt")).strip()

def tprint(text: str, role: str = "desc") -> None:
    print(tc(text, role))

# ── Tavern rooms ──────────────────────────────────────────────────────────────

@dataclass
class TavernRoom:
    room_id: str
    name: str
    description: str
    exits: dict[str, str]
    npc: Optional[str] = None

TAVERN_ROOMS = {
    "entrance": TavernRoom(
        room_id="entrance",
        name="Tavern Entrance",
        description=(
            " You stand in the grand foyer of the Saunter Inn, a sturdy wooden\n"
            " structure with a low ceiling and a warm hearth. The smell of ale\n"
            " and woodsmoke hangs in the air. Patrons of all sorts mill about.\n"
        ),
        exits={"north": "bar", "east": "guild_hall"},
        npc=None,
    ),
    "bar": TavernRoom(
        room_id="bar",
        name="The Tavern Bar",
        description=(
            " The bar is busy with patrons nursing drinks and swapping stories.\n"
            " A stout man with a weathered face stands behind the bar, polishing\n"
            " glasses. This is Horace, the keeper of this place and the guild's\n"
            " unofficial quartermaster.\n"
        ),
        exits={"south": "entrance", "east": "backroom"},
        npc="horace",
    ),
    "backroom": TavernRoom(
        room_id="backroom",
        name="The Back Room",
        description=(
            " Shelves line the walls, stocked with potions, scrolls, weapons,\n"
            " and mysterious artifacts. A thin man with ink-stained fingers\n"
            " sits at a cluttered desk, poring over a massive tome. This must\n"
            " be Aldric, the wizard who trades in magical goods.\n"
        ),
        exits={"west": "bar"},
        npc="aldric",
    ),
    "guild_hall": TavernRoom(
        room_id="guild_hall",
        name="The Adventurers' Guild Hall",
        description=(
            " This is the heart of the Guild of Free Adventurers. A large\n"
            " bulletin board dominates the far wall, covered with notices,\n"
            " contracts, and tales of legendary deeds. Maps and weapons\n"
            " decorate the rest of the room.\n"
        ),
        exits={"west": "entrance"},
        npc=None,
    ),
}

# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║ ███████╗ █████╗ ███╗ ███╗ ██████╗ ███╗ ██╗                          ║
║ ██╔════╝ ██╔══██╗ ████╗ ████║ ██╔═══██╗ ████╗ ██║                  ║
║ █████╗ ███████║ ██╔████╔██║ ██║ ██║ ██╔██╗ ██║                  ║
║ ██╔══╝ ██╔══██║ ██║╚██╔╝██║ ██║ ██║ ██║╚██╗██║                  ║
║ ███████╗ ██║ ██║ ██║ ╚═╝ ██║ ╚██████╔╝ ██║ ╚████║                 ║
║ ╚══════╝ ╚═╝ ╚═╝ ╚═╝ ╚═╝ ╚═════╝ ╚═╝ ╚═══╝                 ║
║                                                                      ║
║ R E D U X  A D V E N T U R E  E N G I N E                           ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║ ~ Saunter Inn and Tavern ~                                          ║
║ Where adventurers gather between quests                             ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ── Item management ───────────────────────────────────────────────────────────

TYPE_VALUE_FLOOR = {
    "weapon": 10, "armor": 15, "shield": 10, "ring": 20, "cloak": 15,
    "potion": 5,  "food": 2,   "readable": 3, "generic": 1, "light": 3,
    "spellbook": 25,
}
UNSELLABLE_TYPES = {"key"}

def sell_value(artifact) -> int:
    if artifact.is_quest_item:
        return 0
    if artifact.artifact_type in UNSELLABLE_TYPES:
        return 0
    if artifact.value >= 0:
        return artifact.value
    return TYPE_VALUE_FLOOR.get(artifact.artifact_type, 1)

def can_sell(artifact) -> bool:
    return sell_value(artifact) > 0

# ── Save game management ──────────────────────────────────────────────────────

SAVE_DIR = "stored_games"

def list_saves(character_name: str = "") -> list[dict]:
    """
    Return save-file metadata sorted by modification time (newest first).
    If character_name given, filter to that character only.
    """
    if not os.path.isdir(SAVE_DIR):
        return []
    saves = []
    for fname in sorted(os.listdir(SAVE_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(SAVE_DIR, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            mtime = os.path.getmtime(path)
            saves.append({
                "name":      data.get("save_name", fname[:-5]),
                "path":      path,
                "char_name": data.get("player", {}).get("name", "?"),
                "adv_path":  data.get("adv_path", ""),
                "adv_title": _adv_title(data.get("adv_path", "")),
                "mtime_str": time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime)),
                "mtime":     mtime,
            })
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    if character_name:
        saves = [s for s in saves if s["char_name"] == character_name]
    saves.sort(key=lambda s: s["mtime"], reverse=True)
    return saves

def _adv_title(adv_path: str) -> str:
    meta = os.path.join(adv_path, "adventure.json")
    if not os.path.exists(meta):
        return adv_path or "?"
    try:
        with open(meta) as f:
            return json.load(f).get("title", adv_path)
    except Exception:
        return adv_path

def menu_load_save(character) -> bool:
    """
    List saved games for this character and offer to resume one.
    Returns True if a game was launched (so the caller can loop back).
    """
    saves = list_saves(character.name)
    if not saves:
        tprint("\n No saved games found for this character.", "warn")
        tinput(" Press Enter to continue...")
        return False

    print(tc("\n ─── Saved Games ────────────────────────────────────────", "border"))
    for i, s in enumerate(saves, 1):
        print(tc(f" {i}. ", "border") +
              tc(f"{s['name']:<22}", "title") +
              tc(f" {s['adv_title']:<22}", "desc") +
              tc(f" {s['mtime_str']}", "sys"))
    print(tc(" 0. Cancel", "border"))
    print()

    while True:
        raw = tinput(" Choose save: ").strip()
        try:
            n = int(raw)
            if n == 0:
                return False
            if 1 <= n <= len(saves):
                chosen = saves[n - 1]
                break
        except ValueError:
            pass
        tprint(" Invalid choice.", "error")

    tprint(f"\n Resuming '{chosen['name']}' — {chosen['adv_title']}...", "sys")

    result = subprocess.run([
        sys.executable, "engine.py",
        chosen["adv_path"],
        "--name",         character.name,
        "--class",        character.char_class,
        "--hardiness",    str(character.hardiness),
        "--agility",      str(character.agility),
        "--charisma",     str(character.charisma),
        "--intelligence", str(character.intelligence),
        "--strength",     str(character.strength),
        "--hp",           str(character.hp),
        "--mana",         str(character.mana),
        "--gold",         str(character.gold),
        "--spells",       ",".join(character.spells),
        "--xp",           str(character.xp),
        "--level",        str(character.level),
        "--savefile",     chosen["name"],
    ])

    _handle_engine_return(character, result, chosen["adv_path"])
    return True

# ── Room display & character commands ─────────────────────────────────────────

def show_room(room: TavernRoom) -> None:
    print()
    print(tc(f" ── {room.name} ──", "border"))
    print(tc(room.description, "desc"))
    if room.exits:
        dirs = ", ".join(d.upper() for d in sorted(room.exits.keys()))
        print(tc(f" Exits: {dirs}", "border"))
    print()

def show_character_sheet(character) -> None:
    from character import CharClass
    print()
    print(tc(" ┌────────────────────────────────────────────────┐", "border"))
    print(tc(f" │ {character.name:<{45}}│", "title"))
    print(tc(" ├────────────────────────────────────────────────┤", "border"))
    print(tc(f" │ Class:  {character.char_class:<{36}}│", "stat"))
    print(tc(f" │ Level:  {character.level}  (XP: {character.xp}){' '*28}│", "stat"))
    print(tc(f" │ Status: {'Veteran' if not character.is_beginner else 'Beginner':<{36}}│", "stat"))
    print(tc(" ├────────────────────────────────────────────────┤", "border"))
    print(tc(f" │ Hardiness:    {character.hardiness:<5} HP:  {character.hp:>3}/{character.hp_max:<3}{' '*14}│", "stat"))
    print(tc(f" │ Agility:      {character.agility:<5} (bonus: {character.agility_bonus:+d}){' '*18}│", "stat"))
    print(tc(f" │ Strength:     {character.strength:<5} (bonus: {character.strength_bonus:+d}){' '*18}│", "stat"))
    print(tc(f" │ Intelligence: {character.intelligence:<5} (bonus: {character.intelligence_bonus:+d}){' '*18}│", "stat"))
    print(tc(f" │ Charisma:     {character.charisma:<5} (bonus: {character.charisma_bonus:+d}){' '*18}│", "stat"))
    if character.char_class == CharClass.SORCERER:
        print(tc(f" │ Mana:  {character.mana}/{character.mana_max}{' '*37}│", "stat"))
    print(tc(f" │ Gold:  {character.gold}{' '*38}│", "sys"))
    print(tc(" └────────────────────────────────────────────────┘", "border"))
    print()

def show_inventory(character) -> None:
    shop_file = os.path.join("characters",
                             f"{character.name.lower().replace(' ','_')}_items.json")
    if not os.path.exists(shop_file):
        print(tc("\n You are not carrying anything.", "desc"))
        return
    with open(shop_file) as f:
        items_data = json.load(f)
    if not items_data:
        print(tc("\n You are not carrying anything.", "desc"))
        return
    from world import Artifact
    carried = [Artifact.from_dict(d) for d in items_data]
    print()
    print(tc(" ┌─── Your Inventory ────────────────────────────────┐", "border"))
    total_weight = 0
    for i, a in enumerate(carried, 1):
        total_weight += a.weight
        print(tc(f" │ {i:>2}. {a.name:<35} {a.weight:>4}g │", "stat"))
    cap = character.carry_capacity
    print(tc(f" │ {'─'*48}│", "border"))
    print(tc(f" │ Weight: {total_weight}/{cap} gronds{' '*(37 - len(str(total_weight)) - len(str(cap)))}│", "sys"))
    print(tc(" └───────────────────────────────────────────────────┘", "border"))
    print()

def show_spells(character) -> None:
    from character import CharClass, SPELL_DEFS
    print()
    if character.char_class != CharClass.SORCERER:
        print(tc(" You do not know any spells.", "warn"))
        return
    if not character.spells:
        print(tc(" You have not learned any spells yet.", "warn"))
        return
    print(tc(" ┌─── Known Spells ──────────────────────────────────┐", "border"))
    print(tc(f" │ Mana: {character.mana}/{character.mana_max}{' '*39}│", "sys"))
    print(tc(" ├───────────────────────────────────────────────────┤", "border"))
    for key in character.spells:
        if key in SPELL_DEFS:
            sp = SPELL_DEFS[key]
            print(tc(f" │ {sp['name']:<28} ({sp['cost']} mana){' '*12}│", "stat"))
            print(tc(f" │   {sp['desc']:<43}│", "desc"))
    print(tc(" └───────────────────────────────────────────────────┘", "border"))
    print()

# ── Tavern command handler ────────────────────────────────────────────────────

DIR_ABBREV_TAVERN = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "u": "up",    "d": "down",
}

def handle_tavern_command(cmd: str, character, room_id: str) -> Optional[str]:
    """
    Process one tavern command. Returns:
      - a room_id string to move to
      - "QUIT" to go to the adventure board
      - None to stay in current room
    """
    raw  = cmd.strip()
    cmd  = raw.upper()
    room = TAVERN_ROOMS[room_id]

    # ── Movement ─────────────────────────────────────────────────
    # Resolve abbreviations and full direction names
    direction = DIR_ABBREV_TAVERN.get(raw.lower(), raw.lower())
    if direction in room.exits:
        return room.exits[direction]
    if cmd.startswith("GO "):
        direction = DIR_ABBREV_TAVERN.get(cmd[3:].strip().lower(), cmd[3:].strip().lower())
        if direction in room.exits:
            return room.exits[direction]
        tprint(" You can't go that way.", "error")
        return None

    # ── "TALK TO <npc>" ───────────────────────────────────────────
    talk_target = ""
    if cmd.startswith("TALK TO "):
        talk_target = cmd[8:].strip()
    elif cmd.startswith("TALK "):
        talk_target = cmd[5:].strip()

    if talk_target:
        if talk_target in ("HORACE",) or (room.npc == "horace" and not talk_target):
            if room.npc == "horace":
                run_horace_shop(character)
            else:
                tprint(" Horace is at the bar. Head north from the entrance.", "desc")
            return None
        if talk_target in ("ALDRIC", "WIZARD") or (room.npc == "aldric" and not talk_target):
            if room.npc == "aldric":
                run_wizard_shop(character)
            else:
                tprint(" Aldric is in the back room. Go to the bar, then east.", "desc")
            return None
        tprint(f" There is no one called '{talk_target.lower()}' here.", "error")
        return None

    # ── Character info ────────────────────────────────────────────
    if cmd in ("CHARACTER", "CHAR", "C", "STATUS", "SHEET"):
        show_character_sheet(character)
        return None
    if cmd in ("INVENTORY", "I", "INV"):
        show_inventory(character)
        return None
    if cmd in ("SPELLS", "SPELL"):
        show_spells(character)
        return None

    # ── NPC interactions (direct keywords) ───────────────────────
    if cmd in ("HORACE", "SHOP", "BUY", "SELL"):
        if room.npc == "horace":
            run_horace_shop(character)
        else:
            tprint(" Horace is at the bar. Head north from the entrance.", "desc")
        return None
    if cmd in ("ALDRIC", "WIZARD", "MAGIC", "POTIONS"):
        if room.npc == "aldric":
            run_wizard_shop(character)
        else:
            tprint(" Aldric is in the back room. Go to the bar, then east.", "desc")
        return None

    # ── Save management ───────────────────────────────────────────
    if cmd in ("RESUME", "LOAD", "SAVES"):
        menu_load_save(character)
        return None

    # ── Meta ──────────────────────────────────────────────────────
    if cmd in ("LOOK", "L"):
        show_room(room)
        return None
    if cmd in ("HELP", "H", "?"):
        show_tavern_help()
        return None
    if cmd in ("QUIT", "Q", "EXIT", "LEAVE", "ADVENTURE", "BOARD"):
        return "QUIT"

    tprint(" You don't understand that. (Type HELP for commands)", "error")
    return None

def show_tavern_help() -> None:
    print()
    print(tc(" ─── Tavern Commands ──────────────────────────────────", "border"))
    print(tc(" NORTH/SOUTH/EAST/WEST (N/S/E/W) — Move between rooms", "desc"))
    print(tc(" GO <direction>                  — Move explicitly", "desc"))
    print(tc(" CHARACTER, CHAR, C, STATUS      — View character sheet", "desc"))
    print(tc(" INVENTORY, I                    — View carried items", "desc"))
    print(tc(" SPELLS                          — View known spells", "desc"))
    print(tc(" LOOK, L                         — Describe current room", "desc"))
    print(tc(" HORACE, SHOP                    — Trade with Horace (bar)", "desc"))
    print(tc(" ALDRIC, WIZARD                  — Visit Aldric (back room)", "desc"))
    print(tc(" RESUME, LOAD, SAVES             — Resume a saved adventure", "desc"))
    print(tc(" QUIT, Q, EXIT                   — Go to adventure board", "desc"))
    print(tc(" HELP, H, ?                      — This message", "desc"))
    print()

# ── Tavern exploration loop ───────────────────────────────────────────────────

def run_tavern_exploration(character) -> bool:
    """
    Walk around the tavern until the player QUITs to the adventure board.
    Returns True (always — QUIT means go to board, not exit the game).
    """
    current_room = "entrance"
    show_room(TAVERN_ROOMS[current_room])
    tprint(" Type HELP for commands, QUIT to go to the adventure board.", "sys")

    while True:
        raw = tinput(f" [{TAVERN_ROOMS[current_room].name}] > ")
        result = handle_tavern_command(raw, character, current_room)
        if result == "QUIT":
            return True
        elif result is not None:
            current_room = result
            show_room(TAVERN_ROOMS[current_room])

# ── Shops ─────────────────────────────────────────────────────────────────────

def run_horace_shop(character) -> None:
    tprint("\n " + tc("─── Horace's Outfitters ──────────────────────────", "border"), "desc")
    print(tc(' Horace says: "What can I do for you today?"', "npc"))
    print()
    print(tc(" 1. Sell items", "desc"))
    print(tc(" 0. Leave", "desc"))
    print()
    if tinput(" > ").strip() == "1":
        run_sell_items(character)

def run_sell_items(character) -> None:
    shop_file = os.path.join("characters",
                             f"{character.name.lower().replace(' ','_')}_items.json")
    if not os.path.exists(shop_file):
        tprint(" You don't have anything to sell.", "warn")
        return
    with open(shop_file) as f:
        items_data = json.load(f)
    from world import Artifact
    carried  = [Artifact.from_dict(d) for d in items_data]
    sellable = [a for a in carried if can_sell(a)]
    if not sellable:
        tprint(" Nothing you're carrying is worth coin to me.", "warn")
        return
    print()
    print(tc(" ─── Items for Sale ───────────────────────────────", "border"))
    for i, a in enumerate(sellable, 1):
        print(tc(f" {i:>2}. {a.name:<32} {sell_value(a):>4}g", "stat"))
    print()
    print(tc(" S <number> — sell one   SELL ALL — sell all   DONE — leave", "desc"))
    print()
    while True:
        raw = tinput(" > ").strip().lower()
        if raw in ("done", "0"):
            break
        if raw == "sell all":
            total = sum(sell_value(a) for a in sellable)
            if tinput(f" Sell all {len(sellable)} items for {total}g? (y/n): ").lower() == "y":
                character.gold += total
                tprint(f" Sold for {total}g. Gold: {character.gold}", "sys")
                with open(shop_file, "w") as f:
                    json.dump([], f)
                character.save()
                break
        elif raw.startswith("s "):
            try:
                idx = int(raw[2:]) - 1
                if 0 <= idx < len(sellable):
                    item  = sellable[idx]
                    price = sell_value(item)
                    if tinput(f" Sell {item.name} for {price}g? (y/n): ").lower() == "y":
                        character.gold += price
                        sellable.pop(idx)
                        remaining = [a for a in carried if a.id != item.id]
                        with open(shop_file, "w") as f:
                            json.dump([a.to_dict() for a in remaining], f, indent=2)
                        character.save()
                        tprint(f" Sold for {price}g. Gold: {character.gold}", "sys")
                else:
                    tprint(" Invalid number.", "error")
            except ValueError:
                tprint(" Enter S <number>.", "error")

def run_wizard_shop(character) -> None:
    tprint("\n " + tc("─── Aldric's Arcane Emporium ─────────────────────", "border"), "desc")
    print(tc(' Aldric says: "Knowledge has a price. So does everything else."', "npc"))
    print()
    print(tc(" 1. Learn a spell", "desc"))
    print(tc(" 0. Leave", "desc"))
    print()
    if tinput(" > ").strip() == "1":
        _learn_spell(character)

def _learn_spell(character) -> None:
    from character import CharClass, SPELL_DEFS
    if character.char_class != CharClass.SORCERER:
        tprint(" Only Sorcerers can learn spells.", "error")
        return
    available = [k for k in SPELL_DEFS if k not in character.spells]
    if not available:
        tprint(" You already know all available spells.", "sys")
        return
    print()
    print(tc(" ─── Available Spells ──────────────────────────────", "border"))
    for i, key in enumerate(available, 1):
        sp = SPELL_DEFS[key]
        print(tc(f" {i}. {sp['name']:<20} 50g — {sp['desc']}", "desc"))
    print()
    raw = tinput(" Choose spell (number): ").strip()
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(available):
            key   = available[idx]
            spell = SPELL_DEFS[key]
            if character.gold < 50:
                tprint(f" You need 50g. You have {character.gold}g.", "error")
                return
            if tinput(f" Learn {spell['name']} for 50g? (y/n): ").lower() == "y":
                character.gold  -= 50
                character.spells.append(key)
                character.save()
                tprint(f" You have learned {spell['name']}!", "sys")
    except ValueError:
        tprint(" Enter a number.", "error")

# ── Character management ──────────────────────────────────────────────────────

def menu_characters():
    from character import Character
    while True:
        names = Character.list_all()
        print(tc("\n ─── The Adventurers' Guild ──────────────────────────", "border"))
        if names:
            for i, name in enumerate(names, 1):
                ch     = Character.load(name)
                status = "Beginner" if ch.is_beginner else "Veteran"
                print(tc(f" {i}. {ch.name:<20}", "title") +
                      tc(f" H:{ch.hardiness} A:{ch.agility} ", "stat") +
                      tc(status, "desc"))
        else:
            tprint(" No characters yet.", "desc")
        print(tc("\n N. New character", "sys"))
        if names:
            print(tc(" V. View character sheet", "stat"))
            print(tc(" D. Delete character", "error"))
        print(tc(" 0. Quit", "border"))
        print()
        choice = tinput(" > ").strip().lower()
        if choice == "0":
            return None
        elif choice == "n":
            return Character.create_interactive()
        elif choice == "v" and names:
            try:
                idx = int(tinput(" Character number: ")) - 1
                if 0 <= idx < len(names):
                    show_character_sheet(Character.load(names[idx]))
                    tinput(" Press Enter to continue...")
            except ValueError:
                pass
        elif choice == "d" and names:
            try:
                idx = int(tinput(" Character number to delete: ")) - 1
                if 0 <= idx < len(names):
                    name = names[idx]
                    if tinput(f" Delete {name}? (yes/no): ").lower() == "yes":
                        Character.delete(name)
                        tprint(f" {name} deleted.", "sys")
            except ValueError:
                pass
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(names):
                    return Character.load(names[idx])
            except (ValueError, IndexError):
                pass

# ── Adventure discovery ───────────────────────────────────────────────────────

def find_adventures(adventures_dir: str = "adventures") -> list[dict]:
    adventures = []
    if not os.path.isdir(adventures_dir):
        return adventures
    for entry in sorted(os.listdir(adventures_dir)):
        adv_path  = os.path.join(adventures_dir, entry)
        meta_path = os.path.join(adv_path, "adventure.json")
        if os.path.isdir(adv_path) and os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            adventures.append({
                "name":       entry,
                "path":       adv_path,
                "title":      meta.get("title", entry),
                "author":     meta.get("author", "Unknown"),
                "is_beginner":meta.get("is_beginner_adventure", False),
            })
    return adventures

def choose_adventure(character, adventures: list[dict]):
    if character.is_beginner:
        available = [a for a in adventures if a["is_beginner"]]
        if not available:
            available = [a for a in adventures if a["name"] == "sample"]
        if not available:
            tprint(" No beginner adventure found.", "error")
            return None
        tprint("\n As a new adventurer, you are directed to:", "desc")
        return available[0]

    print(tc("\n ─── Available Adventures ────────────────────────────", "border"))
    for i, adv in enumerate(adventures, 1):
        done   = tc(" [completed]", "sys") if adv["name"] in character.adventures_completed else ""
        print(tc(f" {i}.", "border") + tc(f" {adv['title']}", "title") + done)
    print(tc(" R. Resume a saved game", "sys"))
    print(tc(" 0. Return to tavern", "border"))
    print()

    while True:
        raw = tinput(" Choose: ").strip().lower()
        if raw == "0":
            return None
        if raw == "r":
            menu_load_save(character)
            return None   # redisplay board via loop
        try:
            n = int(raw)
            if 1 <= n <= len(adventures):
                return adventures[n - 1]
        except ValueError:
            pass
        tprint(" Invalid choice.", "error")

# ── Engine launch helpers ─────────────────────────────────────────────────────

def _launch_engine(character, adv_path: str, savefile: str = "") -> "subprocess.CompletedProcess":
    cmd = [
        sys.executable, "engine.py", adv_path,
        "--name",         character.name,
        "--class",        character.char_class,
        "--hardiness",    str(character.hardiness),
        "--agility",      str(character.agility),
        "--charisma",     str(character.charisma),
        "--intelligence", str(character.intelligence),
        "--strength",     str(character.strength),
        "--hp",           str(character.hp),
        "--mana",         str(character.mana),
        "--gold",         str(character.gold),
        "--spells",       ",".join(character.spells),
        "--xp",           str(character.xp),
        "--level",        str(character.level),
    ]
    if savefile:
        cmd += ["--savefile", savefile]
    return subprocess.run(cmd)

def _handle_engine_return(character, result, adv_path: str,
                          adv_name: str = "", is_beginner_adv: bool = False) -> None:
    completed = (result.returncode == 1)
    died      = (result.returncode == 2)
    crashed   = result.returncode not in (0, 1, 2)

    if crashed:
        tprint("\n Something went wrong during that adventure.", "error")
        tprint(" Your character has not been affected.", "warn")
    elif died:
        missing = character.hp_max - 1
        cost    = min(missing * 2, character.gold)
        character.gold -= cost
        character.hp    = character.hp_max
        tprint(f"\n You were revived. Revival cost: {cost}g", "warn")
        character.save()
    else:
        character.hp   = character.hp_max
        character.mana = character.mana_max
        if completed and adv_name and adv_name not in character.adventures_completed:
            character.adventures_completed.append(adv_name)
            if is_beginner_adv and character.is_beginner:
                character.is_beginner = False
                tprint("\n You are no longer a beginner.", "sys")
        character.save()

# ── Main tavern loop ──────────────────────────────────────────────────────────

def run_tavern() -> None:
    print(tc(BANNER, "title"))

    character = menu_characters()
    if character is None:
        tprint("\n Safe travels.\n", "desc")
        return

    while True:
        print()
        tprint(" Welcome to the Saunter Inn and Tavern.", "sys")

        run_tavern_exploration(character)   # always returns True (QUIT = go to board)

        adventures = find_adventures()
        if not adventures:
            tprint(" No adventures available.", "error")
            break

        adv = choose_adventure(character, adventures)
        if adv is None:
            # Player chose 0 (return to tavern) — loop back to exploration
            continue

        tprint(f"\n You set out for: {adv['title']}\n", "sys")
        result = _launch_engine(character, adv["path"])
        _handle_engine_return(character, result, adv["path"],
                              adv_name=adv["name"],
                              is_beginner_adv=adv["is_beginner"])

        again = tinput("\n Return to the adventure board? (y/n): ").lower()
        if again != "y":
            tprint("\n Until next time, adventurer.", "desc")
            break


if __name__ == "__main__":
    run_tavern()
