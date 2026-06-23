"""
tavern.py — Main Hall of the Free Adventurers.

Entry point for the game system. Handles character creation/selection,
adventure launching, and the Main Hall as a navigable space with live NPCs,
shops, a bank, Marie Laveau's chamber, and the exit to the wider world.
"""

from __future__ import annotations

import os
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
    "sys"    : "\033[0;36m",   # cyan           — gold, system info
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

# ── Session state (resets each time the player enters the Main Hall) ──────────

_session: dict = {
    "marie_bonus":  0,       # attitude modifier from gifts given this session
    "npc_greeted":  set(),   # room_ids where NPC has already spoken on entry
    "verbose":      True,    # verbose mode: show full desc every visit (like engine)
    "visited":      set(),   # room_ids seen this session (for brief mode)
    "floor_items":  {},      # room_id → list of Artifact dropped this session
}

def _reset_session() -> None:
    _session["marie_bonus"] = 0
    _session["npc_greeted"] = set()
    _session["verbose"]     = True
    _session["visited"]     = set()
    _session["floor_items"] = {}

# ── Main Hall rooms ────────────────────────────────────────────────────────────

@dataclass
class TavernRoom:
    room_id: str
    name: str
    description: str
    brief_description: str
    exits: dict
    npc: Optional[str] = None

MAIN_HALL_ROOMS = {
    "foyer": TavernRoom(
        room_id="foyer",
        name="The Main Hall",
        description=(
            " You stand in the grand foyer of the Main Hall of the Free Adventurers.\n"
            " Marble columns rise to a vaulted ceiling hung with the banners of storied\n"
            " guilds. An enchanted map on the north wall marks known adventure sites.\n"
            " Passages branch off in every direction. A heavy oak door to the south\n"
            " opens onto the street beyond.\n"
        ),
        brief_description=" The Main Hall foyer. Marble columns, enchanted map north. Exits: N, E, W, NE, S (street).",
        exits={
            "north":     "common_room",
            "east":      "weapon_shop",
            "west":      "bank",
            "northeast": "guild_hall",
            "south":     "EXIT_UNIVERSE",
        },
    ),
    "common_room": TavernRoom(
        room_id="common_room",
        name="The Saunter Inn — Common Room",
        description=(
            " A warm, smoke-hazed common room thick with the smell of roasting meat and\n"
            " spilled ale. Adventurers of every fortune crowd the long trestle tables.\n"
            " A fire roars in the stone hearth. The passage east smells faintly of\n"
            " incense. To the north, beads clatter softly in a draught.\n"
        ),
        brief_description=" Saunter Inn common room. Smoke, fire, and adventurers. Exits: S, E, N (beads).",
        exits={
            "south": "foyer",
            "east":  "magic_shop",
            "north": "witch_chamber",
        },
    ),
    "weapon_shop": TavernRoom(
        room_id="weapon_shop",
        name="Cavielli's Weapons and Armour Shoppe",
        description=(
            " Weapons of every description fill racks from floor to ceiling — swords,\n"
            " axes, maces, bows, and armour of a dozen styles. The air smells of oil\n"
            " and fresh leather. A stocky man in a black apron looks up from the blade\n"
            " he is honing, his eyes measuring you in an instant.\n"
        ),
        brief_description=" Cavielli's Weapons Shoppe. Racks of arms and armour. Marcus Marcos is here.",
        exits={"west": "foyer"},
        npc="marcus",
    ),
    "magic_shop": TavernRoom(
        room_id="magic_shop",
        name="Magic, Potions and Sundries",
        description=(
            " Shelves crammed with arcane curiosities line every wall, floor to ceiling.\n"
            " Jars of strange ingredients, bundled scrolls, and crystalline vials catch\n"
            " the candlelight. The air tastes of ozone and dried flowers. A lean man in\n"
            " robes sits at a high desk, quill poised, peering over wire-rimmed spectacles.\n"
        ),
        brief_description=" Aldric's shop. Arcane goods on every shelf, ozone in the air. Aldric is here.",
        exits={"west": "common_room"},
        npc="aldric",
    ),
    "witch_chamber": TavernRoom(
        room_id="witch_chamber",
        name="Marie Laveau's Chamber",
        description=(
            " You push aside a beaded curtain and step into a dim, candlelit room.\n"
            " Dried herbs hang from the rafters. Bones, crystals, and strange tokens\n"
            " crowd every surface. Incense smoke coils upward in lazy spirals. An\n"
            " imposing woman in dark robes sits at the centre, a crystal ball before\n"
            " her. Her gaze finds you before you speak a word.\n"
        ),
        brief_description=" Marie Laveau's candlelit chamber. Incense, crystals, bones. She watches you.",
        exits={"south": "common_room"},
        npc="marie",
    ),
    "bank": TavernRoom(
        room_id="bank",
        name="The Main Hall Bank",
        description=(
            " A solid stone chamber with iron-bound doors and a polished granite counter.\n"
            " The vault behind the counter is a foot of solid steel with a brass combination\n"
            " lock. A neat, balding man in a green coat and wire spectacles looks up\n"
            " from a leather-bound ledger and sets down his pen.\n"
        ),
        brief_description=" The Main Hall Bank. Granite counter, steel vault. Pemberton is here.",
        exits={"east": "foyer"},
        npc="banker",
    ),
    "guild_hall": TavernRoom(
        room_id="guild_hall",
        name="The Adventurers' Guild Hall",
        description=(
            " The heart of the Guild of Free Adventurers. A massive brass-framed board\n"
            " covers the far wall, thick with contracts, maps, and notices of quests both\n"
            " available and recently completed. The guild registrar sits at a desk near\n"
            " the door. Type ADVENTURE to browse the quest board.\n"
        ),
        brief_description=" The Guild Hall. Quest board on the far wall. Type ADVENTURE to browse.",
        exits={"southwest": "foyer"},
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
║     ~ Main Hall of the Free Adventurers ~                            ║
║   Where legends begin, and gold changes hands freely                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ── Item valuation ────────────────────────────────────────────────────────────

TYPE_VALUE_FLOOR = {
    "weapon": 10, "armor": 15, "shield": 10, "ring": 20, "cloak": 15,
    "potion": 5,  "food": 2,   "readable": 3, "generic": 1, "light": 3,
    "spellbook": 25,
}
UNSELLABLE_TYPES = {"key"}

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

MARCUS_CORE = [
    {"name": "dagger",         "artifact_type": "weapon", "weight": 1, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 5,  "price": 15,  "desc": "1d4 (sword)"},
    {"name": "short sword",    "artifact_type": "weapon", "weight": 2, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 10, "price": 30,  "desc": "1d6 (sword)"},
    {"name": "leather armor",  "artifact_type": "armor",  "weight": 3, "heal_amount": 0, "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 13, "price": 40,  "desc": "AC +1"},
    {"name": "chainmail coat", "artifact_type": "armor",  "weight": 6, "heal_amount": 0, "armor_class": 3, "damage_dice": 1, "damage_sides": 4, "value": 30, "price": 100, "desc": "AC +3"},
    {"name": "wooden shield",  "artifact_type": "shield", "weight": 3, "heal_amount": 0, "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 8,  "price": 25,  "desc": "AC +1 (shield)"},
    {"name": "ration",         "artifact_type": "food",   "weight": 1, "heal_amount": 4, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 2,  "price": 5,   "desc": "Restores 4 HP"},
    {"name": "torch",          "artifact_type": "light",  "weight": 1, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 3,  "price": 8,   "desc": "Light source"},
]

MARCUS_RANDOM_POOL = [
    {"name": "war axe",     "artifact_type": "weapon", "weight": 4, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 8, "value": 15, "price": 50,  "desc": "1d8 (axe)"},
    {"name": "iron mace",   "artifact_type": "weapon", "weight": 3, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 12, "price": 35,  "desc": "1d6 (club)"},
    {"name": "spear",       "artifact_type": "weapon", "weight": 3, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 10, "price": 28,  "desc": "1d6 (spear)"},
    {"name": "hunting bow", "artifact_type": "weapon", "weight": 2, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 15, "price": 45,  "desc": "1d6 (bow)"},
    {"name": "longsword",   "artifact_type": "weapon", "weight": 3, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 8, "value": 20, "price": 60,  "desc": "1d8 (sword)"},
    {"name": "scale armor", "artifact_type": "armor",  "weight": 8, "heal_amount": 0, "armor_class": 4, "damage_dice": 1, "damage_sides": 4, "value": 60, "price": 180, "desc": "AC +4"},
    {"name": "iron shield", "artifact_type": "shield", "weight": 4, "heal_amount": 0, "armor_class": 2, "damage_dice": 1, "damage_sides": 4, "value": 18, "price": 55,  "desc": "AC +2 (shield)"},
    {"name": "battle axe",  "artifact_type": "weapon", "weight": 5, "heal_amount": 0, "armor_class": 0, "damage_dice": 2, "damage_sides": 6, "value": 25, "price": 80,  "desc": "2d6 (axe)"},
]

ALDRIC_POTIONS = [
    {"name": "healing potion",        "artifact_type": "potion",   "weight": 1, "heal_amount": 10, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 8,  "price": 25, "desc": "Restores 10 HP"},
    {"name": "minor healing potion",  "artifact_type": "potion",   "weight": 1, "heal_amount": 5,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 4,  "price": 12, "desc": "Restores 5 HP"},
    {"name": "greater healing potion","artifact_type": "potion",   "weight": 1, "heal_amount": 20, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 20, "price": 60, "desc": "Restores 20 HP"},
    {"name": "mana potion",           "artifact_type": "potion",   "weight": 1, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 15, "price": 50, "desc": "Restores 10 mana"},
    {"name": "mystery scroll",        "artifact_type": "readable", "weight": 0, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 5,  "price": 20, "desc": "Faded writing"},
]

_SHOP_SELL_VALUES = {
    item["name"]: item["value"]
    for pool in (MARCUS_CORE, MARCUS_RANDOM_POOL, ALDRIC_POTIONS)
    for item in pool
    if item["value"] > 0
}

MAX_POTIONS = 2

# ── Item management helpers ───────────────────────────────────────────────────

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
        except ValueError:
            tprint(" Usage: S <number> or SELL ALL", "error"); return
    else:
        try:
            idx = int(raw) - 1
            if not (0 <= idx < len(sellable)):
                tprint(" Invalid number.", "error"); return
            item  = sellable[idx]
            price = sell_value(item)
            if tinput(f" Sell {item.name} for {price}g? (y/n): ").lower() != "y":
                return
            ids_to_sell = {id(item)}
        except ValueError:
            tprint(" Usage: S <number> or SELL ALL", "error"); return

    sold      = [a for a in sellable if id(a) in ids_to_sell]
    total     = sum(sell_value(a) for a in sold)
    remaining = [a for a in all_carried if id(a) not in ids_to_sell]
    _save_carried(character, remaining)
    character.gold += total
    character.save()
    tprint(f" Sold for {total}g. Gold: {character.gold}g", "sys")

# ── Character display ─────────────────────────────────────────────────────────

def _tavern_effective_stats(character) -> dict:
    """Compute effective stats for character sheet by summing stat_bonuses of equipped items."""
    items = _load_carried(character)
    bonuses: dict[str, int] = {}
    for item_name in character.equipped.values():
        if item_name:
            for item in items:
                if item.name == item_name:
                    for stat, val in (item.stat_bonuses or {}).items():
                        bonuses[stat] = bonuses.get(stat, 0) + val
                    break
    if not bonuses:
        return {}
    return {stat: getattr(character, stat, 0) + bonus
            for stat, bonus in bonuses.items()}

def show_character_sheet(character) -> None:
    effective = _tavern_effective_stats(character)
    print(f"\033[1;33m{character.stat_summary(effective_stats=effective or None)}\033[0m")

def show_inventory(character) -> None:
    carried = _load_carried(character)
    if not carried:
        tprint("\n You are not carrying anything.", "desc")
        return
    total_weight = sum(a.weight for a in carried)
    cap = character.carry_capacity
    equipped_names = set(character.equipped.values())
    INNER = 46
    print()
    print(tc(" ┌─── Your Inventory ────────────────────────────────┐", "border"))
    for i, a in enumerate(carried, 1):
        sv = f" ({sell_value(a)}g)" if can_sell(a) else ""
        eq = " [EQUIPPED]" if a.name in equipped_names else ""
        right = f"{a.weight:>3}g{sv:<7}"
        left  = f"{i:>2}. {a.name}{eq}"
        pad   = max(0, INNER - len(left) - len(right))
        inner = (left + " " * pad + right)[:INNER]
        color = "title" if eq else "stat"
        print(tc(" │ ", "border") + tc(inner, color) + tc("│", "border"))
    print(tc(f" │ {'─'*INNER}│", "border"))
    wline = f" Weight: {total_weight}/{cap} gronds  |  Bank: {character.bank_balance}g"
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
               "shield": "shield", "ring": "ring", "cloak": "cloak"}

def cmd_equip_tavern(noun: str, character) -> None:
    carried    = _load_carried(character)
    equippable = [a for a in carried if a.artifact_type in _EQUIP_SLOT]
    if not equippable:
        tprint(" You have nothing that can be equipped.", "warn"); return

    equipped_names = set(character.equipped.values())
    target = None
    if noun:
        for a in equippable:
            if noun.lower() in a.name.lower():
                target = a; break
        if not target:
            tprint(f" You're not carrying anything called '{noun}'.", "error"); return
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
        raw = tinput(" Equip # (0 to cancel): ").strip()
        if not raw or raw == "0": return
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(equippable):
                target = equippable[idx]
            else:
                tprint(" Invalid number.", "error"); return
        except ValueError:
            tprint(" Invalid input.", "error"); return

    slot = _EQUIP_SLOT[target.artifact_type]
    current_name = character.equipped.get(slot)
    if current_name:
        current = next((a for a in carried if a.name == current_name), None)
        if current and current.flags.get("cursed"):
            tprint(f" The {current_name} is cursed — it cannot be removed!", "error"); return
        msg = f" You remove the {current_name} and equip the {target.name}."
    else:
        msg = f" You equip the {target.name}."
    character.equipped[slot] = target.name
    character.save()
    tprint(msg, "desc")

# ── Marie Laveau ──────────────────────────────────────────────────────────────

_STATS      = ["hardiness", "agility", "charisma", "intelligence", "strength"]
_STAT_NAMES = {
    "hardiness":    "Hardiness",
    "agility":      "Agility",
    "charisma":     "Charisma",
    "intelligence": "Intelligence",
    "strength":     "Strength",
}
_STAT_ALIASES = {
    # Short forms
    "hard": "hardiness", "har": "hardiness",
    "agi":  "agility",   "ag":  "agility",
    "cha":  "charisma",  "ch":  "charisma",
    "int":  "intelligence",
    "str":  "strength",  "stre": "strength",
    # Full names
    "hardiness": "hardiness", "agility": "agility", "charisma": "charisma",
    "intelligence": "intelligence", "strength": "strength",
}

def _marie_total_attitude(character) -> int:
    """Persistent attitude + session gift bonus + charisma modifier."""
    charisma_mod = 0
    if character.charisma >= 16:
        charisma_mod = 1
    elif character.charisma <= 7:
        charisma_mod = -1
    return max(-3, min(3, character.marie_attitude + _session["marie_bonus"] + charisma_mod))

def _marie_greeting_line(character) -> str:
    att = _marie_total_attitude(character)
    if att >= 2:
        return tc(' Marie Laveau spreads her arms. "Mon cher! Marie has been expecting you. Come, sit."', "npc")
    elif att == 1:
        return tc(' Marie fixes you with a knowing look. "Ah. You return. Sit, child. We have business."', "npc")
    elif att == 0:
        return tc(' Marie regards you without expression. "You may enter. State your purpose."', "npc")
    elif att == -1:
        return tc(' Marie\'s eyes narrow. "You again. Marie remembers our last meeting. Be careful."', "npc")
    else:
        return tc(' Marie holds up a hand. "Stop. You have displeased Marie. Bring an offering first."', "npc")

def _marie_lowest_stat(character) -> str:
    return min(_STATS, key=lambda s: getattr(character, s))

def _marie_give_gift(item, character) -> None:
    """Process giving an item to Marie. Adjusts session and persistent attitude."""
    val = item.value if item.value > 0 else 1
    if val >= 200:
        _session["marie_bonus"] += 2
        character.marie_attitude = min(3, character.marie_attitude + 1)
        print(tc(' Marie\'s eyes gleam as she turns the gift over slowly. "Now THIS is a proper', "npc"))
        print(tc(' offering, cher. Marie is... very pleased."', "npc"))
    elif val >= 50:
        _session["marie_bonus"] += 1
        print(tc(' Marie nods slowly, examining the gift. "Acceptable. Marie acknowledges', "npc"))
        print(tc(' your... consideration."', "npc"))
    elif val >= 10:
        print(tc(' Marie glances at the gift, then back at you. "This is... modest."', "npc"))
        print(tc(' "It is noted. But do not expect Marie\'s favour to come cheaply, cher."', "npc"))
    else:
        _session["marie_bonus"] -= 1
        character.marie_attitude = max(-3, character.marie_attitude - 1)
        print(tc(' Marie\'s lip curls. "You offer Marie THIS? That is an insult dressed as a gift."', "npc"))
        print(tc(' "Take it back. And think very carefully about your next visit."', "npc"))
    character.save()

def run_marie_shop(character) -> None:
    """Marie Laveau's stat-raising service."""
    att = _marie_total_attitude(character)
    print()
    print(tc(" ─── Marie Laveau's Chamber ──────────────────────────", "border"))
    print(_marie_greeting_line(character))
    print()

    if att >= 0:
        print(tc(' "Marie can see what you seek. You wish to become more than you are."', "npc"))
        print(tc(' "For the right... tribute... Marie can channel the forces of change."', "npc"))
    else:
        print(tc(' "You have not pleased Marie. Bring a worthy offering before you ask', "npc"))
        print(tc(' for her gifts. GIVE <item> to make an offering."', "npc"))
    print()

    # Show current stats
    for s in _STATS:
        val = getattr(character, s)
        print(tc(f"  {_STAT_NAMES[s]:<14}: {val}", "stat"))
    print()
    print(tc(f"  Gold: {character.gold}g  |  Bank: {character.bank_balance}g", "sys"))
    print(tc("  Enter a stat name to request an increase, GIVE <item> to offer a gift,", "desc"))
    print(tc("  or DONE to leave.", "desc"))
    print()

    raw = tinput(" > ").strip().lower()

    if raw in ("done", "leave", "0"):
        print(tc(' "Until next time, cher," Marie says, returning to her crystal ball.', "npc"))
        return

    if raw.startswith("give "):
        _marie_give_gift_by_name(raw[5:].strip(), character)
        return

    stat = _STAT_ALIASES.get(raw)
    if not stat:
        tprint(f' Marie raises an eyebrow. "Marie knows no stat called \'{raw}\'."', "npc")
        return

    # Calculate price with charisma influence
    base_cost = random.randint(2500, 5000)
    if character.charisma >= 15:
        discount = random.uniform(0.05, 0.20)
        cost = int(base_cost * (1 - discount))
        cost_note = f"  ({int(discount*100)}% charisma discount)"
    elif character.charisma <= 8:
        surcharge = random.uniform(0.05, 0.15)
        cost = int(base_cost * (1 + surcharge))
        cost_note = f"  ({int(surcharge*100)}% surcharge — your manner displeases)"
    else:
        cost = base_cost
        cost_note = ""

    stat_name = _STAT_NAMES[stat]
    print()
    print(tc(f' Marie studies you for a long moment. "For {stat_name}...', "npc"))
    print(tc(f' the spirits ask {cost}g.{cost_note}"', "npc"))
    print()

    confirm = tinput(f" Pay {cost}g? (y/n): ").lower()
    if confirm != "y":
        print(tc(' "Come back when you are ready," Marie says without looking up.', "npc"))
        return

    if character.gold < cost:
        print(tc(f' "You do not have {cost}g. Marie cannot work for promises."', "npc"))
        return

    character.gold -= cost
    print()
    print(tc(' Marie closes her eyes. Her lips move in silence. The candles flicker.', "desc"))
    print(tc(' The air in the room grows heavy and still.', "desc"))
    print()

    # Determine outcome based on attitude
    actual_stat = stat

    if att >= 2:
        # Loves you — guaranteed chosen stat
        actual_stat = stat
        outcome = f' "It is done," Marie says warmly. "Your {stat_name} grows, as you wished."'
    elif att == 1:
        # Likes you — 85% chance of chosen stat
        if random.random() < 0.85:
            actual_stat = stat
            outcome = f' Marie opens her eyes. "Your {stat_name} has been strengthened, cher."'
        else:
            actual_stat = random.choice([s for s in _STATS if s != stat])
            outcome = (f' Marie opens her eyes. "The spirits chose their own path today.'
                       f' Your {_STAT_NAMES[actual_stat]} grows instead."')
    elif att == 0:
        # Neutral — raises the player's weakest stat (her choice)
        actual_stat = _marie_lowest_stat(character)
        if actual_stat == stat:
            outcome = f' Marie opens her eyes. "The spirits agreed with your choice. {stat_name} grows."'
        else:
            outcome = (f' Marie opens her eyes. "The spirits showed Marie something different.'
                       f' Your {_STAT_NAMES[actual_stat]} needed growth more urgently."')
    elif att == -1:
        # Dislikes you — unpredictable
        r = random.random()
        if r < 0.35:
            actual_stat = _marie_lowest_stat(character)
            outcome = (f' Marie opens her eyes, expression unreadable. "The spirits see your'
                       f' weakness. Your {_STAT_NAMES[actual_stat]} is raised. Not what you'
                       f' asked — what you needed."')
        elif r < 0.70:
            actual_stat = random.choice([s for s in _STATS if s != stat])
            outcome = (f' Marie opens her eyes with a faint smile. "The spirits were'
                       f' capricious. Your {_STAT_NAMES[actual_stat]} grows."')
        else:
            # Takes money, raises something random anyway
            actual_stat = random.choice(_STATS)
            outcome = (f' Marie opens her eyes slowly. "The spirits... wandered. Your'
                       f' {_STAT_NAMES[actual_stat]} is altered. Perhaps next time bring'
                       f' a worthier gift."')
    else:
        # Hates you — 40% chance of nothing useful
        if random.random() < 0.40:
            print(tc(' The candles flare and die. When they relight, Marie is watching you coldly.', "desc"))
            print(tc(' "The spirits refused. Your gold, however, is mine."', "npc"))
            print(tc(' "Come back when you have learned some manners — and brought a proper offering."', "npc"))
            character.save()
            return
        else:
            actual_stat = random.choice(_STATS)
            outcome = (f' Marie opens her eyes. A cruel smile crosses her lips. "The spirits'
                       f' gave what they wished. Your {_STAT_NAMES[actual_stat]} is changed.'
                       f' Perhaps this teaches you to treat Marie with more respect."')

    old_val = getattr(character, actual_stat)
    setattr(character, actual_stat, old_val + 1)
    if actual_stat == "hardiness":
        character.hp = min(character.hp + 2, character.hp_max)

    print(tc(outcome, "npc"))
    print()
    print(tc(f"  {_STAT_NAMES[actual_stat]}: {old_val} → {old_val + 1}", "stat"))
    print()
    character.save()

def _marie_give_gift_by_name(name: str, character) -> None:
    """Handle GIVE <item> in Marie's chamber."""
    carried = _load_carried(character)
    item = next((a for a in carried if name.lower() in a.name.lower()), None)
    if not item:
        tprint(f" You're not carrying anything called '{name}'.", "error"); return
    _marie_give_gift(item, character)
    remaining = [a for a in carried if id(a) != id(item)]
    _save_carried(character, remaining)
    tprint(f" You place the {item.name} before Marie.", "desc")

# ── The Bank ──────────────────────────────────────────────────────────────────

def run_bank(character) -> None:
    """Reginald T. Pemberton — Main Hall Bank."""
    print()
    print(tc(" ─── The Main Hall Bank ──────────────────────────────", "border"))
    print(tc(' Pemberton sets down his pen and folds his hands precisely.', "desc"))
    print(tc(' "Reginald T. Pemberton, at your service. Your gold is safe here."', "npc"))
    print(tc(' "DEPOSIT, WITHDRAW, BALANCE, or DONE."', "npc"))
    _show_balance(character)
    print()

    while True:
        raw = tinput(" > ").strip().lower()

        if raw in ("done", "leave", "0", "d"):
            print(tc(' "Good day to you. Your assets are always safe in our vault."', "npc"))
            break

        elif raw in ("balance", "bal", "b"):
            _show_balance(character)

        elif raw.startswith("deposit"):
            _bank_deposit(raw[7:].strip(), character)

        elif raw.startswith("withdraw"):
            _bank_withdraw(raw[8:].strip(), character)

        else:
            tprint(" DEPOSIT <amount>, WITHDRAW <amount>, BALANCE, or DONE.", "warn")

def _show_balance(character) -> None:
    print()
    print(tc(f"  Carried gold : {character.gold}g", "stat"))
    print(tc(f"  Bank balance : {character.bank_balance}g", "stat"))
    print()

def _bank_deposit(amt_str: str, character) -> None:
    if amt_str in ("all", ""):
        amt = character.gold
    else:
        try:
            amt = int(amt_str)
        except ValueError:
            tprint(' "How much? DEPOSIT <amount> or DEPOSIT ALL."', "error"); return
    if amt <= 0:
        tprint(' "There is nothing to deposit."', "warn"); return
    if amt > character.gold:
        tprint(f' "You only have {character.gold}g to deposit."', "error"); return
    if tinput(f" Deposit {amt}g? (y/n): ").lower() != "y":
        return
    character.gold -= amt
    character.bank_balance += amt
    character.save()
    print(tc(f' Pemberton notes it carefully in his ledger. "Deposited {amt}g."', "npc"))
    _show_balance(character)

def _bank_withdraw(amt_str: str, character) -> None:
    if amt_str in ("all", ""):
        amt = character.bank_balance
    else:
        try:
            amt = int(amt_str)
        except ValueError:
            tprint(' "How much? WITHDRAW <amount> or WITHDRAW ALL."', "error"); return
    if amt <= 0:
        tprint(' "There is nothing to withdraw."', "warn"); return
    if amt > character.bank_balance:
        tprint(f' "Your balance is only {character.bank_balance}g."', "error"); return
    if tinput(f" Withdraw {amt}g? (y/n): ").lower() != "y":
        return
    character.bank_balance -= amt
    character.gold += amt
    character.save()
    print(tc(f' Pemberton counts out the coins with practiced efficiency. "Withdrawn {amt}g."', "npc"))
    _show_balance(character)

# ── Cavielli's Weapons and Armour Shoppe ──────────────────────────────────────

def run_marcus_shop(character) -> None:
    random.seed(len(character.adventures_completed) * 7 + character.level)
    extras = random.sample(MARCUS_RANDOM_POOL, min(4, len(MARCUS_RANDOM_POOL)))
    random.seed()
    stock = MARCUS_CORE + extras

    # Charisma gives a small buy-price discount
    raw_discount = (character.charisma - 10) * 0.015
    discount = max(0.0, min(0.15, raw_discount))

    while True:
        show_inventory(character)
        tprint("\n " + tc("─── Cavielli's Weapons and Armour Shoppe ─────────", "border"), "desc")
        if "weapon_shop" not in _session["npc_greeted"]:
            print(tc(' Marcus looks you over with a tradesman\'s eye. "Marcus Marcos — finest', "npc"))
            print(tc(' steel in the city. You look like someone who knows quality. What\'ll it be?"', "npc"))
            _session["npc_greeted"].add("weapon_shop")
        else:
            print(tc(' Marcus nods. "Back again. Good. Let\'s do business."', "npc"))
        print()
        for i, item in enumerate(stock, 1):
            price = max(1, int(item["price"] * (1 - discount)))
            print(tc(f" {i:>3}. ", "border") +
                  tc(f"{item['name']:<28}", "title") +
                  tc(f" {price:>4}g  ", "sys") +
                  tc(item.get("desc", ""), "desc"))
        print()
        if discount > 0.005:
            print(tc(f" (Charisma earns you a {int(discount*100)}% discount)", "sys"))
        print(tc(f" Gold: {character.gold}g", "stat"))
        print(tc(" B <n> — buy   S <n> / SELL ALL — sell gear   DONE — leave", "desc"))
        print()

        raw = tinput(" > ").strip().lower()

        if raw in ("done", "leave", "0", "d"):
            print(tc(' "Come back anytime. Marcus Marcos always has what you need."', "npc"))
            break

        elif raw == "s" or raw.startswith("sell"):
            carried        = _load_carried(character)
            equipped_names = set(character.equipped.values())
            marcus_types   = {"weapon","armor","shield","ring","cloak","generic","light","food"}
            eligible       = [a for a in carried if can_sell(a) and a.artifact_type in marcus_types]
            sellable       = [a for a in eligible if a.name not in equipped_names]
            if not eligible:
                tprint(' "Nothing here I\'d buy. Try Aldric for potions and scrolls."', "warn")
                continue
            print(tc(" ── Items Marcus will buy ───────────────────────────", "border"))
            n = 0
            for a in eligible:
                is_eq = a.name in equipped_names
                if is_eq:
                    print(tc("      ", "border") +
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
            _process_sell(sell_raw, sellable, carried, character, marcus_types)

        elif raw.startswith("b "):
            try:
                idx   = int(raw[2:]) - 1
                if not (0 <= idx < len(stock)):
                    tprint(" Invalid number.", "error"); continue
                item  = stock[idx]
                price = max(1, int(item["price"] * (1 - discount)))
                if character.gold < price:
                    tprint(f' "That\'ll be {price}g. You\'re a bit short." ({character.gold}g carried)', "error"); continue
                if tinput(f" Buy {item['name']} for {price}g? (y/n): ").lower() == "y":
                    character.gold -= price
                    _add_to_inventory(character, item)
                    character.save()
                    tprint(f' "Good choice." Purchased. Gold: {character.gold}g', "sys")
            except ValueError:
                tprint(" Enter B followed by a number.", "error")

        else:
            tprint(" B <n> to buy, S to sell, or DONE.", "warn")

# ── Aldric's Magic, Potions and Sundries ──────────────────────────────────────

def _aldric_spell_price(spell_key: str, character) -> int:
    """Spell base price with small Charisma modifier (random ±5-15%)."""
    from character import SPELL_DEFS
    base = SPELL_DEFS[spell_key]["cost"]
    if character.charisma >= 15:
        # High charisma: 5-15% random discount
        return int(base * (1 - random.uniform(0.05, 0.15)))
    elif character.charisma <= 8:
        # Low charisma: 5-10% surcharge
        return int(base * (1 + random.uniform(0.05, 0.10)))
    return base

def run_aldric_shop(character) -> None:
    from character import SPELL_DEFS

    random.seed(len(character.adventures_completed) * 13 + character.level)
    extras = random.sample(ALDRIC_POTIONS, min(3, len(ALDRIC_POTIONS)))
    random.seed()

    while True:
        show_inventory(character)
        tprint("\n " + tc("─── Magic, Potions and Sundries ──────────────────", "border"), "desc")
        if "magic_shop" not in _session["npc_greeted"]:
            print(tc(' Aldric sets down his quill and studies you over his spectacles.', "desc"))
            print(tc(' "A seeker of the arcane arts, perhaps? Or merely in need of a restorative?"', "npc"))
            print(tc(' "Either way — you have found the right establishment."', "npc"))
            _session["npc_greeted"].add("magic_shop")
        else:
            print(tc(' Aldric glances up briefly. "Back already. Browse freely."', "npc"))
        print()

        available_spells = [
            (k, v) for k, v in SPELL_DEFS.items()
            if character.spell_proficiencies.get(k) is None
        ]

        print(tc(" ── Spells ─────────────────────────────────────────", "border"))
        if available_spells:
            for i, (key, spell) in enumerate(available_spells, 1):
                price = _aldric_spell_price(key, character)
                mark  = "✦" if character.gold >= price else "✗"
                print(tc(f" {i:>3}. ", "border") +
                      tc(f"{spell['name']:<15}", "title") +
                      tc(f" {price:>5}g  ", "sys") +
                      tc(spell["desc"], "desc") +
                      tc(f"  {mark}", "sys"))
        else:
            tprint(" You know all available spells.", "sys")

        item_offset = len(available_spells)
        print(tc("\n ── Potions and Sundries ──────────────────────────", "border"))
        for i, item in enumerate(extras, item_offset + 1):
            limit = " [at limit]" if item["artifact_type"] == "potion" and _count_potions(character) >= MAX_POTIONS else ""
            print(tc(f" {i:>3}. ", "border") +
                  tc(f"{item['name']:<28}", "title") +
                  tc(f" {item['price']:>4}g  ", "sys") +
                  tc(item.get("desc", ""), "desc") +
                  tc(limit, "error"))

        print()
        learned = [k for k, v in character.spell_proficiencies.items() if v is not None]
        print(tc(f" Gold: {character.gold}g  |  Known: {', '.join(learned) if learned else 'none'}", "stat"))
        print(tc(" B <n> — buy   S <n> / SELL ALL — sell potions/scrolls   DONE — leave", "desc"))
        print()

        raw = tinput(" > ").strip().lower()

        if raw in ("done", "leave", "0", "d"):
            print(tc(' "Knowledge is never wasted. Return when you need more."', "npc"))
            break

        elif raw == "s" or raw.startswith("sell"):
            carried        = _load_carried(character)
            equipped_names = set(character.equipped.values())
            aldric_types   = {"potion","readable","spellbook"}
            eligible       = [a for a in carried if can_sell(a) and a.artifact_type in aldric_types]
            sellable       = [a for a in eligible if a.name not in equipped_names]
            if not eligible:
                tprint(' "Nothing magical I\'d buy. Try Marcus for weapons and armour."', "warn"); continue
            print(tc(" ── Items Aldric will buy ───────────────────────────", "border"))
            n = 0
            for a in eligible:
                is_eq = a.name in equipped_names
                if is_eq:
                    print(tc("      ", "border") +
                          tc(f"{a.name:<30}", "title") +
                          tc(f" {sell_value(a):>4}g", "sys") +
                          tc(" [EQUIPPED — unequip first]", "warn"))
                else:
                    n += 1
                    print(tc(f" {n:>3}. ", "border") +
                          tc(f"{a.name:<30}", "title") +
                          tc(f" {sell_value(a):>4}g", "sys"))
            if not sellable:
                tprint(" All sellable items are equipped.", "warn"); continue
            sell_raw = tinput(" S <n> or SELL ALL: ").strip().lower()
            _process_sell(sell_raw, sellable, carried, character, aldric_types)

        elif raw.startswith("b "):
            try:
                idx = int(raw[2:]) - 1
                all_items = [(k, v, "spell") for k, v in available_spells] + \
                            [(i, i, "item")  for i in extras]
                if not (0 <= idx < len(all_items)):
                    tprint(" Invalid number.", "error"); continue
                key, val, kind = all_items[idx]

                if kind == "spell":
                    price = _aldric_spell_price(key, character)
                    if character.gold < price:
                        tprint(f' "That spell costs {price}g. You have {character.gold}g."', "npc"); continue
                    if tinput(f" Learn {val['name']} for {price}g? (y/n): ").lower() == "y":
                        character.gold -= price
                        character.spell_proficiencies[key] = random.randint(25, 75)
                        character.save()
                        tprint(f" You have learned {val['name']}! (proficiency: {character.spell_proficiencies[key]}%)", "sys")
                        print(tc(' "Use it wisely," Aldric says. "The arcane arts do not forgive carelessness."', "npc"))
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

# ── Room display ──────────────────────────────────────────────────────────────

def show_room(room: TavernRoom, character=None, entering: bool = False, brief: bool = False) -> None:
    print()
    print(tc(f" ── {room.name} ──", "border"))
    if brief and room.brief_description:
        print(tc(room.brief_description, "desc"))
    else:
        print(tc(room.description, "desc"))

    # Items dropped on the floor this session
    floor = _session["floor_items"].get(room.room_id, [])
    if floor:
        print()
        for a in floor:
            tprint(f"  {a.name} is here on the floor.", "warn")

    if room.exits:
        dirs = []
        for d in sorted(room.exits.keys()):
            dirs.append("SOUTH (exit to street)" if room.exits[d] == "EXIT_UNIVERSE" else d.upper())
        print(tc(f" Exits: {', '.join(dirs)}", "border"))

    # NPC first-entry greeting
    if entering and character and room.npc and room.room_id not in _session["npc_greeted"]:
        print()
        _print_npc_entry_greeting(room.npc, character)
        _session["npc_greeted"].add(room.room_id)
    print()

def _print_npc_entry_greeting(npc: str, character) -> None:
    if npc == "marcus":
        print(tc(' Marcus Marcos looks up from his work. "Well, well — a Free Adventurer!"', "npc"))
        print(tc(' "Marcus Marcos at your service. Finest weapons in the city. Have a look."', "npc"))
    elif npc == "aldric":
        print(tc(' Aldric the Mage sets down his quill and peers over his spectacles at you.', "desc"))
        print(tc(' "Ah. A visitor. How... timely. I am Aldric. Knowledge and its tools, at a price."', "npc"))
    elif npc == "marie":
        print(_marie_greeting_line(character))
        att = _marie_total_attitude(character)
        if att < 0:
            print(tc(' "If you have an offering, set it before Marie. Otherwise — speak quickly."', "npc"))
        elif att == 0:
            print(tc(' "You seek something. Marie can see it in your eyes. Speak your need."', "npc"))
        else:
            print(tc(' "You are always welcome here, cher. What can Marie do for you today?"', "npc"))
    elif npc == "banker":
        print(tc(' "Reginald T. Pemberton, Bank of the Main Hall," the man says precisely.', "npc"))
        print(tc(' "DEPOSIT, WITHDRAW, or BALANCE. All transactions are recorded and final."', "npc"))

# ── Main Hall command handler ─────────────────────────────────────────────────

DIR_ABBREV = {
    "n":"north","s":"south","e":"east","w":"west","u":"up","d":"down",
    "ne":"northeast","nw":"northwest","se":"southeast","sw":"southwest",
}

def handle_main_hall_command(raw: str, character, room_id: str) -> Optional[str]:
    room = MAIN_HALL_ROOMS[room_id]
    cmd, status, suggestions = parse_command(raw, "tavern")

    parts = raw.strip().lower().split()
    noun  = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Special parsing: GIVE <item> TO <npc>
    if parts and parts[0] == "give" and "to" in parts:
        to_idx = parts.index("to")
        cmd    = "give"
        status = "exact"
        noun   = " ".join(parts[1:to_idx]) + "|" + " ".join(parts[to_idx+1:])

    # Special parsing: TALK TO <npc>
    elif len(parts) >= 3 and parts[0] == "talk" and parts[1] == "to":
        cmd    = "talk"
        status = "exact"
        noun   = " ".join(parts[2:])

    if status in ("exact", "partial"):
        return _execute_main_hall_command(cmd, noun, character, room)
    elif status == "ambiguous":
        tprint(f"\n Ambiguous: '{parts[0].upper()}'. Did you mean: {', '.join(s.upper() for s in (suggestions or []))}?", "error")
    else:
        tprint(" Unknown command. Type HELP for a list.", "error")
        if suggestions:
            tprint(f" Did you mean: {', '.join(s.upper() for s in suggestions[:3])}?", "sys")
    return None


# ── Tavern item helpers ───────────────────────────────────────────────────────

def _find_item_by_name(noun: str, items: list):
    """Return first item whose name contains noun (case-insensitive), or None."""
    noun_l = noun.strip().lower()
    for item in items:
        if noun_l in item.name.lower() or item.name.lower().startswith(noun_l):
            return item
    return None


_NPC_DESCRIPTIONS = {
    "marcus":  ("Marcus Marcos",
                "A stocky man in a black apron, blade half-honed in hand. His eyes"
                " measure you like a potential customer — which, he hopes, you are."),
    "aldric":  ("Aldric the Mage",
                "A lean, pale scholar in wire spectacles and ink-stained robes. His quill"
                " is always poised. He looks faintly irritated by existence in general."),
    "marie":   ("Marie Laveau",
                "An imposing woman in dark robes, seated before a crystal ball. Her gaze"
                " is ancient and knowing. She does not smile — but she does not need to."),
    "banker":  ("Reginald T. Pemberton",
                "A neat, balding man in a green coat, every hair in place. He radiates"
                " the particular calm of someone who has never lost track of a single coin."),
}

def _cmd_tavern_examine(noun: str, character, room) -> None:
    noun_l = noun.strip().lower()
    if not noun_l:
        show_room(room, character, entering=False); return

    # Check carried items
    carried = _load_carried(character)
    target  = _find_item_by_name(noun, carried)
    if not target:
        # Check floor items
        floor  = _session["floor_items"].get(room.room_id, [])
        target = _find_item_by_name(noun, floor)

    if target:
        print()
        print(tc(f" {target.name}", "title"))
        print(tc(f" {target.description}", "desc"))
        atype = getattr(target, "artifact_type", "")
        extras = []
        if atype == "weapon":
            extras.append(f"Damage: {target.damage_dice}d{target.damage_sides}")
        elif atype in ("armor", "shield"):
            extras.append(f"Armor class: {target.armor_class}")
        elif atype in ("potion", "food"):
            if target.heal_amount:
                extras.append(f"Heals: {target.heal_amount} HP")
        if extras:
            print(tc(f" [{', '.join(extras)}]", "stat"))
        sv = sell_value(target)
        if sv > 0:
            print(tc(f" Value: ~{sv}g", "sys"))
        print()
        return

    # Check NPC in room
    if room.npc and room.npc in _NPC_DESCRIPTIONS:
        npc_key = room.npc
        name, desc = _NPC_DESCRIPTIONS[npc_key]
        if (noun_l in npc_key or noun_l in name.lower()
                or any(noun_l in k for k in ("marcus","aldric","marie","banker","pemberton","laveau","cavielli")
                       if k in (npc_key + name.lower()))):
            print()
            print(tc(f" {name}", "title"))
            print(tc(f" {desc}", "desc"))
            print()
            return

    # Check room features
    if noun_l in ("room", "area", "here", "around"):
        show_room(room, character, entering=False); return
    if noun_l in ("map", "board", "notice") and room.room_id == "guild_hall":
        tprint(" The quest board lists every adventure available to Guild members. Type ADVENTURE to browse.", "desc"); return
    if noun_l in ("map",) and room.room_id == "foyer":
        tprint(" The enchanted map shimmers faintly. Known adventure sites pulse with soft light.", "desc"); return

    tprint(f" You don't see a '{noun}' here.", "error")


def _cmd_tavern_read(noun: str, character, room) -> None:
    carried = _load_carried(character)
    floor   = _session["floor_items"].get(room.room_id, [])
    target  = _find_item_by_name(noun, carried) or _find_item_by_name(noun, floor)
    if not target:
        tprint(f" You don't see a '{noun}' to read.", "error"); return
    if getattr(target, "artifact_type", "") not in ("readable", "spellbook"):
        tprint(f" There is nothing to read on the {target.name}.", "error"); return
    text = getattr(target, "read_text", None) or getattr(target, "description", "(The page is blank.)")
    print()
    print(tc(f" [{target.name}]", "title"))
    print(tc(f" {text}", "desc"))
    print()


def _cmd_tavern_drop(noun: str, character, room) -> None:
    if not noun:
        tprint(" Drop what?", "error"); return
    carried = _load_carried(character)
    target  = _find_item_by_name(noun, carried)
    if not target:
        tprint(f" You're not carrying a '{noun}'.", "error"); return
    equipped_names = set(character.equipped.values())
    if target.name in equipped_names:
        tprint(f" Unequip the {target.name} before dropping it.", "warn"); return
    remaining = [a for a in carried if id(a) != id(target)]
    _save_carried(character, remaining)
    floor = _session["floor_items"].setdefault(room.room_id, [])
    floor.append(target)
    tprint(f" You drop the {target.name} on the floor.", "desc")


def _cmd_tavern_get(noun: str, character, room) -> None:
    floor = _session["floor_items"].get(room.room_id, [])
    if not floor:
        tprint(" There is nothing here to pick up.", "error"); return
    if not noun:
        tprint(" Pick up what?", "error"); return
    target = _find_item_by_name(noun, floor)
    if not target:
        tprint(f" You don't see a '{noun}' on the floor here.", "error"); return
    carried = _load_carried(character)
    carried.append(target)
    _save_carried(character, carried)
    _session["floor_items"][room.room_id] = [a for a in floor if id(a) != id(target)]
    tprint(f" You pick up the {target.name}.", "desc")


def _cmd_tavern_use(noun: str, character, room) -> None:
    if not noun:
        tprint(" Use what?", "error"); return
    carried = _load_carried(character)
    floor   = _session["floor_items"].get(room.room_id, [])
    target  = _find_item_by_name(noun, carried) or _find_item_by_name(noun, floor)
    if not target:
        tprint(f" You don't have or see a '{noun}' here.", "error"); return
    atype = getattr(target, "artifact_type", "")
    if atype == "potion":
        _cmd_tavern_drink(target.name, character)
    elif atype == "food":
        _cmd_tavern_eat(target.name, character)
    elif atype in ("weapon", "armor", "shield", "ring", "cloak"):
        cmd_equip_tavern(target.name, character)
    elif atype in ("readable", "spellbook"):
        _cmd_tavern_read(target.name, character, room)
    elif atype == "light":
        _cmd_tavern_light(target.name, character, room)
    else:
        tprint(f" You're not sure how to use the {target.name} here.", "desc")


def _cmd_tavern_eat(noun: str, character) -> None:
    if not noun:
        tprint(" Eat what?", "error"); return
    carried = _load_carried(character)
    target  = _find_item_by_name(noun, carried)
    if not target:
        tprint(f" You're not carrying a '{noun}'.", "error"); return
    if getattr(target, "artifact_type", "") != "food":
        tprint(f" You can't eat the {target.name}.", "error"); return
    healing = getattr(target, "heal_amount", 0) or 0
    old_hp  = character.hp
    character.hp = min(character.hp + healing, character.hp_max)
    gained  = character.hp - old_hp
    tprint(f" You eat the {target.name}.{' (+' + str(gained) + ' HP)' if gained else ''}", "desc")
    _save_carried(character, [a for a in carried if id(a) != id(target)])
    character.save()


def _cmd_tavern_drink(noun: str, character) -> None:
    if not noun:
        tprint(" Drink what?", "error"); return
    carried = _load_carried(character)
    target  = _find_item_by_name(noun, carried)
    if not target:
        tprint(f" You're not carrying a '{noun}'.", "error"); return
    if getattr(target, "artifact_type", "") != "potion":
        tprint(f" You can't drink the {target.name}.", "error"); return
    healing = getattr(target, "heal_amount", 0) or 0
    if healing > 0:
        old_hp = character.hp
        character.hp = min(character.hp + healing, character.hp_max)
        gained = character.hp - old_hp
        tprint(f" You drink the {target.name}. (+{gained} HP)", "desc")
    else:
        tprint(f" You drink the {target.name}. (Mana restored — takes effect at your next adventure.)", "desc")
    _save_carried(character, [a for a in carried if id(a) != id(target)])
    character.save()


def _cmd_tavern_health(character) -> None:
    bar_len = 20
    filled  = int(bar_len * character.hp / max(1, character.hp_max))
    bar     = "█" * filled + "░" * (bar_len - filled)
    print()
    print(tc(f" HP:   {character.hp}/{character.hp_max}  [{bar}]", "stat"))
    print(tc(f" Gold: {character.gold}g  |  Bank: {character.bank_balance}g", "sys"))
    active = {s: n for s, n in character.equipped.items() if n}
    if active:
        estr = ", ".join(f"{s}: {n}" for s, n in active.items())
        print(tc(f" Equipped: {estr}", "desc"))
    print()


def _cmd_tavern_rest(character) -> None:
    if character.hp >= character.hp_max:
        tprint(" You are already fully rested.", "desc"); return
    healed = character.hp_max - character.hp
    character.hp = character.hp_max
    character.save()
    tprint(f" You rest at the inn. All wounds are healed. (+{healed} HP)", "desc")


def _cmd_tavern_light(noun: str, character, room) -> None:
    if not noun:
        tprint(" Light what?", "error"); return
    carried = _load_carried(character)
    floor   = _session["floor_items"].get(room.room_id, [])
    target  = _find_item_by_name(noun, carried) or _find_item_by_name(noun, floor)
    if not target:
        tprint(f" You don't have or see a '{noun}' here.", "error"); return
    if getattr(target, "artifact_type", "") != "light":
        tprint(f" The {target.name} can't be lit.", "error"); return
    tprint(f" You light the {target.name}. The {room.name} brightens a little.", "desc")


def _execute_main_hall_command(cmd: str, noun: str, character, room) -> Optional[str]:

    # ── Movement ──────────────────────────────────────────────────────────────
    if cmd in ("north","south","east","west","northeast","northwest","southeast","southwest","up","down"):
        target = room.exits.get(cmd)
        if target == "EXIT_UNIVERSE":
            _temporarily_leave_universe(character); return "EXIT_GAME"
        elif target:
            return target
        tprint(" You can't go that way.", "error"); return None

    if cmd == "go":
        direction = DIR_ABBREV.get(noun.strip().lower(), noun.strip().lower())
        target    = room.exits.get(direction)
        if target == "EXIT_UNIVERSE":
            _temporarily_leave_universe(character); return "EXIT_GAME"
        elif target:
            return target
        tprint(" You can't go that way.", "error"); return None

    # ── LEAVE / QUIT ──────────────────────────────────────────────────────────
    if cmd in ("leave", "quit"):
        if room.room_id != "foyer":
            tprint(" The exit is through the Main Hall foyer (south).", "desc"); return None
        _temporarily_leave_universe(character); return "EXIT_GAME"

    # ── NPC interaction ────────────────────────────────────────────────────────
    if cmd == "talk":
        target = noun.strip().lower()
        if not target:
            if room.npc:
                target = room.npc
            else:
                tprint(" Talk to whom?", "error"); return None

        if any(k in target for k in ("marcus","cavielli","weapon","shop","armour","armor")):
            if room.npc == "marcus":
                run_marcus_shop(character)
            else:
                tprint(" Cavielli's Weapons Shoppe is east of the Main Hall.", "desc")
            return None

        if any(k in target for k in ("aldric","wizard","magic","mage","potion")):
            if room.npc == "aldric":
                run_aldric_shop(character)
            else:
                tprint(" Aldric's shop is in the back room — east from the Common Room.", "desc")
            return None

        if any(k in target for k in ("marie","laveau","witch")):
            if room.npc == "marie":
                run_marie_shop(character)
            else:
                tprint(" Marie Laveau's chamber is north of the Common Room.", "desc")
            return None

        if any(k in target for k in ("banker","pemberton","bank")):
            if room.npc == "banker":
                run_bank(character)
            else:
                tprint(" The bank is west of the Main Hall.", "desc")
            return None

        tprint(f" There is no one called '{noun}' here.", "error"); return None

    # ── Shop shortcut commands ────────────────────────────────────────────────
    if cmd in ("buy", "sell"):
        if room.npc == "marcus":
            run_marcus_shop(character)
        elif room.npc == "aldric":
            run_aldric_shop(character)
        elif room.npc == "marie":
            run_marie_shop(character)
        elif room.npc == "banker":
            run_bank(character)
        else:
            tprint(" No shopkeeper here. Try Marcus (east), Aldric (common room → east), or the bank (west).", "desc")
        return None

    if cmd in ("marcus", "horace"):
        if room.npc == "marcus":
            run_marcus_shop(character)
        else:
            tprint(" Cavielli's Weapons Shoppe is east of the Main Hall.", "desc")
        return None

    if cmd in ("wizard", "aldric"):
        if room.npc == "aldric":
            run_aldric_shop(character)
        else:
            tprint(" Aldric's shop is east of the Common Room.", "desc")
        return None

    if cmd == "marie":
        if room.npc == "marie":
            run_marie_shop(character)
        else:
            tprint(" Marie Laveau's chamber is north of the Common Room.", "desc")
        return None

    if cmd == "bank":
        if room.npc == "banker":
            run_bank(character)
        else:
            tprint(" The bank is west of the Main Hall.", "desc")
        return None

    # ── GIVE ─────────────────────────────────────────────────────────────────
    if cmd == "give":
        if "|" in noun:
            item_name, npc_name = noun.split("|", 1)
            item_name = item_name.strip()
            npc_name  = npc_name.strip()
        else:
            item_name = noun.strip()
            npc_name  = room.npc or ""

        if not item_name:
            tprint(" Give what?", "error"); return None

        if any(k in npc_name for k in ("marie","laveau","witch")) or room.npc == "marie":
            if room.npc != "marie" and not any(k in npc_name for k in ("marie","laveau","witch")):
                tprint(" Marie Laveau is north of the Common Room.", "desc"); return None
            _marie_give_gift_by_name(item_name, character)
        elif room.npc in ("marcus","aldric"):
            npc_label = "Marcus" if room.npc == "marcus" else "Aldric"
            tprint(f' {npc_label} shakes his head. "I don\'t want gifts. Sell it to me properly."', "npc")
        elif room.npc == "banker":
            tprint(' Pemberton raises an eyebrow. "We deal in coin, not goods. DEPOSIT to store gold."', "npc")
        else:
            tprint(" There is no one here to give that to.", "error")
        return None

    # ── Bank commands ─────────────────────────────────────────────────────────
    if cmd in ("deposit", "withdraw", "balance"):
        if room.npc != "banker":
            tprint(" The bank is west of the Main Hall.", "desc"); return None
        if cmd == "deposit":
            _bank_deposit(noun, character)
        elif cmd == "withdraw":
            _bank_withdraw(noun, character)
        else:
            _show_balance(character)
        return None

    # ── Character management ──────────────────────────────────────────────────
    if cmd == "character":
        show_character_sheet(character); return None
    if cmd == "inventory":
        show_inventory(character); return None
    if cmd == "spells":
        show_spells(character); return None
    if cmd == "equipment":
        show_equipment(character); return None
    if cmd == "equip":
        cmd_equip_tavern(noun, character); return None
    if cmd == "unequip":
        show_equipment(character); return None

    # ── Game control ──────────────────────────────────────────────────────────
    if cmd == "save":
        character.save()
        tprint(" Character saved.", "sys"); return None

    if cmd == "look":
        show_room(room, character, entering=False); return None

    # ── Verbose / Brief mode ──────────────────────────────────────────────────
    if cmd == "verbose":
        _session["verbose"] = True
        tprint(" Verbose mode on — full room descriptions every visit.", "sys"); return None

    if cmd == "brief":
        _session["verbose"] = False
        tprint(" Brief mode on — short descriptions after first visit.", "sys"); return None

    # ── Examine / Read ────────────────────────────────────────────────────────
    if cmd == "examine":
        _cmd_tavern_examine(noun, character, room); return None

    if cmd == "read":
        _cmd_tavern_read(noun, character, room); return None

    # ── Item handling ─────────────────────────────────────────────────────────
    if cmd == "drop":
        _cmd_tavern_drop(noun, character, room); return None

    if cmd == "get":
        _cmd_tavern_get(noun, character, room); return None

    if cmd == "use":
        _cmd_tavern_use(noun, character, room); return None

    if cmd == "eat":
        _cmd_tavern_eat(noun, character); return None

    if cmd == "drink":
        _cmd_tavern_drink(noun, character); return None

    if cmd == "light":
        _cmd_tavern_light(noun, character, room); return None

    # ── Status ────────────────────────────────────────────────────────────────
    if cmd == "health":
        _cmd_tavern_health(character); return None

    if cmd == "rest":
        _cmd_tavern_rest(character); return None

    # ── Game control ──────────────────────────────────────────────────────────
    if cmd == "help":
        show_main_hall_help(); return None

    if cmd == "adventure":
        return "BOARD"

    if cmd == "resume":
        menu_load_save(character); return None

    tprint(" Unknown command. Type HELP for a list.", "error")
    return None


def _temporarily_leave_universe(character) -> None:
    """The classic Eamon 'Temporarily Leave the Universe' exit."""
    print()
    print(tc(" ─────────────────────────────────────────────────────", "border"))
    print(tc("  You push open the heavy oak door of the Main Hall and step out", "desc"))
    print(tc("  into the street. The city carries on around you, indifferent.", "desc"))
    print()
    print(tc("  Your legend is duly recorded in the Guild rolls.", "sys"))
    print(tc("  The Free Adventurers will be here when you return.", "sys"))
    print()
    print(tc("  (Temporarily Leaving the Universe — character saved.)", "warn"))
    print(tc(" ─────────────────────────────────────────────────────", "border"))
    print()
    character.save()

# ── Help ──────────────────────────────────────────────────────────────────────

def show_main_hall_help() -> None:
    print()
    print(tc(" ─── Main Hall Commands ───────────────────────────────", "border"))
    cmds = [
        ("N/S/E/W/NE/SW/...",   "Move between rooms"),
        ("GO <direction>",      "Move explicitly"),
        ("LOOK / L",            "Describe current room (always full)"),
        ("VERBOSE",             "Full room descriptions on every visit"),
        ("BRIEF",               "Short descriptions after first visit"),
        ("EXAMINE / X <thing>", "Examine an item, NPC, or room feature"),
        ("READ <item>",         "Read a scroll, book, or sign"),
        ("DROP <item>",         "Drop a carried item on the floor"),
        ("GET <item>",          "Pick up an item from the floor"),
        ("USE <item>",          "Use an item (drink potion, equip weapon, etc.)"),
        ("EAT <item>",          "Eat a food item"),
        ("DRINK <item>",        "Drink a potion"),
        ("HEALTH / HP",         "Quick health and gold summary"),
        ("REST",                "Rest at the inn to restore HP"),
        ("LIGHT <item>",        "Light a torch or lamp"),
        ("TALK TO <name>",      "Speak to the NPC in this room"),
        ("GIVE <item> TO <npc>","Give an item to an NPC (gifts for Marie)"),
        ("BUY / SELL",          "Open the shop in your current room"),
        ("MARCUS / CAVIELLI",   "Cavielli's Weapons Shoppe (east of Main Hall)"),
        ("ALDRIC / WIZARD",     "Aldric's Magic shop (common room → east)"),
        ("MARIE / WITCH",       "Marie Laveau's chamber (common room → north)"),
        ("BANK",                "The Main Hall Bank (west of Main Hall)"),
        ("DEPOSIT <amount>",    "Deposit gold at the bank"),
        ("WITHDRAW <amount>",   "Withdraw gold from the bank"),
        ("BALANCE",             "Check your bank balance"),
        ("INVENTORY / I",       "List carried items"),
        ("EQUIPMENT / EQ",      "View and manage equipped items"),
        ("EQUIP <item>",        "Equip a carried weapon, armour, or accessory"),
        ("UNEQUIP",             "Remove an equipped item"),
        ("CHARACTER / V",       "Full character sheet"),
        ("SPELLS",              "Known spells and proficiencies"),
        ("SAVE",                "Save character to disk"),
        ("ADVENTURE / A",       "Go to the adventure board (guild hall)"),
        ("RESUME",              "Resume a saved adventure"),
        ("LEAVE / QUIT",        "Temporarily Leave the Universe (save and exit)"),
        ("HELP / ?",            "This message"),
    ]
    for c, desc in cmds:
        print(tc(f" {c:<26}", "title") + tc(desc, "desc"))
    print()

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

def menu_load_save(character) -> None:
    from character import Character
    games = list_resumable_games(character.name)
    if not games:
        tprint("\n No saved games found.", "error")
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
    if choice == str(len(adv_list) + 1) or choice.lower() == "cancel":
        return
    adventure = None
    try:
        adv_idx = int(choice) - 1
        if 0 <= adv_idx < len(adv_list):
            adventure = adv_list[adv_idx]
    except ValueError:
        for adv in adv_list:
            if choice.lower() in adv.lower():
                adventure = adv; break
    if not adventure:
        tprint(" Adventure not found.", "error"); return
    saves = games[adventure]
    if len(saves) == 1:
        slot = saves[0][0]
    else:
        slot_nums = ", ".join(str(s[0]) for s in saves)
        try:
            slot = int(tinput(f"\n Which save slot? ({slot_nums}): ").strip())
            if not any(s[0] == slot for s in saves):
                tprint(" Invalid slot.", "error"); return
        except ValueError:
            tprint(" Invalid input.", "error"); return
    save_data = load_game_slotted(character.name, adventure, slot, interactive=False)
    if not save_data:
        tprint(" Load failed.", "error"); return
    adv_path = None
    adventures = find_adventures()
    for adv in adventures:
        if adv["name"] == adventure:
            adv_path = adv["path"]; break
    if not adv_path:
        for adv in adventures:
            if adventure.lower() in adv["name"].lower() or adv["name"].lower() in adventure.lower():
                adv_path = adv["path"]; break
    if not adv_path:
        tprint(f" Adventure path not found for: {adventure}", "error"); return
    tprint(f"\n Resuming: {adventure}\n", "sys")
    result = _launch_engine(character, adv_path, save_data=save_data)
    _handle_engine_return(character, result, adv_path, adv_name=adventure, is_beginner_adv=False)

# ── Main Hall exploration loop ────────────────────────────────────────────────

def run_main_hall_exploration(character) -> str:
    """Navigate the Main Hall. Returns 'BOARD' or 'EXIT_GAME'."""
    _reset_session()
    current_room = "foyer"
    _session["visited"].add(current_room)
    show_room(MAIN_HALL_ROOMS[current_room], character, entering=True)
    tprint(" Type HELP for commands, ADVENTURE for the board, LEAVE to exit.", "sys")
    while True:
        raw    = tinput(f" [{MAIN_HALL_ROOMS[current_room].name}] > ")
        result = handle_main_hall_command(raw, character, current_room)
        if result in ("BOARD", "EXIT_GAME"):
            return result
        elif result is not None:
            current_room = result
            room = MAIN_HALL_ROOMS[current_room]
            # First visit always full; subsequent: full if verbose, brief otherwise
            is_first = current_room not in _session["visited"]
            _session["visited"].add(current_room)
            show_room(room, character, entering=True, brief=not is_first and not _session["verbose"])

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
    print(tc(" 0. Return to Main Hall", "border"))
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

def _launch_engine(character, adv_path: str, save_data: dict = None):
    from engine import run_adventure
    return run_adventure(character, adv_path, save_data=save_data)

def _handle_engine_return(character, result, adv_path: str,
                          adv_name: str = "", is_beginner_adv: bool = False) -> None:
    completed = (result == 1)
    died      = (result == 2)
    escaped   = (result == 3)

    if escaped:
        tprint("\n You return to the Main Hall.", "sys"); return
    elif result not in (0, 1, 2, 3):
        tprint("\n Something went wrong during that adventure.", "error")
    elif died:
        tprint("\n You have fallen. The Main Hall healer revives you for 2 gold per HP lost.", "warn")
        hp_lost = character.hp_max - character.hp
        cost = max(2, hp_lost * 2)
        character.gold = max(0, character.gold - cost)
        character.hp   = character.hp_max
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
            tprint(f" Welcome to the Main Hall, {character.name}.", "sys")
            first_entry = False

        action = run_main_hall_exploration(character)
        # SAVE ①: checkpoint after every tavern session — catches any in-hall
        # mutation that didn't call save() and ensures disk matches memory
        # before we branch to EXIT or to the adventure engine.
        character.save()

        if action == "EXIT_GAME":
            # _temporarily_leave_universe() already saved; SAVE ① above is
            # the belt-and-suspenders copy for this exit path.
            tprint("\n Until next time, adventurer.\n", "desc")
            break

        # action == "BOARD"
        adventures = find_adventures()
        if not adventures:
            tprint(" No adventures available.", "error"); continue

        adv = choose_adventure(character, adventures)
        if adv is None:
            continue

        tprint(f"\n You set out for: {adv['title']}\n", "sys")
        # SAVE ②: pre-engine checkpoint — guarantees disk = in-memory state
        # (gold, bank_balance, equipped, spells) before the engine takes over.
        character.save()
        result = _launch_engine(character, adv["path"])
        _handle_engine_return(character, result, adv["path"],
                              adv_name=adv["name"],
                              is_beginner_adv=adv["is_beginner"])
        # SAVE ③: post-engine checkpoint — _handle_engine_return saves for
        # died (result 2) and completed (result 1) but NOT for escaped (result 3).
        # This covers all remaining paths so no engine-modified state is lost.
        character.save()

        if result == 3:
            continue

        again = tinput("\n Return to the Saunter Inn? (y/n): ").lower()
        if again != "y":
            tprint("\n Until next time, adventurer.", "desc"); break


if __name__ == "__main__":
    run_tavern()
