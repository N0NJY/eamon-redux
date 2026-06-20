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
import random
import time
from dataclasses import dataclass
from typing import Optional
from save_system import list_resumable_games, load_game as load_game_slotted
from command_parser import parse_command

# ── Colors ────────────────────────────────────────────────────────────────────

_TAVERN_COLORS = {
    "title"  : "\033[1;33m",   # bright yellow  — headers, banners
    "border" : "\033[0;33m",   # yellow         — box borders, dividers
    "stat"   : "\033[1;36m",   # bright cyan    — stats, item lists
    "sys"    : "\033[0;36m",   # cyan           — weight, gold, system info
    "error"  : "\033[1;31m",   # bright red     — errors
    "warn"   : "\033[0;33m",   # yellow         — warnings, hints
    "prompt" : "\033[1;37m",   # bright white   — input prompts
    "npc"    : "\033[1;35m",   # bright magenta — NPC dialogue
    "desc"   : "\033[0;32m",   # green          — room/area descriptions
    "reset"  : "\033[0m",
}

def tc(text: str, role: str) -> str:
    return f"{_TAVERN_COLORS.get(role, '')}{text}{_TAVERN_COLORS['reset']}"

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
    exits: dict
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
    ),
}

# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║ ███████╗  █████╗   ███╗ ███╗   ██████╗  ██╗    ██╗                   ║
║ ██╔════╝ ██╔══██╗ ████╗ ████║ ██╔═══██╗ ████╗  ██║                   ║
║ █████╗   ███████║ ██╔████╔██║ ██║   ██║ ██╔██╗ ██║                   ║
║ ██╔══╝   ██╔══██║ ██║╚██╔╝██║ ██║   ██║ ██║╚██╗██║                   ║
║ ███████╗ ██║  ██║ ██║ ╚═╝ ██║ ╚██████╔╝ ██║ ╚████║                   ║
║ ╚══════╝  ╚═╝ ╚═╝ ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═══╝                   ║
║                                                                      ║
║     R E D U X  A D V E N T U R E  E N G I N E                        ║
║                                                                      ║
║        (C) 2026, Rick Donaldson                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║        ~ Saunter Inn and Tavern ~                                    ║
║    Where adventurers gather between quests                           ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ── Item valuation ────────────────────────────────────────────────────────────

TYPE_VALUE_FLOOR = {
    "weapon": 10, "armor": 15, "shield": 10, "ring": 20, "cloak": 15,
    "potion": 5,  "food": 2,   "readable": 3, "generic": 1, "light": 3,
    "spellbook": 25,
}
UNSELLABLE_TYPES = {"key"}

# Populated after shop templates are defined; used as a fallback so items
# bought before sell values were added to templates can still be resold.
_SHOP_SELL_VALUES: dict = {}

def sell_value(artifact) -> int:
    if artifact.is_quest_item:
        return 0
    if artifact.artifact_type in UNSELLABLE_TYPES:
        return 0
    if artifact.value > 0:
        return artifact.value
    if artifact.value == 0:
        return _SHOP_SELL_VALUES.get(artifact.name, 0)
    return TYPE_VALUE_FLOOR.get(artifact.artifact_type, 1)

def can_sell(artifact) -> bool:
    return sell_value(artifact) > 0

# ── Shop data ─────────────────────────────────────────────────────────────────

# Spell pricing: BUG-10 fix — use actual spell keys (blast, heal, speed, power)
_SPELL_BASE_PRICE = {"blast": 100, "heal": 50, "speed": 200, "power": 25}
_SPELL_FIGHTER_OK = {"heal"}  # Fighters may only learn Heal

def _spell_price(spell_key: str, character) -> int:
    base  = _SPELL_BASE_PRICE.get(spell_key, 50)
    level = character.level
    for threshold, mult in ((2, 1), (4, 2), (6, 4), (8, 8)):
        if level <= threshold:
            base *= mult
            break
    else:
        base *= 16
    return base

HORACE_CORE = [
    {"name": "healing potion",       "artifact_type": "potion", "weight": 1, "heal_amount": 10, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 8,  "price": 25,  "desc": "Restores 10 HP"},
    {"name": "minor healing potion", "artifact_type": "potion", "weight": 1, "heal_amount": 5,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 4,  "price": 12,  "desc": "Restores 5 HP"},
    {"name": "ration",               "artifact_type": "food",   "weight": 1, "heal_amount": 4,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 2,  "price": 5,   "desc": "Restores 4 HP when eaten"},
    {"name": "dagger",               "artifact_type": "weapon", "weight": 1, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 5,  "price": 15,  "desc": "1d4 damage"},
    {"name": "short sword",          "artifact_type": "weapon", "weight": 2, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 10, "price": 30,  "desc": "1d6 damage"},
    {"name": "leather armor",        "artifact_type": "armor",  "weight": 3, "heal_amount": 0,  "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 13, "price": 40,  "desc": "AC +1"},
    {"name": "chainmail coat",       "artifact_type": "armor",  "weight": 6, "heal_amount": 0,  "armor_class": 3, "damage_dice": 1, "damage_sides": 4, "value": 30, "price": 100, "desc": "AC +3"},
    {"name": "wooden shield",        "artifact_type": "shield", "weight": 3, "heal_amount": 0,  "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 8,  "price": 25,  "desc": "AC +1 (shield slot)"},
]

HORACE_RANDOM_POOL = [
    {"name": "war axe",     "artifact_type": "weapon", "weight": 4, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 8, "value": 15, "price": 50,  "desc": "1d8 damage"},
    {"name": "iron mace",   "artifact_type": "weapon", "weight": 3, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 12, "price": 35,  "desc": "1d6 damage"},
    {"name": "scale armor", "artifact_type": "armor",  "weight": 8, "heal_amount": 0, "armor_class": 4, "damage_dice": 1, "damage_sides": 4, "value": 60, "price": 180, "desc": "AC +4"},
    {"name": "iron shield", "artifact_type": "shield", "weight": 4, "heal_amount": 0, "armor_class": 2, "damage_dice": 1, "damage_sides": 4, "value": 18, "price": 55,  "desc": "AC +2 (shield slot)"},
    {"name": "hunting bow", "artifact_type": "weapon", "weight": 2, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 15, "price": 45,  "desc": "1d6 damage"},
    {"name": "torch",       "artifact_type": "light",  "weight": 1, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 3,  "price": 8,   "desc": "A light source"},
]

WIZARD_RANDOM_POOL = [
    {"name": "greater healing potion", "artifact_type": "potion",   "weight": 1, "heal_amount": 20, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 20, "price": 60, "desc": "Restores 20 HP"},
    {"name": "mana potion",            "artifact_type": "potion",   "weight": 1, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 15, "price": 50, "desc": "Restores 10 mana"},
    {"name": "mystery scroll",         "artifact_type": "readable", "weight": 0, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 5,  "price": 20, "desc": "Faded writing. Hard to read."},
]

_SHOP_SELL_VALUES = {
    item["name"]: item["value"]
    for pool in (HORACE_CORE, HORACE_RANDOM_POOL, WIZARD_RANDOM_POOL)
    for item in pool
    if item["value"] > 0
}

MAX_POTIONS = 2

def _items_path(character) -> str:
    safe = character.name.lower().replace(" ", "_")
    return os.path.join("characters", f"{safe}_items.json")

def _load_carried(character) -> list:
    from world import Artifact
    path = _items_path(character)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [Artifact.from_dict(d) for d in json.load(f)]

def _save_carried(character, items: list) -> None:
    os.makedirs("characters", exist_ok=True)
    with open(_items_path(character), "w") as f:
        json.dump([a.to_dict() for a in items], f, indent=2)

def _count_potions(character) -> int:
    return sum(1 for a in _load_carried(character) if a.artifact_type == "potion")

def _make_artifact(template: dict, new_id: int):
    from world import Artifact
    return Artifact(
        id=new_id, name=template["name"],
        description=template.get("desc", template["name"]),
        room_id=None,
        artifact_type=template["artifact_type"],
        weight=template.get("weight", 1),
        heal_amount=template.get("heal_amount", 0),
        armor_class=template.get("armor_class", 0),
        damage_dice=template.get("damage_dice", 1),
        damage_sides=template.get("damage_sides", 4),
        value=template.get("value", -1),
        synonyms=[],
    )

def _add_to_inventory(character, template: dict) -> None:
    carried = _load_carried(character)
    new_id  = max((a.id for a in carried), default=100) + 1
    carried.append(_make_artifact(template, new_id))
    _save_carried(character, carried)

def _process_sell(raw: str, sellable: list, all_carried: list,
                  character, allowed_types: set) -> None:
    raw = raw.strip().lower()
    if raw == "sell all":
        total = sum(sell_value(a) for a in sellable)
        if tinput(f" Sell all {len(sellable)} item(s) for {total}g? (y/n): ").lower() != "y":
            return
        ids_to_sell = {id(a) for a in sellable}
    elif raw.startswith("s "):
        # Format: "S 1"
        try:
            idx = int(raw[2:]) - 1
            if not (0 <= idx < len(sellable)):
                tprint(" Invalid number.", "error"); return
            item  = sellable[idx]
            price = sell_value(item)
            if tinput(f" Sell {item.name} for {price}g? (y/n): ").lower() != "y":
                return
            ids_to_sell = {id(item)}
            total = price
        except ValueError:
            tprint(" Usage: S <number> or SELL ALL", "error"); return
    else:
        # Try plain number format: "1"
        try:
            idx = int(raw) - 1
            if not (0 <= idx < len(sellable)):
                tprint(" Invalid number.", "error"); return
            item  = sellable[idx]
            price = sell_value(item)
            if tinput(f" Sell {item.name} for {price}g? (y/n): ").lower() != "y":
                return
            ids_to_sell = {id(item)}
            total = price
        except ValueError:
            tprint(" Usage: S <number> or SELL ALL", "error"); return

    sold    = [a for a in sellable if id(a) in ids_to_sell]
    total   = sum(sell_value(a) for a in sold)
    remaining = [a for a in all_carried if id(a) not in ids_to_sell]
    _save_carried(character, remaining)
    character.gold += total
    character.save()
    tprint(f" Sold for {total}g. Gold: {character.gold}g", "sys")

# ── Save game management ──────────────────────────────────────────────────────

SAVE_DIR = "stored_games"

def _adv_title(adv_path: str) -> str:
    meta = os.path.join(adv_path, "adventure.json")
    if not os.path.exists(meta):
        return adv_path or "?"
    try:
        with open(meta) as f:
            return json.load(f).get("title", adv_path)
    except Exception:
        return adv_path

def list_saves(character) -> list:
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
            if data.get("player", {}).get("name") != character.name:
                continue
            mtime = os.path.getmtime(path)
            saves.append({
                "name":      data.get("save_name", fname[:-5]),
                "path":      path,
                "adv_path":  data.get("adv_path", ""),
                "adv_title": _adv_title(data.get("adv_path", "")),
                "mtime_str": time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime)),
                "mtime":     mtime,
            })
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    saves.sort(key=lambda s: s["mtime"], reverse=True)
    return saves

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
    """Display the character's complete stat sheet in bright yellow."""
    print(f"\033[1;33m{character.stat_summary()}\033[0m")

def show_inventory(character) -> None:
    carried = _load_carried(character)
    if not carried:
        tprint("\n You are not carrying anything.", "desc")
        return
    total_weight = sum(a.weight for a in carried)
    cap = character.carry_capacity
    equipped_names = set(character.equipped.values())
    INNER = 46  # chars between ` │ ` and `│`
    print()
    print(tc(" ┌─── Your Inventory ────────────────────────────────┐", "border"))
    for i, a in enumerate(carried, 1):
        sv = f" ({sell_value(a)}g)" if can_sell(a) else ""
        eq = " [EQUIPPED]" if a.name in equipped_names else ""
        right = f"{a.weight:>3}g{sv:<7}"          # 11 chars
        left  = f"{i:>2}. {a.name}{eq}"
        pad   = max(0, INNER - len(left) - len(right))
        inner = (left + " " * pad + right)[:INNER]  # plain string, exact width
        color = "title" if eq else "stat"
        print(tc(" │ ", "border") + tc(inner, color) + tc("│", "border"))
    print(tc(f" │ {'─'*INNER}│", "border"))
    wline = f" Weight: {total_weight}/{cap} gronds"
    print(tc(" │ ", "border") + tc(f"{wline:<{INNER}}", "sys") + tc("│", "border"))
    print(tc(" └───────────────────────────────────────────────────┘", "border"))
    print()

def show_spells(character) -> None:
    from character import SPELL_DEFS
    print()
    learned = {k: v for k, v in character.spell_proficiencies.items() if v is not None}
    if not learned:
        tprint(" You have not learned any spells yet.", "warn"); return
    print(tc(" ┌─── Known Spells ──────────────────────────────────┐", "border"))
    print(tc(" ├───────────────────────────────────────────────────┤", "border"))
    for key, prof in learned.items():
        if key in SPELL_DEFS:
            sp = SPELL_DEFS[key]
            print(tc(f" │  {sp['name']:<12} {prof:>3}%   {sp['desc']:<26}│", "stat"))
    print(tc(" └───────────────────────────────────────────────────┘", "border"))
    print()

def show_equipment(character) -> None:
    """Display equipped items and allow unequipping in the tavern."""
    print()
    print(tc(" ┌─── Equipment ──────────────────────────────────────┐", "border"))
    active = {s: n for s, n in character.equipped.items() if n}
    if not active:
        print(tc(" │  (nothing equipped)                                │", "stat"))
        print(tc(" └───────────────────────────────────────────────────┘", "border"))
        print()
        return
    slots = list(active.keys())
    for i, slot in enumerate(slots, 1):
        name = active[slot]
        print(tc(f" │ {i:>2}. {slot.upper():<10} {name:<32}│", "stat"))
    print(tc(f" │ {'─'*48}│", "border"))
    print(tc(f" │  Enter # to unequip, or 0 to cancel               │", "desc"))
    print(tc(" └───────────────────────────────────────────────────┘", "border"))
    print()
    choice = tinput(" > ").strip()
    if not choice or choice == "0":
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(slots):
            slot = slots[idx]
            name = active[slot]
            del character.equipped[slot]
            character.save()
            tprint(f" {name} unequipped.", "desc")
        else:
            tprint(" Invalid choice.", "error")
    except ValueError:
        tprint(" Invalid input.", "error")


_EQUIP_SLOT = {"weapon": "weapon", "armor": "armor",
               "shield": "shield", "ring":   "ring", "cloak": "cloak"}

def cmd_equip_tavern(noun: str, character) -> None:
    """Equip a carried item in the tavern (no combat context needed)."""
    carried    = _load_carried(character)
    equippable = [a for a in carried if a.artifact_type in _EQUIP_SLOT]
    if not equippable:
        tprint(" You have nothing that can be equipped.", "warn")
        return

    equipped_names = set(character.equipped.values())

    target = None
    if noun:
        for a in equippable:
            if noun.lower() in a.name.lower():
                target = a
                break
        if not target:
            tprint(f" You're not carrying anything called '{noun}'.", "error")
            return
    else:
        print()
        print(tc(" ─── Equippable Items ────────────────────────────────", "border"))
        for i, a in enumerate(equippable, 1):
            slot   = _EQUIP_SLOT[a.artifact_type]
            eq_tag = " [EQUIPPED]" if a.name in equipped_names else ""
            color  = "title" if eq_tag else "stat"
            print(tc(f" {i:>3}. ", "border") +
                  tc(f"{a.name:<28}", color) +
                  tc(f"{slot:<8}", "desc") +
                  tc(eq_tag, "title"))
        print()
        raw = tinput(" Equip #  (0 to cancel): ").strip()
        if not raw or raw == "0":
            return
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(equippable):
                target = equippable[idx]
            else:
                tprint(" Invalid number.", "error"); return
        except ValueError:
            tprint(" Invalid input.", "error"); return

    slot = _EQUIP_SLOT[target.artifact_type]

    # Refuse to swap out a cursed item
    current_name = character.equipped.get(slot)
    if current_name:
        current = next((a for a in carried if a.name == current_name), None)
        if current and current.flags.get("cursed"):
            tprint(f" The {current_name} is cursed — it cannot be removed!", "error")
            return
        msg = f" You remove the {current_name} and equip the {target.name}."
    else:
        msg = f" You equip the {target.name}."

    character.equipped[slot] = target.name
    character.save()
    tprint(msg, "desc")


# ── Shops ─────────────────────────────────────────────────────────────────────

def run_horace_shop(character) -> None:
    random.seed(len(character.adventures_completed) * 7 + character.level)
    extras = random.sample(HORACE_RANDOM_POOL, min(3, len(HORACE_RANDOM_POOL)))
    random.seed()
    stock = HORACE_CORE + extras

    while True:
        show_inventory(character)
        tprint("\n " + tc("─── Horace's Outfitters ──────────────────────────", "border"), "desc")
        print(tc(' Horace says: "Buy, sell, or just browse. Gold talks."', "npc"))
        print()
        for i, item in enumerate(stock, 1):
            print(tc(f" {i:>3}. ", "border") +
                  tc(f"{item['name']:<28}", "title") +
                  tc(f" {item['price']:>4}g  ", "sys") +
                  tc(item.get("desc", ""), "desc"))
        print()
        print(tc(f" Gold: {character.gold}g", "stat"))
        print(tc(" B <n> — buy   S <n> / SELL ALL — sell gear   DONE — leave", "desc"))
        print()

        raw = tinput(" > ").strip().lower()

        if raw in ("done", "leave", "0", "d"):
            break

        elif raw == "s" or raw.startswith("sell"):
            carried        = _load_carried(character)
            equipped_names = set(character.equipped.values())
            horace_types   = {"weapon","armor","shield","ring","cloak","generic","light"}
            eligible       = [a for a in carried if can_sell(a) and a.artifact_type in horace_types]
            sellable       = [a for a in eligible if a.name not in equipped_names]
            if not eligible:
                tprint(" Nothing here I'd buy. Try Aldric for magical items.", "warn")
                continue
            print(tc(" ── Items Horace will buy ───────────────────────────", "border"))
            n = 0
            for a in eligible:
                is_eq = a.name in equipped_names
                if is_eq:
                    print(tc(f"      ", "border") +
                          tc(f"{a.name:<30}", "title") +
                          tc(f" {sell_value(a):>4}g", "sys") +
                          tc(" [EQUIPPED — unequip first]", "warn"))
                else:
                    n += 1
                    print(tc(f" {n:>3}. ", "border") +
                          tc(f"{a.name:<30}", "title") +
                          tc(f" {sell_value(a):>4}g", "sys"))
            if not sellable:
                tprint(" All sellable items are equipped. Use EQUIPMENT to unequip.", "warn")
                continue
            sell_raw = tinput(" S <n> or SELL ALL: ").strip().lower()
            _process_sell(sell_raw, sellable, carried, character,
                          horace_types)

        elif raw.startswith("b "):
            try:
                idx = int(raw[2:]) - 1
                if not (0 <= idx < len(stock)):
                    tprint(" Invalid number.", "error"); continue
                item  = stock[idx]
                price = item["price"]
                if item["artifact_type"] == "potion" and _count_potions(character) >= MAX_POTIONS:
                    tprint(f" You can only carry {MAX_POTIONS} potions.", "error"); continue
                if character.gold < price:
                    tprint(f" Not enough gold. (Need {price}g, have {character.gold}g)", "error"); continue
                if tinput(f" Buy {item['name']} for {price}g? (y/n): ").lower() == "y":
                    character.gold -= price
                    _add_to_inventory(character, item)
                    character.save()
                    tprint(f" Purchased. Gold: {character.gold}g", "sys")
            except ValueError:
                tprint(" Enter B followed by a number.", "error")

        else:
            tprint(" B <n> to buy, S to sell, or DONE.", "warn")


def run_wizard_shop(character) -> None:
    from character import SPELL_DEFS

    random.seed(len(character.adventures_completed) * 13 + character.level)
    extras = random.sample(WIZARD_RANDOM_POOL, min(2, len(WIZARD_RANDOM_POOL)))
    random.seed()

    while True:
        show_inventory(character)
        tprint("\n " + tc("─── Aldric's Arcane Emporium ─────────────────────", "border"), "desc")
        print(tc(' Aldric says: "Knowledge has a price. So does everything else."', "npc"))
        print()

        # All characters may learn any spell
        available_spells = [
            (k, v) for k, v in SPELL_DEFS.items()
            if character.spell_proficiencies.get(k) is None
        ]

        print(tc(" ── Spells ────────────────────────────────────────", "border"))
        if available_spells:
            for i, (key, spell) in enumerate(available_spells, 1):
                price = _spell_price(key, character)
                mark  = "✦" if character.gold >= price else "✗"
                print(tc(f" {i:>3}. ", "border") +
                      tc(f"{spell['name']:<15}", "title") +
                      tc(f" {price:>5}g  ", "sys") +
                      tc(spell["desc"], "desc") +
                      tc(f"  {mark}", "sys"))
        else:
            tprint(" You know all spells available to you.", "sys")

        item_offset = len(available_spells)
        print(tc("\n ── Magical Items ─────────────────────────────────", "border"))
        for i, item in enumerate(extras, item_offset + 1):
            limit = " [at limit]" if item["artifact_type"] == "potion" and _count_potions(character) >= MAX_POTIONS else ""
            print(tc(f" {i:>3}. ", "border") +
                  tc(f"{item['name']:<28}", "title") +
                  tc(f" {item['price']:>4}g  ", "sys") +
                  tc(item.get("desc", ""), "desc") +
                  tc(limit, "error"))

        print()
        print(tc(f" Gold: {character.gold}g  |  Level: {character.level}  |  XP: {character.xp}", "stat"))
        learned = [k for k, v in character.spell_proficiencies.items() if v is not None]
        print(tc(f" Known spells: {', '.join(learned) if learned else 'none'}", "desc"))
        print(tc(" B <n> — buy   S <n> / SELL ALL — sell magical items   DONE — leave", "desc"))
        print()

        raw = tinput(" > ").strip().lower()

        if raw in ("done", "leave", "0", "d"):
            break

        elif raw == "s" or raw.startswith("sell"):
            carried        = _load_carried(character)
            equipped_names = set(character.equipped.values())
            aldric_types   = {"potion","readable","spellbook"}
            eligible       = [a for a in carried if can_sell(a) and a.artifact_type in aldric_types]
            sellable       = [a for a in eligible if a.name not in equipped_names]
            if not eligible:
                tprint(" Nothing magical I'd buy. Try Horace for weapons.", "warn"); continue
            print(tc(" ── Items Aldric will buy ───────────────────────────", "border"))
            n = 0
            for a in eligible:
                is_eq = a.name in equipped_names
                if is_eq:
                    print(tc(f"      ", "border") +
                          tc(f"{a.name:<30}", "title") +
                          tc(f" {sell_value(a):>4}g", "sys") +
                          tc(" [EQUIPPED — unequip first]", "warn"))
                else:
                    n += 1
                    print(tc(f" {n:>3}. ", "border") +
                          tc(f"{a.name:<30}", "title") +
                          tc(f" {sell_value(a):>4}g", "sys"))
            if not sellable:
                tprint(" All sellable items are equipped. Use EQUIPMENT to unequip.", "warn")
                continue
            sell_raw = tinput(" S <n> or SELL ALL: ").strip().lower()
            _process_sell(sell_raw, sellable, carried, character,
                          aldric_types)

        elif raw.startswith("b "):
            try:
                idx = int(raw[2:]) - 1
                all_items = [(k, v, "spell") for k, v in available_spells] + \
                            [(i, i, "item")  for i in extras]
                if not (0 <= idx < len(all_items)):
                    tprint(" Invalid number.", "error"); continue
                key, val, kind = all_items[idx]

                if kind == "spell":
                    price = _spell_price(key, character)
                    if character.gold < price:
                        tprint(f" Not enough gold. (Need {price}g, have {character.gold}g)", "error"); continue
                    if tinput(f" Learn {val['name']} for {price}g? (y/n): ").lower() == "y":
                        character.gold -= price
                        character.spell_proficiencies[key] = random.randint(25, 75)
                        character.save()
                        tprint(f" You have learned {val['name']}! (starting proficiency: {character.spell_proficiencies[key]}%)", "sys")
                        print(tc(' Aldric says: "Use it wisely. Or don\'t. I don\'t care."', "npc"))
                else:
                    item  = val
                    price = item["price"]
                    if item["artifact_type"] == "potion" and _count_potions(character) >= MAX_POTIONS:
                        tprint(f" You can only carry {MAX_POTIONS} potions.", "error"); continue
                    if character.gold < price:
                        tprint(f" Not enough gold. (Need {price}g, have {character.gold}g)", "error"); continue
                    if tinput(f" Buy {item['name']} for {price}g? (y/n): ").lower() == "y":
                        character.gold -= price
                        _add_to_inventory(character, item)
                        character.save()
                        tprint(f" Purchased. Gold: {character.gold}g", "sys")
            except (ValueError, IndexError):
                tprint(" Enter B followed by a number.", "error")

        else:
            tprint(" B <n> to buy, S to sell, or DONE.", "warn")

# ── Tavern command handler ────────────────────────────────────────────────────

DIR_ABBREV = {"n":"north","s":"south","e":"east","w":"west","u":"up","d":"down"}

def handle_tavern_command(raw: str, character, room_id: str) -> Optional[str]:
    """Handle tavern commands with fuzzy matching. Returns new room_id, 'QUIT', or None."""
    room = TAVERN_ROOMS[room_id]
    
    # Parse command with fuzzy matching
    cmd, status, suggestions = parse_command(raw, "tavern")
    
    # Extract noun (everything after the first word)
    parts = raw.strip().lower().split()
    noun = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Handle special "talk to" syntax
    if len(parts) >= 3 and parts[0] == "talk" and parts[1] == "to":
        cmd = "talk"
        noun = " ".join(parts[2:])
    
    # ────────────────────────────────────────────────────────────────────────────
    # Handle parsing results
    # ────────────────────────────────────────────────────────────────────────────
    
    if status == "exact" or status == "partial":
        return _execute_tavern_command(cmd, noun, character, room)
    
    elif status == "ambiguous":
        tprint(f"\n Ambiguous command: '{parts[0].upper()}'", "error")
        tprint(f" Did you mean: {', '.join(s.upper() for s in suggestions)}?", "sys")
        tprint(f" Type HELP for a list of commands.\n", "sys")
        return None
    
    elif status == "not_found":
        tprint(f" You don't understand that. (Type HELP for commands)", "error")
        if suggestions:
            tprint(f" Did you mean: {', '.join(s.upper() for s in suggestions[:3])}?", "sys")
        return None
    
    return None


def _execute_tavern_command(cmd: str, noun: str, character, room) -> Optional[str]:
    """Execute a validated tavern command."""
    
    # ────────────────────────────────────────────────────────────────────────────
    # Movement
    # ────────────────────────────────────────────────────────────────────────────
    if cmd in ("north", "south", "east", "west"):
        if cmd in room.exits:
            return room.exits[cmd]
        else:
            tprint(" You can't go that way.", "error")
            return None
    
    if cmd == "go":
        if not noun:
            tprint(" Go where?", "error")
            return None
        direction = DIR_ABBREV.get(noun, noun)
        if direction in room.exits:
            return room.exits[direction]
        tprint(" You can't go that way.", "error")
        return None
    
    # ────────────────────────────────────────────────────────────────────────────
    # NPC Interaction
    # ────────────────────────────────────────────────────────────────────────────
    if cmd == "talk":
        if not noun:
            tprint(" Talk to whom?", "error")
            return None
        
        talk_target = noun.strip().lower()
        
        # Handle Horace
        if "horace" in talk_target or "shop" in talk_target:
            if room.npc == "horace":
                run_horace_shop(character)
            else:
                tprint(" Horace is at the bar. Head north from the entrance.", "desc")
            return None
        
        # Handle Aldric
        if "aldric" in talk_target or "wizard" in talk_target or "magic" in talk_target:
            if room.npc == "aldric":
                run_wizard_shop(character)
            else:
                tprint(" Aldric is in the back room. Bar, then east.", "desc")
            return None
        
        tprint(f" There is no one called '{noun}' here.", "error")
        return None
    
    # ────────────────────────────────────────────────────────────────────────────
    # Shop (direct command)
    # ────────────────────────────────────────────────────────────────────────────
    if cmd == "buy" or cmd == "sell":
        if room.npc == "horace":
            run_horace_shop(character)
        else:
            tprint(" Horace is at the bar. Head north from the entrance.", "desc")
        return None
    
    # ────────────────────────────────────────────────────────────────────────────
    # Character Management
    # ────────────────────────────────────────────────────────────────────────────
    if cmd == "character":
        show_character_sheet(character)
        return None
    
    if cmd == "inventory":
        show_inventory(character)
        return None
    
    if cmd == "spells":
        show_spells(character)
        return None

    if cmd == "equipment":
        show_equipment(character)
        return None

    if cmd == "equip":
        cmd_equip_tavern(noun, character)
        return None

    if cmd == "unequip":
        show_equipment(character)   # show_equipment already prompts to unequip by number
        return None

    # ────────────────────────────────────────────────────────────────────────────
    # Game Control
    # ────────────────────────────────────────────────────────────────────────────
    if cmd == "look":
        show_room(room)
        return None
    
    if cmd == "help":
        show_tavern_help()
        return None
    
    if cmd == "adventure":
        return "BOARD"

    if cmd == "resume":
        menu_load_save(character)
        return None

    if cmd == "quit":
        character.save()
        return "EXIT_GAME"
    
    # Should not reach here (parser already validated command)
    tprint(" You don't understand that. (Type HELP for commands)", "error")
    return None

def show_tavern_help() -> None:
    print()
    print(tc(" ─── Tavern Commands ──────────────────────────────────", "border"))
    cmds = [
        ("N/S/E/W",           "Move between rooms"),
        ("GO <direction>",    "Move explicitly"),
        ("CHARACTER / SHEET", "View character sheet"),
        ("INVENTORY / I",     "View carried items"),
        ("SPELLS",            "View known spells"),
        ("EQUIPMENT / EQ",    "View equipped items and unequip"),
        ("EQUIP <item>",      "Equip a carried weapon, armor, or accessory"),
        ("UNEQUIP",           "Unequip an item (same menu as EQUIPMENT)"),
        ("LOOK / L",          "Describe current room"),
        ("HORACE / SHOP",     "Trade with Horace (at the bar)"),
        ("ALDRIC / WIZARD",   "Visit Aldric (bar → east)"),
        ("TALK TO <name>",    "Speak to an NPC"),
        ("ADVENTURE / A",     "Go to the adventure board"),
        ("RESUME / SAVES",    "Resume a saved adventure"),
        ("QUIT / Q",          "Save and exit the game"),
        ("HELP / ?",          "This message"),
    ]
    for cmd, desc in cmds:
        print(tc(f" {cmd:<22}", "title") + tc(desc, "desc"))
    print()

# ✅ BUG 8 FIX: REMOVED first definition of menu_load_save (lines 323+)
# Only keeping the second, complete definition below:

def menu_load_save(character) -> None:
    """Browse and resume saved games by adventure."""
    from character import Character
    
    games = list_resumable_games(character.name)
    
    if not games:
        tprint("\n ❌ No saved games found.", "error")
        tinput(" Press Enter to continue...")
        return
    
    print(tc("\n ─── Saved Games ──────────────────────────────────", "border"))
    
    adv_list = sorted(games.keys())
    for i, adv_name in enumerate(adv_list, 1):
        saves = games[adv_name]
        print(tc(f" {i}. {adv_name} ({len(saves)} save(s))", "title"))
        for slot, filename, meta in saves:
            print(tc(f"    └─ Slot {slot}: {meta['room']} (HP: {meta['hp']}, {meta['timestamp'][:10]})", "desc"))
    
    print(tc(f"\n {len(adv_list) + 1}. Cancel", "border"))
    
    choice = tinput("\n Resume which adventure? (# or name): ").strip()
    
    if choice == str(len(adv_list) + 1) or choice.lower() == 'cancel':
        return
    
    adventure = None
    try:
        adv_idx = int(choice) - 1
        if 0 <= adv_idx < len(adv_list):
            adventure = adv_list[adv_idx]
    except ValueError:
        # Try matching by name substring
        for adv in adv_list:
            if choice.lower() in adv.lower():
                adventure = adv
                break
    
    if not adventure:
        tprint(" ❌ Adventure not found.", "error")
        return
    
    saves = games[adventure]
    
    # Prompt for slot if multiple saves
    if len(saves) == 1:
        slot = saves[0][0]
    else:
        slot_nums = ", ".join(str(s[0]) for s in saves)
        try:
            slot = int(tinput(f"\n Which save slot? ({slot_nums}): ").strip())
            if not any(s[0] == slot for s in saves):
                tprint(" ❌ Invalid slot.", "error")
                return
        except ValueError:
            tprint(" ❌ Invalid input.", "error")
            return
    
    # Load and launch adventure
    save_data = load_game_slotted(character.name, adventure, slot, interactive=False)
    if not save_data:
        tprint(" ❌ Load failed.", "error")
        return
    
    # Find adventure path
    adv_path = None
    adventures = find_adventures()
    
    # First try exact match
    for adv in adventures:
        if adv["name"] == adventure:
            adv_path = adv["path"]
            break
    
    # If not found, try substring match (case-insensitive)
    if not adv_path:
        for adv in adventures:
            if adventure.lower() in adv["name"].lower() or adv["name"].lower() in adventure.lower():
                adv_path = adv["path"]
                break
    
    if not adv_path:
        tprint(f" ❌ Adventure path not found for: {adventure}", "error")
        return
    
    # Launch engine with savefile
    safe_name = character.name.lower().replace(" ", "_")
    safe_adv = adventure.lower().replace(" ", "_")
    savefile = f"{safe_name}_{safe_adv}_slot{slot}"
    
    tprint(f"\n Resuming: {adventure}\n", "sys")
    result = _launch_engine(character, adv_path, savefile)  # ✅ Now savefile is used!
    _handle_engine_return(character, result, adv_path,
                          adv_name=adventure,
                          is_beginner_adv=False)

def run_tavern_exploration(character) -> str:
    """Walk the tavern. Returns 'BOARD' to go to adventure board, 'EXIT_GAME' to quit."""
    current_room = "entrance"
    show_room(TAVERN_ROOMS[current_room])
    tprint(" Type HELP for commands, ADVENTURE for the board, QUIT to exit.", "sys")
    while True:
        raw    = tinput(f" [{TAVERN_ROOMS[current_room].name}] > ")
        result = handle_tavern_command(raw, character, current_room)
        if result in ("BOARD", "EXIT_GAME"):
            return result
        elif result is not None:
            current_room = result
            show_room(TAVERN_ROOMS[current_room])

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

def find_adventures(adventures_dir: str = "adventures") -> list:
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
                "name":        entry,
                "path":        adv_path,
                "title":       meta.get("title", entry),
                "author":      meta.get("author", "Unknown"),
                "is_beginner": meta.get("is_beginner_adventure", False),
            })
    return adventures

def choose_adventure(character, adventures: list):
    if character.is_beginner:
        available = [a for a in adventures if a["is_beginner"]] or \
                    [a for a in adventures if a["name"] == "sample"]
        if not available:
            tprint(" No beginner adventure found.", "error"); return None
        tprint("\n As a new adventurer, you are directed to:", "desc")
        return available[0]

    print(tc("\n ─── Available Adventures ────────────────────────────", "border"))
    for i, adv in enumerate(adventures, 1):
        done = tc(" [completed]", "sys") if adv["name"] in character.adventures_completed else ""
        print(tc(f" {i}.", "border") + tc(f" {adv['title']}", "title") + done)
    print(tc(" R. Resume a saved game", "sys"))
    print(tc(" 0. Return to tavern", "border"))
    print()
    while True:
        raw = tinput(" Choose: ").strip().lower()
        if raw == "0": return None
        if raw == "r": menu_load_save(character); return None
        try:
            n = int(raw)
            if 1 <= n <= len(adventures): return adventures[n - 1]
        except ValueError:
            pass
        tprint(" Invalid choice.", "error")

# ── Engine launch & return ────────────────────────────────────────────────────
# ✅ BUG 7 FIX: NOW PASSES savefile PARAMETER
def _launch_engine(character, adv_path: str, savefile: str = ""):
    """Launch adventure directly."""
    from engine import run_adventure
    result = run_adventure(character, adv_path, savefile)  # ✅ savefile passed
    return result


def _handle_engine_return(character, result, adv_path: str,
                          adv_name: str = "", is_beginner_adv: bool = False) -> None:
    """Handle return from adventure."""
    # Character is already updated by run_adventure() - no need to reload
    
    completed = (result == 1)  # 1 = won
    died      = (result == 2)  # 2 = died
    escaped   = (result == 3)  # 3 = exited via EXIT_TAVERN
    crashed   = result not in (0, 1, 2, 3)

    if escaped:
        tprint("\n You return to the Saunter Inn.", "sys")
        return
    elif crashed:
        tprint("\n Something went wrong during that adventure.", "error")
    elif died:
        tprint("\n You have fallen. The tavern healer revives you for 2 gold per HP lost.", "warn")
        hp_lost = character.hp_max - character.hp
        cost = max(2, hp_lost * 2)
        character.gold = max(0, character.gold - cost)
        character.hp = character.hp_max
        character.save()
    elif completed:
        tprint("\n Welcome back, hero! Your deeds have been recorded.", "sys")
        character.is_beginner = False
        if adv_name and adv_name not in character.adventures_completed:
            character.adventures_completed.append(adv_name)
        character.save()

# ── Main loop ─────────────────────────────────────────────────────────────────

def run_tavern() -> None:
    print(tc(BANNER, "title"))

    character = menu_characters()
    if character is None:
        tprint("\n Safe travels.\n", "desc"); return

    first_entry = True
    while True:
        if first_entry:
            tprint(" Welcome to the Saunter Inn and Tavern.", "sys")
            first_entry = False

        action = run_tavern_exploration(character)

        if action == "EXIT_GAME":
            tprint("\n Until next time, adventurer.\n", "desc")
            break

        # action == "BOARD" — proceed to adventure board
        adventures = find_adventures()
        if not adventures:
            tprint(" No adventures available.", "error"); continue

        adv = choose_adventure(character, adventures)
        if adv is None:
            continue  # back to exploration

        tprint(f"\n You set out for: {adv['title']}\n", "sys")
        result = _launch_engine(character, adv["path"])
        _handle_engine_return(character, result, adv["path"],
                              adv_name=adv["name"],
                              is_beginner_adv=adv["is_beginner"])

        if result == 3:
            continue  # Escaped — return to tavern exploration

        again = tinput("\n Return to the Saunter Inn? (y/n): ").lower()
        if again != "y":
            tprint("\n Until next time, adventurer.", "desc"); break


if __name__ == "__main__":
    run_tavern()
