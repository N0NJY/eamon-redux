"""
tavern.py - The Saunter Inn and Tavern.

Entry point for the whole game system.
Handles character creation/selection/deletion and adventure launching.
"""

from __future__ import annotations
import os
import sys
import subprocess


# ── Tavern color palette (separate from engine colors) ───────────────────────

_TAVERN_COLORS = {
    "title"  : "\033[1;33m",   # bold yellow  — banners, headers
    "border" : "\033[2;33m",   # dim yellow   — box borders
    "stat"   : "\033[0;37m",   # white        — character stats
    "sys"    : "\033[0;36m",   # cyan         — confirmations
    "error"  : "\033[0;31m",   # red          — errors
    "warn"   : "\033[0;33m",   # yellow       — warnings
    "prompt" : "\033[1;37m",   # bold white   — input prompts
    "npc"    : "\033[0;35m",   # magenta      — Guardian Horace speech
    "desc"   : "\033[2;37m",   # dim white    — scene descriptions
    "reset"  : "\033[0m",
}

def tc(text: str, role: str) -> str:
    """Tavern color: wrap text in the given role's color."""
    color = _TAVERN_COLORS.get(role, "")
    return f"{color}{text}{_TAVERN_COLORS['reset']}"

def tinput(prompt_text: str) -> str:
    return input(tc(prompt_text, "prompt")).strip()

def tprint(text: str, role: str = "desc") -> None:
    print(tc(text, role))


# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = """
  ╔══════════════════════════════════════════════════════════════════════╗
  ║                                                                      ║
  ║        ███████╗  █████╗  ███╗   ███╗  ██████╗  ███╗   ██╗           ║
  ║        ██╔════╝ ██╔══██╗ ████╗ ████║ ██╔═══██╗ ████╗  ██║           ║
  ║        █████╗   ███████║ ██╔████╔██║ ██║   ██║ ██╔██╗ ██║           ║
  ║        ██╔══╝   ██╔══██║ ██║╚██╔╝██║ ██║   ██║ ██║╚██╗██║           ║
  ║        ███████╗ ██║  ██║ ██║ ╚═╝ ██║ ╚██████╔╝ ██║ ╚████║           ║
  ║        ╚══════╝ ╚═╝  ╚═╝ ╚═╝     ╚═╝  ╚═════╝  ╚═╝  ╚═══╝           ║
  ║                                                                      ║
  ║                    R  E  D  U  X                                     ║
  ║                A D V E N T U R E   E N G I N E                      ║
  ║                                                                      ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║                                                                      ║
  ║             ~ ~  Saunter Inn and Tavern  ~ ~                        ║
  ║               Where adventurers gather                              ║
  ║                                                                      ║
  ╠══════════════════════════════════════════════════════════════════════╣
  ║   Inspired by the classic Eamon system (1980) by Donald Brown       ║
  ║   Reimagined in Python                                               ║
  ╚══════════════════════════════════════════════════════════════════════╝
"""


# ── Item valuation ───────────────────────────────────────────────────────────────

# Default sell price floors by artifact type
TYPE_VALUE_FLOOR = {
    "weapon":   10,
    "armor":    15,
    "shield":   10,
    "ring":     20,
    "cloak":    15,
    "potion":    5,
    "food":      2,
    "readable":  3,
    "generic":   1,
    "light":     3,
    "spellbook": 25,
}
UNSELLABLE_TYPES = {"key"}

def sell_value(artifact) -> int:
    """Return the gold value of an artifact. 0 = unsellable."""
    if artifact.is_quest_item:
        return 0
    if artifact.artifact_type in UNSELLABLE_TYPES:
        return 0
    if artifact.value >= 0:
        return artifact.value
    return TYPE_VALUE_FLOOR.get(artifact.artifact_type, 1)

def can_sell(artifact) -> bool:
    return sell_value(artifact) > 0


# ── Tavern shop ───────────────────────────────────────────────────────────────

def run_shop(character) -> None:
    """The tavern shop — sell carried items to Horace."""
    from world import World
    import json, os

    # Load carried artifacts from character's last adventure save
    # Since items persist via the engine exit, we just use what's in the
    # character object. Items are passed back via a companion save file.
    shop_file = os.path.join("characters", f"{character.name.lower().replace(' ','_')}_items.json")

    if not os.path.exists(shop_file):
        horace_says("You don't seem to be carrying anything worth selling.")
        return

    with open(shop_file) as f:
        items_data = json.load(f)

    if not items_data:
        horace_says("Your pack looks empty to me.")
        return

    # Reconstruct artifact objects for display
    from world import Artifact
    carried = [Artifact.from_dict(d) for d in items_data]
    sellable = [a for a in carried if can_sell(a)]
    unsellable = [a for a in carried if not can_sell(a)]

    if not sellable:
        horace_says("Nothing you're carrying is worth coin to me.")
        if unsellable:
            tprint(f"  (You have {len(unsellable)} item(s) I can't buy: "
                   f"{', '.join(a.name for a in unsellable)})", "desc")
        return

    while True:
        header = tc('─── Horace\'s Trading Post ───────────────────────────────', 'border')
        tprint(f"\n  {header}", "desc")
        horace_says("Let's see what you've got. I pay fair prices.")
        print()
        for i, a in enumerate(sellable, 1):
            price = sell_value(a)
            equipped_note = ""
            print(tc(f"  {i:>3}. ", "border") +
                  tc(f"{a.name:<30}", "title") +
                  tc(f"  {price:>4} gold", "sys"))
        total = sum(sell_value(a) for a in sellable)
        print()
        print(tc(f"  Total if selling all: {total} gold", "sys"))
        print(tc(f"  Your gold: {character.gold}", "stat"))
        print()
        print(tc("  S <number>  — sell one item  (e.g. S 2)", "desc"))
        print(tc("  SELL ALL    — sell everything", "desc"))
        print(tc("  DONE        — leave the shop", "desc"))
        print()

        raw = tinput("  > ").strip().lower()

        if raw in ("done", "leave", "exit", "0", "quit", "d"):
            break

        elif raw == "sell all":
            total_gold = sum(sell_value(a) for a in sellable)
            names = ", ".join(a.name for a in sellable)
            confirm = tinput(f"  Sell all {len(sellable)} items for {total_gold} gold? (y/n): ").lower()
            if confirm == "y":
                character.gold += total_gold
                horace_says(f"Pleasure doing business. Here's your {total_gold} gold.")
                tprint(f"  Gold: {character.gold}", "sys")
                # Remove sold items from save file
                remaining = unsellable
                with open(shop_file, "w") as f:
                    json.dump([a.to_dict() for a in remaining], f, indent=2)
                sellable.clear()
                if not unsellable:
                    break
                else:
                    tprint(f"  Remaining (unsellable): {', '.join(a.name for a in unsellable)}", "desc")
                    break

        elif raw.startswith("s "):
            try:
                idx = int(raw[2:].strip()) - 1
                if 0 <= idx < len(sellable):
                    item = sellable[idx]
                    price = sell_value(item)
                    confirm = tinput(f"  Sell {item.name} for {price} gold? (y/n): ").lower()
                    if confirm == "y":
                        character.gold += price
                        tprint(f"  Sold {item.name} for {price} gold. (Total: {character.gold})", "sys")
                        sellable.pop(idx)
                        # Update save file
                        remaining = sellable + unsellable
                        with open(shop_file, "w") as f:
                            json.dump([a.to_dict() for a in remaining], f, indent=2)
                        if not sellable:
                            horace_says("That's the lot. Safe travels.")
                            break
                else:
                    tprint("  Invalid number.", "error")
            except ValueError:
                tprint("  Enter 'S' followed by a number, e.g. S 2", "error")
        else:
            tprint("  Enter S <number>, SELL ALL, or DONE.", "warn")

    character.save()


# ── Guardian dialogue ─────────────────────────────────────────────────────────

def horace_says(text: str) -> None:
    print(tc(f'\n  Horace says: "{text}"', "npc"))
    print()


def guardian_greet(character) -> None:
    tprint("\n  The tavern is warm and smoky. A stout man behind the bar looks up.", "desc")
    tprint("  He has the look of someone who has seen every kind of adventurer\n"
           "  and forgotten most of them.", "desc")

    if character.is_beginner:
        horace_says(
            f"Ah, {character.name}! New to the adventuring life, are you? "
            f"Good, good. We've a place for your sort. "
            f"The Beginner's Cave is just down the road — Thornwall Keep. "
            f"You'll want to cut your teeth there before venturing further. "
            f"Come back when you've seen it through and I'll point you somewhere grander."
        )
    else:
        completed = len(character.adventures_completed)
        horace_says(
            f"Welcome back, {character.name}! "
            f"{'One adventure' if completed == 1 else f'{completed} adventures'} under your belt "
            f"and still breathing — that's more than most manage. "
            f"Take your pick of what's on offer. The world doesn't save itself."
        )


# ── Adventure discovery ───────────────────────────────────────────────────────

def find_adventures(adventures_dir: str = "adventures") -> list[dict]:
    """
    Scan the adventures/ folder. Each subfolder with an adventure.json is an adventure.
    Returns list of dicts: {name, path, title, author, min_hardiness, min_agility}
    """
    import json
    adventures = []
    if not os.path.isdir(adventures_dir):
        return adventures

    for entry in sorted(os.listdir(adventures_dir)):
        adv_path = os.path.join(adventures_dir, entry)
        meta_path = os.path.join(adv_path, "adventure.json")
        if os.path.isdir(adv_path) and os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            adventures.append({
                "name"         : entry,
                "path"         : adv_path,
                "title"        : meta.get("title", entry),
                "author"       : meta.get("author", "Unknown"),
                "min_hardiness": meta.get("min_hardiness", 0),
                "min_agility"  : meta.get("min_agility", 0),
                "is_beginner"  : meta.get("is_beginner_adventure", False),
            })
    return adventures


def choose_adventure(character, adventures: list[dict]) -> dict | None:
    """Show adventure menu; enforce beginner restriction and stat minimums."""
    if character.is_beginner:
        # Beginners can only play adventures flagged as beginner adventures
        available = [a for a in adventures if a["is_beginner"]]
        if not available:
            # Fall back to 'sample' if nothing is flagged
            available = [a for a in adventures if a["name"] == "sample"]
        if not available:
            tprint("\n  No beginner adventure found. Ask your game master.", "error")
            return None
        tprint("\n  As a new adventurer, Horace directs you to the beginner's adventure:", "desc")
        return available[0]

    # Veterans see all adventures, with eligibility notes
    print(tc("\n  ─── Available Adventures ───────────────────────────────────", "border"))
    eligible = []
    for i, adv in enumerate(adventures, 1):
        met_h = character.hardiness >= adv["min_hardiness"]
        met_a = character.agility  >= adv["min_agility"]
        eligible_flag = met_h and met_a
        completed_flag = adv["name"] in character.adventures_completed

        status = ""
        if completed_flag:
            status = tc("  [completed]", "sys")
        if not eligible_flag:
            reqs = []
            if not met_h:
                reqs.append(f"Hardiness {adv['min_hardiness']}+")
            if not met_a:
                reqs.append(f"Agility {adv['min_agility']}+")
            status = tc(f"  [requires: {', '.join(reqs)}]", "error")

        eligible.append(eligible_flag)
        marker = tc(f"  {i}.", "border")
        title  = tc(f" {adv['title']}", "title" if eligible_flag else "desc")
        author = tc(f" by {adv['author']}", "desc")
        print(f"{marker}{title}{author}{status}")

    print(tc("  0. Return to tavern", "border"))
    print()

    while True:
        raw = tinput("  Choose an adventure: ")
        try:
            n = int(raw)
            if n == 0:
                return None
            if 1 <= n <= len(adventures):
                if not eligible[n - 1]:
                    tprint("  Your stats aren't high enough for that one yet.", "error")
                    continue
                return adventures[n - 1]
        except ValueError:
            pass
        tprint("  Please enter a number from the list.", "warn")


# ── Post-adventure return ─────────────────────────────────────────────────────

def handle_return(character, adventure_name: str, completed: bool) -> None:
    """Called when the engine exits. Update character state."""
    if completed and adventure_name not in character.adventures_completed:
        character.adventures_completed.append(adventure_name)

        # Check if this was the beginner adventure
        adventures = find_adventures()
        adv_meta = next((a for a in adventures if a["name"] == adventure_name), None)
        was_beginner_adv = adv_meta and adv_meta.get("is_beginner", False)

        if was_beginner_adv and character.is_beginner:
            character.is_beginner = False
            tprint("\n  ════════════════════════════════════════════════", "border")
            horace_says(
                f"Well done, {character.name}! You've made it through in one piece. "
                f"Not everyone does. You're no beginner now — "
                f"the full world of Eamon is open to you."
            )
            tprint("  ════════════════════════════════════════════════", "border")
        else:
            horace_says(
                f"Another adventure completed, {character.name}. "
                f"Pull up a stool and have a drink."
            )

        character.save()


# ── Character management menu ─────────────────────────────────────────────────

def menu_characters() -> "Character | None":
    """Character selection / creation / deletion. Returns chosen character or None."""
    from character import Character

    while True:
        names = Character.list_all()

        print(tc("\n  ─── The Adventurers' Guild ──────────────────────────────", "border"))
        if names:
            for i, name in enumerate(names, 1):
                ch = Character.load(name)
                status = "Beginner" if ch.is_beginner else f"Veteran ({len(ch.adventures_completed)} adventures)"
                hp_pct = f"HP {ch.hp}/{ch.hp_max}"
                print(tc(f"  {i}. ", "border") +
                      tc(f"{ch.name:<20}", "title") +
                      tc(f"  H:{ch.hardiness} A:{ch.agility} C:{ch.charisma}  ", "stat") +
                      tc(f"{hp_pct:<12}", "sys") +
                      tc(status, "desc"))
        else:
            tprint("  No characters yet.", "desc")

        print(tc("\n  N. Create new character", "sys"))
        if names:
            print(tc("  D. Delete a character", "error"))
            print(tc("  V. View character details", "stat"))
        print(tc("  M. Read the Adventurer\'s Manual", "desc"))
        print(tc("  0. Quit", "border"))
        print()

        choice = tinput("  > ").lower()

        if choice == "0":
            return None

        elif choice == "n":
            from character import Character
            ch = Character.create_interactive()
            return ch

        elif choice == "m":
            _show_manual()

        elif choice == "v" and names:
            raw = tinput("  Enter character number to view: ")
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(names):
                    ch = Character.load(names[idx])
                    print()
                    print(tc("  ┌─────────────────────────────────────────┐", "border"))
                    print(tc(f"  │  Character Sheet: {ch.name:<22}│", "title"))
                    print(tc("  ├─────────────────────────────────────────┤", "border"))
                    for line in ch.stat_summary().split("\n"):
                        padded = f"  │  {line.strip():<39}│"
                        print(tc(padded, "stat"))
                    print(tc("  └─────────────────────────────────────────┘", "border"))
                    tinput("\n  Press Enter to continue...")
            except (ValueError, IndexError):
                tprint("  Invalid selection.", "error")

        elif choice == "d" and names:
            raw = tinput("  Enter character number to delete: ")
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(names):
                    name = names[idx]
                    confirm = tinput(f"  Delete '{name}'? This cannot be undone. (yes/no): ").lower()
                    if confirm == "yes":
                        from character import Character
                        Character.delete(name)
                        tprint(f"  Character '{name}' deleted.", "sys")
                    else:
                        tprint("  Cancelled.", "desc")
            except (ValueError, IndexError):
                tprint("  Invalid selection.", "error")

        else:
            # Try selecting by number
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(names):
                    ch = Character.load(names[idx])
                    tprint(f"\n  Welcome back, {ch.name}.", "sys")
                    return ch
                else:
                    tprint("  Invalid selection.", "error")
            except ValueError:
                tprint("  Invalid selection.", "error")


# ── Shop data ────────────────────────────────────────────────────────────────────

from world import Artifact, ArtifactType

# Spell definitions mirrored here for the wizard shop
SPELL_CATALOG = {
    "heal":     {"name": "Heal",     "base_price": 50,  "classes": ["Sorcerer", "Fighter"], "desc": "Restore 1d6+INT HP"},
    "light":    {"name": "Light",    "base_price": 25,  "classes": ["Sorcerer", "Fighter"], "desc": "Illuminate dark rooms"},
    "shield":   {"name": "Shield",   "base_price": 75,  "classes": ["Sorcerer"],            "desc": "+3 AC for 3 rounds"},
    "fireball": {"name": "Fireball", "base_price": 150, "classes": ["Sorcerer"],            "desc": "2d6+INT fire damage"},
}

def spell_price(spell_key: str, character) -> int:
    """Price scales with level; Fighters pay double."""
    base = SPELL_CATALOG[spell_key]["base_price"]
    level = character.level
    # Multiplier tiers: 1-2=1x, 3-4=2x, 5-6=4x, 7-8=8x, 9+=16x
    tiers = [(2,1),(4,2),(6,4),(8,8)]
    multiplier = 16
    for threshold, mult in tiers:
        if level <= threshold:
            multiplier = mult
            break
    price = base * multiplier
    if character.char_class == "Fighter":
        price *= 2
    return price

# Horace's fixed core stock
HORACE_CORE = [
    {"name": "healing potion",       "artifact_type": "potion", "weight": 1, "heal_amount": 10, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 25,  "desc": "Restores 10 HP"},
    {"name": "minor healing potion", "artifact_type": "potion", "weight": 1, "heal_amount": 5,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 12,  "desc": "Restores 5 HP"},
    {"name": "ration",               "artifact_type": "food",   "weight": 1, "heal_amount": 4,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 5,   "desc": "Restores 4 HP when eaten"},
    {"name": "dagger",               "artifact_type": "weapon", "weight": 1, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 15,  "desc": "1d4 damage"},
    {"name": "short sword",          "artifact_type": "weapon", "weight": 2, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 0, "price": 30,  "desc": "1d6 damage"},
    {"name": "leather armor",        "artifact_type": "armor",  "weight": 3, "heal_amount": 0,  "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 40,  "desc": "AC +1"},
    {"name": "chainmail coat",       "artifact_type": "armor",  "weight": 6, "heal_amount": 0,  "armor_class": 3, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 100, "desc": "AC +3"},
    {"name": "wooden shield",        "artifact_type": "shield", "weight": 3, "heal_amount": 0,  "armor_class": 1, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 25,  "desc": "AC +1 (shield slot)"},
]

HORACE_RANDOM_POOL = [
    {"name": "war axe",     "artifact_type": "weapon", "weight": 4, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 8, "value": 0, "price": 50,  "desc": "1d8 damage"},
    {"name": "iron mace",   "artifact_type": "weapon", "weight": 3, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 0, "price": 35,  "desc": "1d6 damage"},
    {"name": "scale armor", "artifact_type": "armor",  "weight": 8, "heal_amount": 0, "armor_class": 4, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 180, "desc": "AC +4"},
    {"name": "iron shield", "artifact_type": "shield", "weight": 4, "heal_amount": 0, "armor_class": 2, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 55,  "desc": "AC +2 (shield slot)"},
    {"name": "hunting bow", "artifact_type": "weapon", "weight": 2, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 6, "value": 0, "price": 45,  "desc": "1d6 damage"},
    {"name": "torch",       "artifact_type": "light",  "weight": 1, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 3,  "price": 8,   "desc": "A light source"},
]

WIZARD_RANDOM_POOL = [
    {"name": "greater healing potion", "artifact_type": "potion", "weight": 1, "heal_amount": 20, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 60,  "desc": "Restores 20 HP"},
    {"name": "mana potion",            "artifact_type": "potion", "weight": 1, "heal_amount": 0,  "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 0, "price": 50,  "desc": "Restores 10 mana (Sorcerer only)", "is_mana_potion": True},
    {"name": "mystery scroll",         "artifact_type": "readable","weight": 0, "heal_amount": 0, "armor_class": 0, "damage_dice": 1, "damage_sides": 4, "value": 5,  "price": 20,  "desc": "Faded writing. Hard to read."},
]

def _make_shop_artifact(template: dict, new_id: int) -> Artifact:
    return Artifact(
        id=new_id,
        name=template["name"],
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

MAX_POTIONS = 2


def run_horace_shop(character) -> None:
    """Horace buys and sells weapons, armor, and gear."""
    import random, json, os

    shop_file = os.path.join("characters",
        f"{character.name.lower().replace(' ','_')}_items.json")

    # Build stock: core + 2-3 random extras (seeded per visit for consistency)
    random.seed(len(character.adventures_completed) * 7 + character.level)
    extras = random.sample(HORACE_RANDOM_POOL, min(3, len(HORACE_RANDOM_POOL)))
    stock = HORACE_CORE + extras
    random.seed()  # reset seed

    while True:
        tprint("\n  " + tc('─── Horace\'s Outfitters ─────────────────────────────────', 'border'), "desc")
        horace_says("Buy, sell, or just browse. Gold talks.")
        print()
        print(tc("  ── For Sale ──────────────────────────────────────", "border"))
        for i, item in enumerate(stock, 1):
            print(tc(f"  {i:>3}. ", "border") +
                  tc(f"{item['name']:<28}", "title") +
                  tc(f"  {item['price']:>4}g  ", "sys") +
                  tc(item.get("desc", ""), "desc"))
        print()
        print(tc(f"  Your gold: {character.gold}", "stat"))
        print()
        print(tc("  B <number>  — buy item", "desc"))
        print(tc("  S           — sell your items", "desc"))
        print(tc("  DONE        — leave", "desc"))
        print()

        raw = tinput("  > ").strip().lower()

        if raw in ("done", "leave", "0", "quit", "d"):
            break

        elif raw == "s":
            # Inline sell for Horace (gear only)
            if not os.path.exists(shop_file):
                tprint("  You don't have anything to sell.", "warn")
                continue
            with open(shop_file) as f:
                items_data = json.load(f)
            from world import Artifact
            carried = [Artifact.from_dict(d) for d in items_data]
            gear = [a for a in carried
                    if a.artifact_type in ("weapon","armor","shield","ring","cloak","generic")
                    and not a.is_quest_item]
            if not gear:
                tprint("  Nothing here I'd buy. Try the wizard for magical items.", "warn")
                continue
            print(tc("\n  ── Your gear ──────────────────────────────────", "border"))
            for i, a in enumerate(gear, 1):
                from tavern import sell_value
                v = sell_value(a)
                print(tc(f"  {i:>3}. ", "border") +
                      tc(f"{a.name:<30}", "title") +
                      tc(f"  {v:>4}g", "sys"))
            print(tc("  SELL ALL or S <number>", "desc"))
            sell_raw = tinput("  > ").strip().lower()
            _process_sell(sell_raw, gear, carried, character, shop_file,
                          allowed_types={"weapon","armor","shield","ring","cloak","generic"})

        elif raw.startswith("b "):
            try:
                idx = int(raw[2:].strip()) - 1
                if 0 <= idx < len(stock):
                    item = stock[idx]
                    price = item["price"]
                    # Potion limit check
                    if item["artifact_type"] == "potion":
                        current_potions = _count_carried_potions(shop_file)
                        if current_potions >= MAX_POTIONS:
                            tprint(f"  You can only carry {MAX_POTIONS} potions at a time.", "error")
                            continue
                    if character.gold < price:
                        tprint(f"  Not enough gold. (Need {price}g, have {character.gold}g)", "error")
                        continue
                    confirm = tinput(f"  Buy {item['name']} for {price}g? (y/n): ").lower()
                    if confirm == "y":
                        character.gold -= price
                        _add_to_inventory(item, shop_file)
                        tprint(f"  Purchased {item['name']}. Gold: {character.gold}g", "sys")
                        character.save()
                else:
                    tprint("  Invalid number.", "error")
            except ValueError:
                tprint("  Enter B followed by a number.", "error")
        else:
            tprint("  Enter B <number> to buy, S to sell, or DONE.", "warn")


def run_wizard_shop(character) -> None:
    """Wizard Aldric buys and sells magical items and spells."""
    import random, json, os

    shop_file = os.path.join("characters",
        f"{character.name.lower().replace(' ','_')}_items.json")

    random.seed(len(character.adventures_completed) * 13 + character.level)
    extras = random.sample(WIZARD_RANDOM_POOL, min(2, len(WIZARD_RANDOM_POOL)))
    random.seed()

    while True:
        tprint("\n  " + tc('─── Aldric\'s Arcane Emporium ────────────────────────────', 'border'), "desc")
        tprint("  A thin man with ink-stained fingers looks up from a large tome.", "desc")
        print(tc('  Aldric says: "Knowledge has a price. So does everything else."', "npc"))
        print()

        # Spells for sale
        available_spells = [
            (k, v) for k, v in SPELL_CATALOG.items()
            if k not in character.spells
            and (character.char_class in v["classes"])
        ]

        print(tc("  ── Spells ────────────────────────────────────────", "border"))
        if available_spells:
            for i, (key, spell) in enumerate(available_spells, 1):
                price = spell_price(key, character)
                can_afford = "✦" if character.gold >= price else "✗"
                print(tc(f"  {i:>3}. ", "border") +
                      tc(f"{spell['name']:<15}", "title") +
                      tc(f"  {price:>5}g  ", "sys") +
                      tc(spell["desc"], "desc") +
                      tc(f"  {can_afford}", "sys"))
        else:
            tprint("  You know all available spells.", "sys")

        # Magical items
        print(tc("\n  ── Magical Items ─────────────────────────────────", "border"))
        item_offset = len(available_spells)
        for i, item in enumerate(extras, item_offset + 1):
            print(tc(f"  {i:>3}. ", "border") +
                  tc(f"{item['name']:<28}", "title") +
                  tc(f"  {item['price']:>4}g  ", "sys") +
                  tc(item.get("desc", ""), "desc"))

        print()
        print(tc(f"  Your gold: {character.gold}  |  Level: {character.level}  |  XP: {character.xp}", "stat"))
        if character.char_class == "Sorcerer":
            print(tc(f"  Known spells: {', '.join(character.spells) or 'none'}", "desc"))
        print()
        print(tc("  B <number>  — buy spell or item", "desc"))
        print(tc("  S           — sell magical items", "desc"))
        print(tc("  DONE        — leave", "desc"))
        print()

        raw = tinput("  > ").strip().lower()

        if raw in ("done", "leave", "0", "d"):
            break

        elif raw == "s":
            if not os.path.exists(shop_file):
                tprint("  Nothing to sell.", "warn")
                continue
            with open(shop_file) as f:
                items_data = json.load(f)
            from world import Artifact
            carried = [Artifact.from_dict(d) for d in items_data]
            magic = [a for a in carried
                     if a.artifact_type in ("potion", "readable", "spellbook")
                     and not a.is_quest_item]
            if not magic:
                tprint("  Nothing magical I'd buy. Try Horace for weapons.", "warn")
                continue
            print(tc("\n  ── Your magical items ─────────────────────────", "border"))
            for i, a in enumerate(magic, 1):
                from tavern import sell_value
                v = sell_value(a)
                print(tc(f"  {i:>3}. ", "border") +
                      tc(f"{a.name:<30}", "title") +
                      tc(f"  {v:>4}g", "sys"))
            sell_raw = tinput("  SELL ALL or S <number>: ").strip().lower()
            _process_sell(sell_raw, magic, carried, character, shop_file,
                          allowed_types={"potion","readable","spellbook"})

        elif raw.startswith("b "):
            try:
                idx = int(raw[2:].strip()) - 1
                all_items = [(k, v, "spell") for k, v in available_spells] +                             [(i, i, "item") for i in extras]
                if 0 <= idx < len(all_items):
                    key, val, kind = all_items[idx]
                    if kind == "spell":
                        price = spell_price(key, character)
                        if character.gold < price:
                            tprint(f"  Not enough gold. (Need {price}g, have {character.gold}g)", "error")
                            continue
                        confirm = tinput(f"  Learn {val['name']} for {price}g? (y/n): ").lower()
                        if confirm == "y":
                            character.gold -= price
                            character.spells.append(key)
                            character.save()
                            tprint(f"  You have learned {val['name']}!", "sys")
                            print(tc('  Aldric says: "Use it wisely. Or don\'t. I don\'t care."', "npc"))
                    else:
                        item = val
                        price = item["price"]
                        if item["artifact_type"] == "potion":
                            current = _count_carried_potions(shop_file)
                            if current >= MAX_POTIONS:
                                tprint(f"  You can only carry {MAX_POTIONS} potions.", "error")
                                continue
                        if character.gold < price:
                            tprint(f"  Not enough gold. (Need {price}g, have {character.gold}g)", "error")
                            continue
                        confirm = tinput(f"  Buy {item['name']} for {price}g? (y/n): ").lower()
                        if confirm == "y":
                            character.gold -= price
                            _add_to_inventory(item, shop_file)
                            tprint(f"  Purchased {item['name']}. Gold: {character.gold}g", "sys")
                            character.save()
                else:
                    tprint("  Invalid number.", "error")
            except (ValueError, IndexError):
                tprint("  Enter B followed by a number.", "error")
        else:
            tprint("  Enter B <number>, S to sell, or DONE.", "warn")


def _count_carried_potions(shop_file: str) -> int:
    import json, os
    if not os.path.exists(shop_file):
        return 0
    with open(shop_file) as f:
        items = json.load(f)
    return sum(1 for d in items if d.get("artifact_type") == "potion")


def _add_to_inventory(template: dict, shop_file: str) -> None:
    """Add a shop item to the player's item save file."""
    import json, os
    items = []
    if os.path.exists(shop_file):
        with open(shop_file) as f:
            items = json.load(f)
    # Generate a new temp id
    new_id = max((d["id"] for d in items), default=100) + 1
    artifact = _make_shop_artifact(template, new_id)
    items.append(artifact.to_dict())
    with open(shop_file, "w") as f:
        json.dump(items, f, indent=2)


def _process_sell(raw: str, sellable: list, all_carried: list,
                  character, shop_file: str, allowed_types: set) -> None:
    """Shared sell logic for both shops."""
    import json
    from tavern import sell_value
    if raw == "sell all":
        total = sum(sell_value(a) for a in sellable)
        confirm = tinput(f"  Sell all for {total}g? (y/n): ").lower()
        if confirm == "y":
            character.gold += total
            remaining = [a for a in all_carried if a not in sellable]
            with open(shop_file, "w") as f:
                json.dump([a.to_dict() for a in remaining], f, indent=2)
            character.save()
            tprint(f"  Sold for {total}g. Gold: {character.gold}g", "sys")
    elif raw.startswith("s "):
        try:
            idx = int(raw[2:].strip()) - 1
            if 0 <= idx < len(sellable):
                item = sellable[idx]
                price = sell_value(item)
                confirm = tinput(f"  Sell {item.name} for {price}g? (y/n): ").lower()
                if confirm == "y":
                    character.gold += price
                    remaining = [a for a in all_carried if a.id != item.id]
                    with open(shop_file, "w") as f:
                        json.dump([a.to_dict() for a in remaining], f, indent=2)
                    character.save()
                    tprint(f"  Sold for {price}g. Gold: {character.gold}g", "sys")
        except ValueError:
            tprint("  Enter S <number>.", "error")


# ── Manual viewer ────────────────────────────────────────────────────────────────

def _show_manual() -> None:
    """Display the manual page by page."""
    import os
    manual_path = "MANUAL.md"
    if not os.path.exists(manual_path):
        tprint("  Manual file not found (MANUAL.md).", "error")
        return

    with open(manual_path) as f:
        lines = f.readlines()

    # Strip markdown formatting for terminal display
    import re
    terminal_lines = []
    for line in lines:
        line = line.rstrip()
        # Headers
        if line.startswith("### "):
            terminal_lines.append(tc("  " + line[4:].upper(), "title"))
        elif line.startswith("## "):
            terminal_lines.append("")
            terminal_lines.append(tc("  ── " + line[3:] + " ──", "border"))
        elif line.startswith("# "):
            terminal_lines.append(tc("  " + line[2:], "title"))
        # Code blocks — pass through as-is
        elif line.startswith("```"):
            pass
        # Table rows — simplify
        elif line.startswith("|"):
            terminal_lines.append(tc("  " + line, "stat"))
        # Bold
        else:
            line = re.sub(r'\*\*(.+?)\*\*', r'', line)
            line = re.sub(r'`(.+?)`', r'', line)
            if line.strip():
                terminal_lines.append("  " + line)
            else:
                terminal_lines.append("")

    # Page through output
    PAGE = 24
    i = 0
    while i < len(terminal_lines):
        page = terminal_lines[i:i+PAGE]
        for ln in page:
            print(ln)
        i += PAGE
        if i < len(terminal_lines):
            raw = tinput("\n  -- press Enter for more, Q to quit -- ").lower()
            if raw == "q":
                break

    tinput("\n  Press Enter to return to the Guild...")


# ── Main tavern loop ──────────────────────────────────────────────────────────

def run_tavern() -> None:
    print(tc(BANNER, "title"))

    # Character selection
    character = menu_characters()
    if character is None:
        tprint("\n  Safe travels.\n", "desc")
        return

    # Guardian greeting
    guardian_greet(character)

    # Main tavern loop — play adventures until player chooses to leave
    while True:
        adventures = find_adventures()
        if not adventures:
            tprint("  No adventures found in the adventures/ folder.", "error")
            break

        adv = choose_adventure(character, adventures)
        if adv is None:
            horace_says("Come back any time. The ale's always fresh.")
            break

        # Launch the engine as a subprocess, passing character stats
        tprint(f"\n  You set out for: {adv['title']}\n", "sys")

        result = subprocess.run([
            sys.executable, "engine.py",
            adv["path"],
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
            "--spells",  ",".join(character.spells),
            "--xp",      str(character.xp),
            "--level",   str(character.level),
        ])

        # Engine exit code: 0 = quit normally, 1 = completed, 2 = died
        # Any other code (e.g. crash) is treated as an abort — no state change
        completed = (result.returncode == 1)
        died      = (result.returncode == 2)
        crashed   = result.returncode not in (0, 1, 2)

        if crashed:
            tprint("\n  ════════════════════════════════════════════", "border")
            tprint("  Something went wrong with that adventure.", "error")
            tprint("  Your character has not been affected.", "warn")
            tprint("  ════════════════════════════════════════════", "border")
        elif died:
            tprint("\n  ════════════════════════════════════════════", "border")
            missing = character.hp_max - 1   # revived at 1 HP
            cost = missing * 2               # 2 gold per HP restored
            cost = min(cost, character.gold) # can't pay more than they have
            character.gold -= cost
            character.hp = character.hp_max  # fully healed after paying
            horace_says(
                f"They carried you in on a board, {character.name}. "
                f"The healer patched you up — costs {cost} gold. "
                f"You have {character.gold} gold remaining. "
                f"Try not to make a habit of this."
            )
            character.save()
            tprint("  ════════════════════════════════════════════", "border")
        else:
            # Restore HP and mana at the tavern (a good night's rest)
            character.hp   = character.hp_max
            character.mana = character.mana_max
            handle_return(character, adv["name"], completed)

        # Offer the shops
        print(tc("\n  ─── What would you like to do? ───────────────────", "border"))
        print(tc("  1. Visit Horace's Outfitters (weapons, armor, gear)", "desc"))
        print(tc("  2. Visit Aldric's Arcane Emporium (spells, potions)", "desc"))
        print(tc("  3. Skip", "desc"))
        shop_choice = tinput("  > ").strip()
        if shop_choice == "1":
            run_horace_shop(character)
        elif shop_choice == "2":
            run_wizard_shop(character)

        # Ask to continue
        again = tinput("\n  Return to the adventure board? (y/n): ").lower()
        if again != "y":
            horace_says("Until next time.")
            break


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_tavern()
