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

# ── Colors ────────────────────────────────────────────────────────────────────

_TAVERN_COLORS = {
    "title"  : "\033[1;33m",
    "border" : "\033[2;33m",
    "stat"   : "\033[0;37m",
    "sys"    : "\033[0;36m",
    "error"  : "\033[0;31m",
    "warn"   : "\033[0;33m",
    "prompt" : "\033[1;37m",
    "npc"    : "\033[0;35m",
    "desc"   : "\033[2;37m",
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

# ── Shop data ─────────────────────────────────────────────────────────────────

# Spell pricing mirrors engine.py SPELL_CATALOG; imported names come from character.py SPELL_DEFS
_SPELL_BASE_PRICE = {"heal": 50, "light": 25, "shield": 75, "fireball": 150}
_SPELL_FIGHTER_OK = {"heal", "light"}   # Fighters pay double for these

def _spell_price(spell_key: str, character) -> int:
    base  = _SPELL_BASE_PRICE.get(spell_key, 50)
    level = character.level
    for threshold, mult in ((2, 1), (4, 2), (6, 4), (8, 8)):
        if level <= threshold:
            base *= mult
            break
    else:
        base *= 16
    if character.char_class == "Fighter":
        base *= 2
    return base

HORACE_CORE = [
    {"name": "healing potion",       "artifact_type": "potion", "weight": 1, "heal_amount": 10, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0,  "price": 25,  "desc": "Restores 10 HP"},
    {"name": "minor healing potion", "artifact_type": "potion", "weight": 1, "heal_amount": 5,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0,  "price": 12,  "desc": "Restores 5 HP"},
    {"name": "ration",               "artifact_type": "food",   "weight": 1, "heal_amount": 4,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0,  "price": 5,   "desc": "Restores 4 HP when eaten"},
    {"name": "dagger",               "artifact_type": "weapon", "weight": 1, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0,  "price": 15,  "desc": "1d4 damage"},
    {"name": "short sword",          "artifact_type": "weapon", "weight": 2, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 0,  "price": 30,  "desc": "1d6 damage"},
    {"name": "leather armor",        "artifact_type": "armor",  "weight": 3, "heal_amount": 0,  "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 0,  "price": 40,  "desc": "AC +1"},
    {"name": "chainmail coat",       "artifact_type": "armor",  "weight": 6, "heal_amount": 0,  "armor_class": 3, "damage_dice": 1, "damage_sides": 4, "value": 0,  "price": 100, "desc": "AC +3"},
    {"name": "wooden shield",        "artifact_type": "shield", "weight": 3, "heal_amount": 0,  "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 0,  "price": 25,  "desc": "AC +1 (shield slot)"},
]

HORACE_RANDOM_POOL = [
    {"name": "war axe",     "artifact_type": "weapon", "weight": 4, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 8, "value": 0, "price": 50,  "desc": "1d8 damage"},
    {"name": "iron mace",   "artifact_type": "weapon", "weight": 3, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 0, "price": 35,  "desc": "1d6 damage"},
    {"name": "scale armor", "artifact_type": "armor",  "weight": 8, "heal_amount": 0, "armor_class": 4, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 180, "desc": "AC +4"},
    {"name": "iron shield", "artifact_type": "shield", "weight": 4, "heal_amount": 0, "armor_class": 2, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 55,  "desc": "AC +2 (shield slot)"},
    {"name": "hunting bow", "artifact_type": "weapon", "weight": 2, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 0, "price": 45,  "desc": "1d6 damage"},
    {"name": "torch",       "artifact_type": "light",  "weight": 1, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 3, "price": 8,   "desc": "A light source"},
]

WIZARD_RANDOM_POOL = [
    {"name": "greater healing potion", "artifact_type": "potion",   "weight": 1, "heal_amount": 20, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 60, "desc": "Restores 20 HP"},
    {"name": "mana potion",            "artifact_type": "potion",   "weight": 1, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 50, "desc": "Restores 10 mana"},
    {"name": "mystery scroll",         "artifact_type": "readable", "weight": 0, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 5, "price": 20, "desc": "Faded writing. Hard to read."},
]

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
        tprint(" Usage: S <number> or SELL ALL", "error"); return

    if raw == "sell all":
        pass  # total already set
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

def menu_load_save(character) -> bool:
    saves = list_saves(character)
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
        raw = tinput(" Choose save: ")
        try:
            n = int(raw)
            if n == 0: return False
            if 1 <= n <= len(saves):
                chosen = saves[n - 1]; break
        except ValueError:
            pass
        tprint(" Invalid choice.", "error")
    tprint(f"\n Resuming '{chosen['name']}' — {chosen['adv_title']}...", "sys")
    result = _launch_engine(character, chosen["adv_path"], savefile=chosen["name"])
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
    print()
    print(tc(" ┌────────────────────────────────────────────────┐", "border"))
    print(tc(f" │ {character.name:<{45}}│", "title"))
    print(tc(" ├────────────────────────────────────────────────┤", "border"))
    print(tc(f" │ Class:  {character.char_class:<{36}}│", "stat"))
    print(tc(f" │ Level:  {character.level}  (XP: {character.xp}){' '*28}│", "stat"))
    print(tc(f" │ Status: {'Veteran' if not character.is_beginner else 'Beginner':<{36}}│", "stat"))
    print(tc(" ├────────────────────────────────────────────────┤", "border"))
    print(tc(f" │ Hardiness:    {character.hardiness:<5} HP:  {character.hp:>3}/{character.hp_max:<{14}}│", "stat"))
    print(tc(f" │ Agility:      {character.agility:<5} (bonus: {character.agility_bonus:+d}){' '*18}│", "stat"))
    print(tc(f" │ Strength:     {character.strength:<5} (bonus: {character.strength_bonus:+d}){' '*18}│", "stat"))
    print(tc(f" │ Intelligence: {character.intelligence:<5} (bonus: {character.intelligence_bonus:+d}){' '*18}│", "stat"))
    print(tc(f" │ Charisma:     {character.charisma:<5} (bonus: {character.charisma_bonus:+d}){' '*18}│", "stat"))
    if character.char_class == "Sorcerer":
        print(tc(f" │ Mana:  {character.mana}/{character.mana_max}{' '*37}│", "stat"))
    print(tc(f" │ Gold:  {character.gold}g{' '*37}│", "sys"))
    print(tc(" └────────────────────────────────────────────────┘", "border"))
    print()

def show_inventory(character) -> None:
    carried = _load_carried(character)
    if not carried:
        tprint("\n You are not carrying anything.", "desc")
        return
    total_weight = sum(a.weight for a in carried)
    cap = character.carry_capacity
    print()
    print(tc(" ┌─── Your Inventory ────────────────────────────────┐", "border"))
    for i, a in enumerate(carried, 1):
        sv = f" ({sell_value(a)}g)" if can_sell(a) else ""
        print(tc(f" │ {i:>2}. {a.name:<30} {a.weight:>3}g{sv:<7}│", "stat"))
    print(tc(f" │ {'─'*48}│", "border"))
    print(tc(f" │ Weight: {total_weight}/{cap} gronds{' '*(37 - len(str(total_weight)) - len(str(cap)))}│", "sys"))
    print(tc(" └───────────────────────────────────────────────────┘", "border"))
    print()

def show_spells(character) -> None:
    from character import SPELL_DEFS
    print()
    if character.char_class != "Sorcerer":
        tprint(" You do not know any spells.", "warn"); return
    if not character.spells:
        tprint(" You have not learned any spells yet.", "warn"); return
    print(tc(" ┌─── Known Spells ──────────────────────────────────┐", "border"))
    print(tc(f" │ Mana: {character.mana}/{character.mana_max}{' '*39}│", "sys"))
    print(tc(" ├───────────────────────────────────────────────────┤", "border"))
    for key in character.spells:
        if key in SPELL_DEFS:
            sp = SPELL_DEFS[key]
            affordable = "✦" if character.mana >= sp["cost"] else "✗"
            print(tc(f" │ {affordable} {sp['name']:<12} ({sp['cost']} mana)  {sp['desc']:<20}│", "stat"))
    print(tc(" └───────────────────────────────────────────────────┘", "border"))
    print()

# ── Shops ─────────────────────────────────────────────────────────────────────

def run_horace_shop(character) -> None:
    random.seed(len(character.adventures_completed) * 7 + character.level)
    extras = random.sample(HORACE_RANDOM_POOL, min(3, len(HORACE_RANDOM_POOL)))
    random.seed()
    stock = HORACE_CORE + extras

    while True:
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
            carried  = _load_carried(character)
            sellable = [a for a in carried
                        if can_sell(a) and a.artifact_type in
                        {"weapon","armor","shield","ring","cloak","generic","light"}]
            if not sellable:
                tprint(" Nothing here I'd buy. Try Aldric for magical items.", "warn")
                continue
            print(tc("\n ── Your gear ──────────────────────────────────", "border"))
            for i, a in enumerate(sellable, 1):
                print(tc(f" {i:>3}. ", "border") +
                      tc(f"{a.name:<30}", "title") +
                      tc(f" {sell_value(a):>4}g", "sys"))
            sell_raw = tinput(" S <n> or SELL ALL: ").strip().lower()
            _process_sell(sell_raw, sellable, carried, character,
                          {"weapon","armor","shield","ring","cloak","generic","light"})

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
        tprint("\n " + tc("─── Aldric's Arcane Emporium ─────────────────────", "border"), "desc")
        print(tc(' Aldric says: "Knowledge has a price. So does everything else."', "npc"))
        print()

        # Spells available to this character's class
        fighter_only = character.char_class == "Fighter"
        available_spells = [
            (k, v) for k, v in SPELL_DEFS.items()
            if k not in character.spells
            and (not fighter_only or k in _SPELL_FIGHTER_OK)
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
        if character.char_class == "Sorcerer":
            print(tc(f" Known spells: {', '.join(character.spells) or 'none'}", "desc"))
        print(tc(" B <n> — buy   S <n> / SELL ALL — sell magical items   DONE — leave", "desc"))
        print()

        raw = tinput(" > ").strip().lower()

        if raw in ("done", "leave", "0", "d"):
            break

        elif raw == "s" or raw.startswith("sell"):
            carried  = _load_carried(character)
            sellable = [a for a in carried
                        if can_sell(a) and a.artifact_type in {"potion","readable","spellbook"}]
            if not sellable:
                tprint(" Nothing magical I'd buy. Try Horace for weapons.", "warn"); continue
            print(tc("\n ── Your magical items ─────────────────────────", "border"))
            for i, a in enumerate(sellable, 1):
                print(tc(f" {i:>3}. ", "border") +
                      tc(f"{a.name:<30}", "title") +
                      tc(f" {sell_value(a):>4}g", "sys"))
            sell_raw = tinput(" S <n> or SELL ALL: ").strip().lower()
            _process_sell(sell_raw, sellable, carried, character,
                          {"potion","readable","spellbook"})

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
                        character.spells.append(key)
                        character.save()
                        tprint(f" You have learned {val['name']}!", "sys")
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
    """Returns new room_id, 'QUIT', or None to stay."""
    room = TAVERN_ROOMS[room_id]
    cmd  = raw.strip().upper()
    low  = raw.strip().lower()

    # Movement
    direction = DIR_ABBREV.get(low, low)
    if direction in room.exits:
        return room.exits[direction]
    if cmd.startswith("GO "):
        direction = DIR_ABBREV.get(cmd[3:].strip().lower(), cmd[3:].strip().lower())
        if direction in room.exits:
            return room.exits[direction]
        tprint(" You can't go that way.", "error"); return None

    # TALK TO
    talk_target = ""
    if cmd.startswith("TALK TO "): talk_target = cmd[8:].strip()
    elif cmd.startswith("TALK "):  talk_target = cmd[5:].strip()
    if talk_target:
        if talk_target in ("HORACE",):
            if room.npc == "horace": run_horace_shop(character)
            else: tprint(" Horace is at the bar. Head north from the entrance.", "desc")
            return None
        if talk_target in ("ALDRIC","WIZARD"):
            if room.npc == "aldric": run_wizard_shop(character)
            else: tprint(" Aldric is in the back room. Bar, then east.", "desc")
            return None
        tprint(f" There is no one called '{raw.strip().split()[-1].lower()}' here.", "error")
        return None

    # Character info
    if cmd in ("CHARACTER","CHAR","C","STATUS","SHEET"):
        show_character_sheet(character); return None
    if cmd in ("INVENTORY","I","INV"):
        show_inventory(character); return None
    if cmd in ("SPELLS","SPELL"):
        show_spells(character); return None

    # Direct NPC keywords
    if cmd in ("HORACE","SHOP","BUY","SELL"):
        if room.npc == "horace": run_horace_shop(character)
        else: tprint(" Horace is at the bar. Head north from the entrance.", "desc")
        return None
    if cmd in ("ALDRIC","WIZARD","MAGIC"):
        if room.npc == "aldric": run_wizard_shop(character)
        else: tprint(" Aldric is in the back room. Bar, then east.", "desc")
        return None

    # Save/load
    if cmd in ("RESUME","LOAD","SAVES"):
        menu_load_save(character); return None

    # Meta
    if cmd in ("LOOK","L"):
        show_room(room); return None
    if cmd in ("HELP","H","?"):
        show_tavern_help(); return None
    if cmd in ("QUIT","Q","EXIT","LEAVE","ADVENTURE","BOARD"):
        return "QUIT"

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
        ("LOOK / L",          "Describe current room"),
        ("HORACE / SHOP",     "Trade with Horace (at the bar)"),
        ("ALDRIC / WIZARD",   "Visit Aldric (bar → east)"),
        ("TALK TO <name>",    "Speak to an NPC"),
        ("RESUME / SAVES",    "Resume a saved adventure"),
        ("QUIT / Q",          "Go to adventure board"),
        ("HELP / ?",          "This message"),
    ]
    for cmd, desc in cmds:
        print(tc(f" {cmd:<22}", "title") + tc(desc, "desc"))
    print()

def run_tavern_exploration(character) -> bool:
    """Walk the tavern until QUIT. Returns True to proceed to adventure board."""
    current_room = "entrance"
    show_room(TAVERN_ROOMS[current_room])
    tprint(" Type HELP for commands, QUIT for the adventure board.", "sys")
    while True:
        raw    = tinput(f" [{TAVERN_ROOMS[current_room].name}] > ")
        result = handle_tavern_command(raw, character, current_room)
        if result == "QUIT":
            return True
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

def _launch_engine(character, adv_path: str, savefile: str = ""):
    safe_name  = character.name.lower().replace(" ", "_")
    items_file = os.path.join("characters", f"{safe_name}_items.json")
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
        "--items-file",   items_file,
    ]
    if savefile:
        cmd += ["--savefile", savefile]
    return subprocess.run(cmd)

def _handle_engine_return(character, result, adv_path: str,
                          adv_name: str = "", is_beginner_adv: bool = False) -> None:
    # FIX: reload character from disk — engine may have updated XP, gold, level, spells, etc.
    from character import Character
    safe_name = character.name.lower().replace(" ", "_")
    reloaded  = Character.load(safe_name)
    if reloaded:
        for attr in ("hardiness","agility","strength","intelligence","charisma",
                     "hp","mana","gold","xp","level","spells",
                     "is_beginner","adventures_completed"):
            setattr(character, attr, getattr(reloaded, attr))

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

        run_tavern_exploration(character)

        adventures = find_adventures()
        if not adventures:
            tprint(" No adventures available.", "error"); break

        adv = choose_adventure(character, adventures)
        if adv is None:
            continue  # back to exploration

        tprint(f"\n You set out for: {adv['title']}\n", "sys")
        result = _launch_engine(character, adv["path"])
        _handle_engine_return(character, result, adv["path"],
                              adv_name=adv["name"],
                              is_beginner_adv=adv["is_beginner"])

        again = tinput("\n Return to the adventure board? (y/n): ").lower()
        if again != "y":
            tprint("\n Until next time, adventurer.", "desc"); break


if __name__ == "__main__":
    run_tavern()
