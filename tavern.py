"""
tavern.py - The Eamon's End Tavern.

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

BANNER = r"""
  ╔══════════════════════════════════════════════════════════════════════╗
  ║                                                                      ║
  ║        ███████╗ █████╗ ███╗   ███╗ ██████╗ ███╗   ██╗               ║
  ║        ██╔════╝██╔══██╗████╗ ████║██╔═══██╗████╗  ██║               ║
  ║        █████╗  ███████║██╔████╔██║██║   ██║██╔██╗ ██║               ║
  ║        ██╔══╝  ██╔══██║██║╚██╔╝██║██║   ██║██║╚██╗██║               ║
  ║        ███████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝██║ ╚████║               ║
  ║        ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝               ║
  ║                                                                      ║
  ║                   A D V E N T U R E   E N G I N E                   ║
  ║                        Eamon's End Tavern                           ║
  ╚══════════════════════════════════════════════════════════════════════╝
"""


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
        print(tc("  0. Quit", "border"))
        print()

        choice = tinput("  > ").lower()

        if choice == "0":
            return None

        elif choice == "n":
            from character import Character
            ch = Character.create_interactive()
            return ch

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
            "--name", character.name,
            "--hardiness", str(character.hardiness),
            "--agility", str(character.agility),
            "--charisma", str(character.charisma),
            "--hp", str(character.hp),
        ])

        # Engine exit code: 0 = quit normally, 1 = completed, 2 = died
        completed = (result.returncode == 1)
        died      = (result.returncode == 2)

        if died:
            tprint("\n  ════════════════════════════════════════════", "border")
            horace_says(
                f"They brought your body back, {character.name}. "
                f"Happens to the best of them. "
                f"You've been patched up — but it'll cost you."
            )
            # Penalty: lose half gold, restore to half HP
            character.gold = max(0, character.gold // 2)
            character.hp   = max(1, character.hp_max // 2)
            character.save()
            tprint("  ════════════════════════════════════════════", "border")
        else:
            # Restore HP partially between adventures (rest at the tavern)
            healed = min(character.hp_max, character.hp + character.hardiness)
            character.hp = healed
            handle_return(character, adv["name"], completed)

        # Ask to continue
        again = tinput("\n  Return to the adventure board? (y/n): ").lower()
        if again != "y":
            horace_says("Until next time.")
            break


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_tavern()
